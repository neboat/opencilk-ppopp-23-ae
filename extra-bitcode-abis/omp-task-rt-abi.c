#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <omp.h>

// Internal OpenMP runtime structures
typedef struct ident {
  int reserved_1;
  int flags;
  int reserved_2;
  int reserved_3;
  char const *psource;
} ident_t;

typedef int (*kmp_routine_entry_t)(int, void *);

typedef union kmp_cmplrdata {
  int priority;
  kmp_routine_entry_t destructors;
} kmp_cmplrdata_t;

typedef struct kmp_task {
  void *shareds;
  kmp_routine_entry_t routine;
  int part_id;
  kmp_cmplrdata_t data1;
  kmp_cmplrdata_t data2;
} kmp_task_t;

// OpenMP runtime methods
int __kmpc_global_thread_num(ident_t *loc_ref);
int __kmpc_omp_task(ident_t *loc_ref, int gtid,
                    kmp_task_t *new_task);
int __kmpc_omp_taskwait(ident_t *loc_ref, int gtid);

kmp_task_t *
__kmpc_omp_task_alloc(ident_t *loc_ref, int gtid, int flags,
                      size_t sizeof_kmp_task_t,
                      size_t sizeof_shareds,
                      kmp_routine_entry_t task_entry);

// Bitcode-ABI structures and globals

static ident_t __rts_ident = { 0, 2, 0, 22, "omp-task-rt-abi" };

#define __RTS_VERSION 1

struct __rts_stack_frame_version {
  uint32_t version_number;
};

typedef struct __rts_stack_frame {
  struct __rts_stack_frame_version version;
  int gtid;
} __rts_stack_frame_t;

// Bitcode-ABI hooks

__attribute__((always_inline)) int __rts_get_num_workers(void) {
  return omp_get_num_threads();
}

__attribute__((always_inline)) int __rts_get_worker_id(void) {
  return omp_get_thread_num();
}

__attribute__((always_inline)) void __rts_enter_frame(__rts_stack_frame_t *sf) {
  sf->version.version_number =
      ((__RTS_VERSION * 13) + offsetof(struct __rts_stack_frame, version)) * 13
      + offsetof(struct __rts_stack_frame, gtid);
  sf->gtid = __kmpc_global_thread_num(&__rts_ident);
}

__attribute__((always_inline)) void* __rts_get_args_from_task(void *task,
                                                              size_t alignment) {
  return (void *)((((uintptr_t)((kmp_task_t *)task)->shareds)
                   + alignment - 1) & -alignment);
  /* return (void *)(((kmp_task_t *)task)->shareds); */
}

__attribute__((always_inline)) void
__rts_spawn(__rts_stack_frame_t *sf, kmp_routine_entry_t fn, void *data,
            size_t data_size, size_t alignment) {
  kmp_task_t *task =
      __kmpc_omp_task_alloc(&__rts_ident, sf->gtid, /*flags*/ 1,
                            sizeof(kmp_task_t), data_size + alignment,
                            fn);
  /* char *dst = (char *)(((uintptr_t)(task->shareds) + alignment) */
  /*                      & -alignment); */
  char *dst = (char *)(((uintptr_t)(task->shareds) + alignment - 1)
                       & -alignment);
  /* char *dst = (char *)(task->shareds); */
  memcpy(dst, data, data_size);
  __kmpc_omp_task(&__rts_ident, sf->gtid, task);
}

__attribute__((always_inline)) void
__rts_sync(__rts_stack_frame_t *sf) {
  __kmpc_omp_taskwait(&__rts_ident, sf->gtid);
}

__attribute__((always_inline)) void
__rts_sync_nothrow(__rts_stack_frame_t *sf) {
  __kmpc_omp_taskwait(&__rts_ident, sf->gtid);
}

/* __attribute__((always_inline)) */
/* void __rts_reduce_add_double(double *reducer, double *view) { */
/*   /\* while (true) { *\/ */
/*   /\*   double old_val = *reducer; *\/ */
/*   /\*   double new_val = old_val + *view; *\/ */
/*   /\*   if (atomic_compare_exchange_strong_explicit( *\/ */
/*   /\*           (_Atomic double *)reducer, &old_val, new_val, *\/ */
/*   /\*           memory_order_acquire, memory_order_release)) *\/ */
/*   /\*     return; *\/ */
/*   /\*   __builtin_ia32_pause(); *\/ */
/*   /\* } *\/ */
/* #pragma omp atomic */
/*   *reducer += *view; */
/* } */

/* __attribute__((always_inline)) */
/* double __rts_reducer_read_double(double *reducer) { */
/*   return *reducer; */
/* } */

#define __rts_loop_grainsize_fn_impl(NAME, INT_T, VAL)                  \
  __attribute__((always_inline)) INT_T NAME(INT_T n) {                  \
    INT_T small_loop_grainsize = n / (8 * omp_get_num_threads());       \
    if (small_loop_grainsize <= 1)                                      \
      return 1;                                                         \
    INT_T large_loop_grainsize = 2048;                                  \
    return large_loop_grainsize < small_loop_grainsize                  \
        ? large_loop_grainsize : small_loop_grainsize;                  \
  }
#define __rts_loop_grainsize_fn(SZ, VAL)                                \
  __rts_loop_grainsize_fn_impl(__rts_loop_grainsize_##SZ, uint##SZ##_t, VAL)

__attribute__((always_inline)) uint8_t
__rts_loop_grainsize_8(uint8_t n) {
  uint8_t small_loop_grainsize = n / (8 * omp_get_num_threads());
  if (small_loop_grainsize <= 1)
    return 1;
  return small_loop_grainsize;
}

__rts_loop_grainsize_fn(16, 2048);
__rts_loop_grainsize_fn(32, 2048);
__rts_loop_grainsize_fn(64, 2048);
