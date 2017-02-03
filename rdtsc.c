#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static inline uint64_t rdtsc(void)
{
        uint32_t lo, hi;
        __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
        return (uint64_t)hi << 32 | lo;
}

main(int argc, char **argv)
{
        uint64_t tsc;
        tsc = rdtsc();
        printf("cpu #%d, tsc: %llu\n", sched_getcpu(), tsc);
}
