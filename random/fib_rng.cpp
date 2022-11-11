#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <iostream>

#include <cilk/cilk.h>
#include <cilk/cilk_api.h>

#include "cilkpub/dotmix.h"

cilkpub::DotMixPrime dprng;

int64_t fib_pedigree(int64_t n) {
  if (n < 2) {
    return dprng.get();
  }
  int64_t x = cilk_spawn fib_pedigree(n-1);
  int64_t y = fib_pedigree(n-2);
  cilk_sync;
  return x + y;
}

#ifdef OPENCILK
int64_t fib_dprand(int64_t n) {
  if (n < 2) {
    return __cilkrts_get_dprand();
  }
  int64_t x = cilk_spawn fib_dprand(n-1);
  int64_t y = fib_dprand(n-2);
  cilk_sync;
  return x + y;
}
#endif

int main(int argc, char *argv[]) {
  uint64_t seed = 0x8c679c168e6bf733ul;
  int num_trials = 20;
  int64_t n = 30;

  if (argc > 1) {
    n = atol(argv[1]);

    if (argc > 2)
      num_trials = atoi(argv[2]);

    if (argc > 3)
      seed = atol(argv[3]);
  }

  dprng.init_seed(seed);
#ifdef OPENCILK
  __cilkrts_dprand_set_seed(seed);
  __cilkrts_init_dprng();

  // cilk_scope {
  for (int t = 0; t < num_trials; ++t) {
    auto start = std::chrono::steady_clock::now();
    int64_t res = fib_dprand(n);
    auto end = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    std::cout << "fib_dprand(" << n << ") = " << res << ", time " << elapsed.count() << "s\n";
  }
  // }
#endif

  for (int t = 0; t < num_trials; ++t) {
    auto start = std::chrono::steady_clock::now();
    int64_t res = fib_pedigree(n);
    auto end = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    std::cout << "fib_pedigree(" << n << ") = " << res << ", time " << elapsed.count() << "s\n";
  }

  return 0;
}
