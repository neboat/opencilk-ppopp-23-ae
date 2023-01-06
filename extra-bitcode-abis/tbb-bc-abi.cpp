// -*- C++ -*-
#include <atomic>
#include <cstring>
#include <oneapi/tbb/task_group.h>
#include <oneapi/tbb/task_arena.h>

struct __rts_stack_frame {
  oneapi::tbb::task_group tg;
};

extern "C" {

__attribute__((always_inline)) int __rts_get_num_workers(void) {
  return oneapi::tbb::this_task_arena::max_concurrency();
}

__attribute__((always_inline)) int __rts_get_worker_id(void) {
  return oneapi::tbb::this_task_arena::current_thread_index();
}

__attribute__((always_inline)) void __rts_enter_frame(__rts_stack_frame *sf) {
  new (&sf->tg) tbb::task_group();
}

__attribute__((always_inline)) void
__rts_spawn(__rts_stack_frame *sf, void(*fn)(void *), void *data,
            size_t data_size, size_t alignment) {
  char *data_cpy = (char *)aligned_alloc(alignment, data_size);
  memcpy(data_cpy, data, data_size);
  sf->tg.run([fn, data_cpy] { fn(data_cpy); free(data_cpy); });
}

__attribute__((always_inline)) void
__rts_sync(__rts_stack_frame *sf) {
  sf->tg.wait();
}

__attribute__((always_inline)) void
__rts_sync_nothrow(__rts_stack_frame *sf) {
  sf->tg.wait();
}

__attribute__((always_inline)) void __rts_leave_frame(__rts_stack_frame *sf) {
  sf->tg.~task_group();
}

// __attribute__((always_inline))
// void __rts_reduce_add_double(double *reducer, double *view) {
//   while (true) {
//     double old_val = *reducer;
//     double new_val = old_val + *view;
//     if (std::atomic_compare_exchange_strong_explicit(
//             reinterpret_cast<std::atomic<double> *>(reducer), &old_val, new_val,
//             std::memory_order_acquire, std::memory_order_release))
//       return;
//     __builtin_ia32_pause();
//   }
// }

#define __rts_loop_grainsize_fn_impl(NAME, INT_T, VAL)                  \
  __attribute__((always_inline)) INT_T NAME(INT_T n) {                  \
    INT_T small_loop_grainsize = n / (8 * __rts_get_num_workers());     \
    if (small_loop_grainsize <= 1)                                      \
      return 1;                                                         \
    INT_T large_loop_grainsize = 2048;                                  \
    return large_loop_grainsize < small_loop_grainsize ?                \
        large_loop_grainsize : small_loop_grainsize;                    \
  }

#define __rts_loop_grainsize_fn(SZ, VAL)                                \
  __rts_loop_grainsize_fn_impl(__rts_loop_grainsize_##SZ, uint##SZ##_t, VAL)

__attribute__((always_inline)) uint8_t __rts_loop_grainsize_8(uint8_t n) {
  uint8_t small_loop_grainsize = n / (8 * __rts_get_num_workers());
  if (small_loop_grainsize <= 1)
    return 1;
  return small_loop_grainsize;
}

  __rts_loop_grainsize_fn(16, 2048);
  __rts_loop_grainsize_fn(32, 2048);
  __rts_loop_grainsize_fn(64, 2048);
}
