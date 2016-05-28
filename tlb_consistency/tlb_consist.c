#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <pthread.h>
#include <stdarg.h>
#include <unistd.h>

#if defined (__WIN32__)
	#include <windows.h>
#else
	#include <sys/mman.h>
#endif

#define NPAGE 2
#define CACHE_LINE_SIZE 64
#define PAGE_EXCHANGES_COUNT 1000000
#define REPORT_EACH_ITERS 100000

// page pointer type
#if defined (__WIN32__)
	typedef PVOID p_ptr;
	HANDLE handles[NPAGE];
	static bool prepare_handles_needed = true;
#else
	typedef void* p_ptr;
#endif

static int num_threads;
static size_t page_size;

// common functions
static void raise_error(const char *fmt, ...)
{
	int msg_size = 256;
	char msg[msg_size];
	va_list args;
	
	va_start(args, fmt);
	vsnprintf(msg, msg_size, fmt, args);
	va_end(args);
	perror(msg);
	exit(EXIT_FAILURE);
}

// page functions
struct map_info {
	p_ptr page;
	char val;
#if defined (__WIN32__)
	int handle_idx;
#endif
};

static void fillout_page(struct map_info *map)
{
	char *pg = map->page;
	for (unsigned i = 0; i < page_size; i++)
		pg[i] = map->val;
}

static void print_page(p_ptr page)
{
	char *pg = page;
	for (unsigned i = 0; i < page_size; i++)
		printf("%d", (int) pg[i]);
	printf("\n");
}

#if defined (__WIN32__)
void extract_os_info() 
{
	SYSTEM_INFO sysinfo;
	GetSystemInfo(&sysinfo);
	num_threads = sysinfo.dwNumberOfProcessors;
	page_size = sysinfo.dwPageSize;
}

void create_handles()
{
	int n_size = 32;
	char h_name[n_size];
	for (int i = 0; i < NPAGE; i++) {
		snprintf(h_name, n_size, "Global\\mapped_file%d", i);
		handles[i] = CreateFileMapping(
				INVALID_HANDLE_VALUE,
				NULL,
				PAGE_READWRITE,
				0,
				page_size,
				h_name);

		if (handles[i] == NULL) {
			raise_error("can't create mapping (%d)", GetLastError());
		}
	}
}

static void prepare_page(struct map_info *map_info, int map_idx)
{
	if(prepare_handles_needed) {
		create_handles();
		prepare_handles_needed = false;
	}

	map_info[map_idx].page =  MapViewOfFile(
					handles[map_idx],
					FILE_MAP_ALL_ACCESS,
					0,
					0,
					page_size);

	if (map_info[map_idx].page == NULL) {
		raise_error("can't map a view (%d)", GetLastError());
	}
	map_info[map_idx].handle_idx = map_idx;
	
	map_info[map_idx].val = map_idx;
	fillout_page(&map_info[map_idx]);
}

void chng_map(p_ptr *dest_view, int handle_idx)
{
	LPVOID r;
	p_ptr tmp_addr = *dest_view;
	UnmapViewOfFile(tmp_addr);
	r = MapViewOfFileEx(
		handles[handle_idx],
		FILE_MAP_ALL_ACCESS,
		0,
		0,
		page_size,
		tmp_addr);

	if (r == NULL) {
		raise_error("can't change mapping (%d)", GetLastError());
	}
	
	if (r != tmp_addr) {
		raise_error("map failed: remapping to a different address");
	}
			
	*dest_view = tmp_addr;
}

static void exchange_mappings(struct map_info *map1, struct map_info *map2)
{
	chng_map(&map1->page, map2->handle_idx);
	chng_map(&map2->page, map1->handle_idx);
		
	int old_val = map1->val;
	int old_handle_idx = map1->handle_idx;
	
	map1->val = map2->val;
	map1->handle_idx = map2->handle_idx;
	
	map2->val = old_val;
	map2->handle_idx = old_handle_idx;
}

#else

int extract_os_info()
{
	num_threads = sysconf(_SC_NPROCESSORS_ONLN);
	page_size = sysconf(_SC_PAGE_SIZE);
}

static void prepare_page(struct map_info *map_info, int map_idx)
{
	map_info[map_idx].page = mmap(
					NULL,
					page_size,
					PROT_READ|PROT_WRITE,
					MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE,
					-1,
					0);
	if (map_info[map_idx].page == MAP_FAILED)
		raise_error("Can't map a page");
	map_info[map_idx].val = map_idx; 
	fillout_page(&map_info[map_idx]);
}

static void exchange_mappings(struct map_info *map1, struct map_info *map2)
{
	void *tmp_page = mmap(NULL, page_size, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if (tmp_page == MAP_FAILED)
		raise_error("Can't map a tmp_page");
	tmp_page = mremap(map1->page, page_size, page_size, MREMAP_MAYMOVE|MREMAP_FIXED, tmp_page);
	if (tmp_page == MAP_FAILED)
		raise_error("Can't remap page1 to tmp_page");
	map1->page = mremap(
			map2->page, page_size, page_size, MREMAP_MAYMOVE|MREMAP_FIXED, map1->page);
	if (map1->page == MAP_FAILED)
		raise_error("Can't remap page2 to page1");
	map2->page = mremap(
			tmp_page, page_size, page_size, MREMAP_MAYMOVE|MREMAP_FIXED, map2->page);
	if (map2->page == MAP_FAILED)
		raise_error("Can't remap tmp_page to page1");
   
    	map2->val ^= map1->val;
	map1->val ^= map2->val;
	map2->val ^= map1->val;
}

#endif

static bool verify_page(p_ptr page, char val)
{
	char *pg = (char*) page;
	for (int i = 0; i < page_size; i++) {
		if (pg[i] != val)
			return false;
	}
	return true;
}


// thread flag functions
static char *start_flags;
static volatile bool go_workers = true;

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
	while(go_workers)
		if (is_flag_set(w_info->id)) {
			for (int p_idx = 0; p_idx < NPAGE; p_idx++){
				if (!verify_page(mapping[p_idx].page, mapping[p_idx].val))
					raise_error("Page verification failed.");
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
			exchange_mappings(&mapping[0], &mapping[1]);
			runs_done++;
			if (runs_done % REPORT_EACH_ITERS == 0) {
				printf("%.0f%% done\n", (1.0 * runs_done / PAGE_EXCHANGES_COUNT) * 100);
			}
			for (int i = 0; i < num_threads; i++)
				set_flag(i);
		}
	}
}

int main(int argc, char** argv)
{
	extract_os_info();
	
	num_threads = num_threads - 1;
	if (num_threads < 1)
		raise_error("Too few cores detected for the test run. Min 2 cores needed");

	int res = 0;
	while((res = getopt(argc, argv, "t:h")) != -1) {
		switch(res) {
		case 't':
			num_threads = atoi(optarg);
			if (num_threads < 1)
				raise_error("Wrong number of threads. Should be more than 0.");
			break;
		case 'h':
			printf("Usage: tlb_consist [OPTIONS]\n");
			printf("\t-t <num_threads>      Set number of threads\n");
			printf("\t-h                    Show this message\n");
			exit(EXIT_SUCCESS);
			break;
		case '?':
			exit(EXIT_SUCCESS);
			break;
		}

	}
	
	printf("Num threads: %d\n", num_threads);
	
	start_flags = (char*) calloc(CACHE_LINE_SIZE * num_threads, sizeof(char));
	if (start_flags == NULL)
			raise_error("Can't allocate memory for start_flags");

	// create and initialize pages that is goinig to be used for testing
	struct map_info m_info[NPAGE];
	for (int i = 0; i < NPAGE; i++) {
		prepare_page(m_info, i);
		if (!verify_page(m_info[i].page, m_info[i].val))
			raise_error("a page verification failed.");
	}

	struct test_info t_info;
	t_info.iters = PAGE_EXCHANGES_COUNT;
	t_info.mapping = m_info;

	struct worker_info w_info[num_threads];
	for (int i = 0; i < num_threads; i++) {
		w_info[i].id = i;
		w_info[i].t_info = &t_info;
	}

	struct director_info d_info;
	d_info.num_threads = num_threads;
	d_info.t_info = &t_info;

	pthread_attr_t attr;
	pthread_t w_ids[num_threads];
	pthread_t d_id;
	int r;
	r = pthread_attr_init(&attr);
	if (r)
		raise_error("Can't initiate thread attrubutes (%d)", r);
	// start workers
	for (int i = 0; i < num_threads; i++) {
		r = pthread_create(&w_ids[i], &attr, &worker, (void*) &w_info[i]);
		if (r)
			raise_error("Can't start a worker thread (%d)", r);
	}

	// start a director thread
	r = pthread_create(&d_id, &attr, &director, (void*) &d_info);
	if (r)
		raise_error("Can't start a director thread (%d)", r);

	r = pthread_attr_destroy(&attr);
	if (r)
		raise_error("Can't destroy threads' attribute (%d)", r);

	printf("Test in progress. Waiting for threads to finish...\n");

	//join director
	r = pthread_join(d_id, NULL);
	if (r)
		raise_error("Error on joining the director thread (%d)", r);

	//join workers
	for (int i = 0; i < num_threads; i++) {
		r = pthread_join(w_ids[i], NULL);
		if (r)
			raise_error("Error on joining a worker thread (%d)", r);
	}
	free(start_flags);
	printf("Done!\n");
	exit(EXIT_SUCCESS);
}
