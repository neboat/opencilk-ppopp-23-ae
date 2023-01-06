#ifndef PARLAY_INTERNAL_SCHEDULER_PLUGINS_OPENCILK_H_
#define PARLAY_INTERNAL_SCHEDULER_PLUGINS_OPENCILK_H_
#if defined(PARLAY_OPENCILK)

#include <cstddef>

#include <cilk/cilk.h>
#include <cilk/cilk_api.h>

#ifdef SERIAL
#include <cilk/cilk_stub.h>
#elifdef OMPTASK
#include <omp.h>
#elifdef TBBTASK
extern "C" int __rts_get_num_workers();
extern "C" int __rts_get_worker_id();
#endif

namespace parlay {

// IWYU pragma: private, include "../../parallel.h"

#ifdef SERIAL
inline size_t num_workers() { return 1; }
inline size_t worker_id() {
  return 0;
}
#elifdef OMPTASK
inline size_t num_workers() { return omp_get_num_threads(); }
inline size_t worker_id() {
  return omp_get_thread_num();
}
#elifdef TBBTASK
inline size_t num_workers() { return __rts_get_num_workers(); }
inline size_t worker_id() {
  return __rts_get_worker_id();
}
#else
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
inline size_t num_workers() { return __cilkrts_get_nworkers(); }
inline size_t worker_id() { return __cilkrts_get_worker_number(); }
#pragma GCC diagnostic pop
#endif

template <typename Lf, typename Rf>
inline void par_do(Lf left, Rf right, bool) {
  cilk_spawn right();
  left();
  cilk_sync;
}

template <typename F>
inline void parallel_for(size_t start, size_t end, F f,
                         long granularity,
                         bool) {
  if (granularity == 0)
    cilk_for(size_t i=start; i<end; i++) f(i);
  else if ((end - start) <= static_cast<size_t>(granularity))
    for (size_t i=start; i < end; i++) f(i);
  else {
    size_t n = end-start;
    size_t mid = (start + (9*(n+1))/16);
    cilk_spawn parallel_for(start, mid, f, granularity);
    parallel_for(mid, end, f, granularity);
    cilk_sync;
  }
}

}  // namespace parlay

#endif
#endif  // PARLAY_INTERNAL_SCHEDULER_PLUGINS_OPENCILK_H_

