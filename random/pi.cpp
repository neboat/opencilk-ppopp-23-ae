#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <iostream>

#include <cilk/cilk.h>
#include <cilk/cilk_api.h>
#ifdef CILKPLUS
#include <cilk/reducer_opadd.h>
#else
#include <cilk/opadd_reducer.h>
#endif

#include "cilkpub/dotmix.h"

cilkpub::DotMixPrime dprng;

double pi_pedigree(int64_t N) {
#ifdef CILKPLUS
  cilk::reducer_opadd<int64_t> inside(0);
#else
  cilk::opadd_reducer<int64_t> inside(0);
#endif
  cilk_for (int64_t i = 0; i < N; ++i) {
    __cilkrts_bump_worker_rank();
    // Get two samples
    uint64_t x_sample = dprng.get();
    uint64_t y_sample = dprng.get();

    double x = static_cast<double>(x_sample)/static_cast<double>(std::numeric_limits<uint64_t>::max());
    double y = static_cast<double>(y_sample)/static_cast<double>(std::numeric_limits<uint64_t>::max());
    double m = (x*x) + (y*y);
    
    // Check if sample is inside of the circle
    if (m <= 1)
      ++inside;
  }

#ifdef CILKPLUS
  return 4.0 * static_cast<double>(inside.get_value()) / static_cast<double>(N);
#else
  return 4.0 * static_cast<double>(inside) / static_cast<double>(N);
#endif
}

#ifdef OPENCILK
double pi_dprand(int64_t N) {
  cilk::opadd_reducer<int64_t> inside(0);

  cilk_for (int64_t i = 0; i < N; ++i) {
    __cilkrts_bump_worker_rank();
    // Get two samples
    uint64_t x_sample = __cilkrts_get_dprand();
    uint64_t y_sample = __cilkrts_get_dprand();

    double x = static_cast<double>(x_sample)/static_cast<double>(std::numeric_limits<uint64_t>::max());
    double y = static_cast<double>(y_sample)/static_cast<double>(std::numeric_limits<uint64_t>::max());
    double m = (x*x) + (y*y);
    
    // Check if sample is inside of the circle
    if (m <= 1)
      ++inside;
  }

  // return 4.0 * static_cast<double>(inside) / static_cast<double>(N);
  return 4.0 * static_cast<double>(inside) / static_cast<double>(N);
}
#endif // OPENCILK

int main(int argc, char *argv[]) {
  uint64_t seed = 0x8c679c168e6bf733ul;
  int num_trials = 20;
  int64_t N = 1024 * 1024;

  if (argc > 1) {
    N = atol(argv[1]);

    if (argc > 2)
      num_trials = atoi(argv[2]);

    if (argc > 3)
      seed = atol(argv[3]);
  }

  dprng.init_seed(seed);
#ifdef OPENCILK
  __cilkrts_dprand_set_seed(seed);
  __cilkrts_init_dprng();
#endif // OPENCILK

#ifdef OPENCILK
  // cilk_scope {
  for (int t = 0; t < num_trials; ++t) {
    auto start = std::chrono::steady_clock::now();
    double res = pi_dprand(N);
    auto end = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    std::cout << "pi_dprand(" << N << ") = " << res << ", time " << elapsed.count() << "s\n";
  }
  // }
#endif // OPENCILK

  for (int t = 0; t < num_trials; ++t) {
    auto start = std::chrono::steady_clock::now();
    double res = pi_pedigree(N);
    auto end = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    std::cout << "pi_pedigree(" << N << ") = " << res << ", time " << elapsed.count() << "s\n";
  }

  return 0;
}
