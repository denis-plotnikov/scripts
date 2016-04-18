#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/mman.h>
#include <stdbool.h>

#define NPAGE 2
#define CACHE_LINE_SIZE 64
#define PAGE_EXCHANGES_COUNT 1000000
#define REPORT_EACH_ITERS 100000
static int num_threads;
// common functions
static void raise_error(char *msg, int err_num)
{
	printf("%s\n", msg);
	exit(err_num);
}

// page functions
struct map_info {
	void *page;
	char val;
};

static void fillout_page(void *page, size_t page_size, char val)
{
	char *pg = page;
	for (unsigned i = 0; i < page_size; i++)
		pg[i] = val;
}

static void print_page(void *page, size_t page_size)
{
	char *pg = page;
	for (unsigned i = 0; i < page_size; i++)
		printf("%d", (int) pg[i]);
	printf("\n");
}

static void prepare_page(void **page, size_t page_size, char val)
{
	*page = mmap(NULL, page_size, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE, -1, 0);
	if (*page == MAP_FAILED)
		raise_error("Can't map a page", EXIT_FAILURE);
	fillout_page(*page, page_size, val);
}

static bool verify_page(void *page, char val, size_t page_size)
{
	char *pg = (char*) page;
	for (int i = 0; i < page_size; i++) {
		if (pg[i] != val)
			return false;
	}
	return true;
}

static void exchange_mappings(void **page1, void **page2, size_t pg_size)
{
	void *tmp_page = mmap(NULL, pg_size, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if (tmp_page == MAP_FAILED)
		raise_error("Can't map a tmp_page", EXIT_FAILURE);
	tmp_page = mremap(*page1, pg_size, pg_size, MREMAP_MAYMOVE|MREMAP_FIXED, tmp_page);
	if (tmp_page == MAP_FAILED)
		raise_error("Can't remap page1 to tmp_page", EXIT_FAILURE);
	*page1 = mremap(*page2, pg_size, pg_size, MREMAP_MAYMOVE|MREMAP_FIXED, *page1);
	if (*page1 == MAP_FAILED)
		raise_error("Can't remap page2 to page1", EXIT_FAILURE);
	*page2 = mremap(tmp_page, pg_size, pg_size, MREMAP_MAYMOVE|MREMAP_FIXED, *page2);
	if (*page2 == MAP_FAILED)
		raise_error("Can't remap tmp_page to page1", EXIT_FAILURE);
}

// thread flag functions
static char *start_flags;
static bool go_workers = true;

static bool is_flag_set(int thread_num)
{
	char val = start_flags[thread_num * CACHE_LINE_SIZE];
	if (val)
		return true;
	else
		return false;
}

void set_flag(int thread_num)
{
	start_flags[thread_num * CACHE_LINE_SIZE] = (char) true;
}

void drop_flag(int thread_num)
{
	start_flags[thread_num * CACHE_LINE_SIZE] = (char) false;
}

// thread functions

struct test_info {
	unsigned long iters;
	struct map_info *mapping;
	size_t pg_size;
};

struct worker_info {
	int id;
	struct test_info* t_info;
};

struct director_info {
	int num_threads;
	struct test_info* t_info;
};

static void *worker(void *thr_info)
{
	struct worker_info *w_info = thr_info;
	struct map_info *mapping = w_info->t_info->mapping;
	int pg_size = w_info->t_info->pg_size;
	while(go_workers)
		if (is_flag_set(w_info->id)) {
			for (int p_idx = 0; p_idx < NPAGE; p_idx++){
				if (!verify_page(mapping[p_idx].page, mapping[p_idx].val, pg_size))
					raise_error("Page verification failed.", EXIT_FAILURE);
			}
			drop_flag(w_info->id);
		}
}

static void print_flags()
{
	for (int i = 0; i < num_threads; i++)
		printf("%d", (int) start_flags[CACHE_LINE_SIZE * i]);
	printf("\n");
}

static void *director(void *thr_info)
{
	struct director_info *info = thr_info;
	struct test_info *t_info = info->t_info;
	struct map_info *mapping = t_info->mapping;
	size_t pg_size = t_info->pg_size;
	unsigned long iters = t_info->iters;
	int num_threads = info->num_threads;
	unsigned long runs_done = 1;
	int i = 0;
	while (true) {
		int counter = 0;
		// check whether all threads have done their page checks
		for (int i = 0; i < num_threads; i++) {
			if (is_flag_set(i))
				counter++;
		}
		// if so, exchange pages and set theads' start flags
		if (counter == 0) {
			// loop exit condition
			// wait until workers' finish the last iteration check
			// send them stop command
			if (runs_done == iters) {
				go_workers = false;
				printf("Stop command sent\n");
				break;
			}
			// page mappings exchange
			exchange_mappings(&mapping[0].page, &mapping[1].page, pg_size);
			// as mapping exchanged - exchange values to be checked
			int tmp = mapping[0].val;
			mapping[0].val = mapping[1].val;
			mapping[1].val = tmp;
			runs_done++;
			if (runs_done % REPORT_EACH_ITERS == 0) {
				printf("%.0f%% done\n", (1.0 * runs_done / PAGE_EXCHANGES_COUNT) * 100);
			}
			for (int i = 0; i < num_threads; i++)
				set_flag(i);
		}
	}
}

int main()
{
	num_threads = sysconf(_SC_NPROCESSORS_ONLN) - 2;
	printf("Num threads: %d\n", num_threads);
	size_t pg_size = sysconf(_SC_PAGE_SIZE);
	start_flags = (char*) calloc(CACHE_LINE_SIZE * num_threads, sizeof(char));
	if (start_flags == NULL)
			raise_error("Can't allocate memory for start_flags", EXIT_FAILURE);

	// create and initialize pages that is goinig to be used for testing
	struct map_info m_info[NPAGE];
	for (int i = 0; i < NPAGE; i++) {
		m_info[i].val = (char)i;
		prepare_page(&m_info[i].page, pg_size, m_info[i].val);
		if (!verify_page(m_info[i].page, m_info[i].val, pg_size))
			raise_error("a page verification failed.", EXIT_FAILURE);
	}

	struct test_info t_info;
	t_info.iters = PAGE_EXCHANGES_COUNT;
	t_info.mapping = m_info;
	t_info.pg_size = pg_size;

	struct worker_info w_info[num_threads];
	for (int i = 0; i < num_threads; i++) {
		w_info[i].id = i;
		w_info[i].t_info = &t_info;
	}

	struct director_info d_info;
	d_info.num_threads = num_threads;
	d_info.t_info = &t_info;

	pthread_attr_t attr;
	pthread_attr_t d_attr;
	pthread_t w_ids[num_threads];
	pthread_t d_id = 0;
	int r;
	r = pthread_attr_init(&attr);
	if (r)
		raise_error("Can't initiate thread attrubutes", r);
	r = pthread_attr_init(&d_attr);
	if (r)
		raise_error("Can't initiate thread attrubutes", r);
	pthread_attr_setdetachstate(&d_attr, PTHREAD_CREATE_JOINABLE);
	// start workers
	for (int i = 0; i < num_threads; i++) {
		r = pthread_create(&w_ids[i], &attr, &worker, (void*) &w_info[i]);
		if (r)
			raise_error("Can't start a worker thread", r);
	}

	// start a director thread
	r = pthread_create(&d_id, &d_attr, &director, (void*) &d_info);
	if (r)
		raise_error("Can't start a director thread", r);

	r = pthread_attr_destroy(&attr);
	if (r)
		raise_error("Can't destroy threads' attribute", r);

	printf("Test in progress. Waiting for threads to finish...\n");

	//join director
	r = pthread_join(d_id, NULL);
	if (r)
		raise_error("Error on joining the director thread", r);
	for (int i = 0; i < num_threads; i++) {
		r = pthread_join(w_ids[i], NULL);
		if (r)
			raise_error("Error on joining a thread", r);
	}
	free(start_flags);
	printf("Done!\n");
	exit(EXIT_SUCCESS);
}
