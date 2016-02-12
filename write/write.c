#include <stdio.h>
#include <unistd.h>

main() {
	FILE *fp;

  	while (1) {
		fp = fopen("test.txt", "w+");
		fprintf(fp, "This is testing for fprintf...\n");
		fputs("This is testing for fputs...\n", fp);
		fclose(fp);
		sleep(1);
	}
}
