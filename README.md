# Getting started

1. Load the docker image:

    docker load -i docker-opencilk-ppopp-23-ae.tar.gz

2. Run the docker image:

    docker run -it opencilk-ppopp-23-ae:latest /bin/bash

3. Once inside the container, enter the test directory:

    cd /usr/local/src/ppopp-23-ae

4. Use the `run_tests.py` script to run a small set of the benchmarks:

    python3 ./run_tests.py -u cilk5 -x baseline,pedigrees -t 5

Note: The source code for OpenCilk is available in
`/usr/local/src/opencilk`, if you would like to examine it.

TODO: Finish "Getting started" section.


# Step-by-Step instructions

These instructions guide you through evaluating the artifact by
rerunning the application tests for the empirical evaluation (Section
4) of the paper.  In particular, these steps will run the tests to
produce four CSV files that are analogous to Figures 3-6 in Section 4.

To generate the results from the empirical evaluation (Section 4) of
the paper, run:

    python3 ./run_tests.py -t 20 -c 1,24,48

The script will emit output as it compiles and runs all of the
application tests.  Ultimately, the script will produce four CSV
files, each of which corresponds with a Figure from Section 4 of the
paper:

- `baseline-<date-time-tag>.csv` presents the baseline performance
  measurements for the non-randomized benchmark programs.  These
  results correspond with Figure 3.

- `pedigrees-<date-time-tag>.csv` presents the performance results on
  the non-randomized benchmark programs with DPRNG support is enabled.
  These results correspond with Figure 4.

- `dprng-<date-time-tag>.csv` presents the performance results on the
  randomized benchmarks.  These results correspond with Figure 5.

- `cilkscale-compare-<date-time-tag>.csv` presents the performance
  comparison between the two versions of the Cilkscale scalability
  analyzer --- one of which is implemented as a standard library, the
  other is implemented using a bitcode-ABI file.  These results
  correspond with Figure 6.

***Note:*** We cannot guarantee that you will get exactly the same
performance results as in the paper if you do not run on the same
hardware.  However, you should observe similar trends to the
performance results highlighted in the paper, e.g., that the OpenCilk
runtime system outperforms the Cilk Plus runtime system.

The full set of application tests take a significant amount of time to
run.  Here are some ways to test the artifact more quickly:

- *Run fewer trials.*  For example, pass `-t 3` to `run_tests.py`,
  instead of `-t 20`, to run only 3 trials per executable.

- *Run parallel codes only in parallel.*  This is the default behavior
  if the `-c` flag is not specified to the script.

- *Use small inputs.* Pass `-s` to `run_tests.py` to instruct it to
   use small inputs for all tests.

- *Skip the GBBS test suites.* These test suites take a particularly
  long time to compile and run.  To run all other test suites, pass
  `-u cilk5,minife,random` to `run_tests.py`.

- *Run a subset of the experiments.* Use the `-x` flag to select which
   experiments to run.  For example, passing `-x baseline,pedigrees`
   to `run_tests.py` will run only the baseline and pedigree
   performance tests, which correspond with Figures 3 and 4,
   respectively.

- *Run only select programs.* Use the `--programs` flag to specify a
   list of benchmark programs to run.  Note that the corresponding
   test suites and experiments must be enabled for each of these
   programs to run.

For more information on how to run the test script, use `-h`:

    python3 ./run_tests.py -h


# Adding more tests to run

You can add a new application to an existing test suite as follows.

- To run additional GBBS tests, add the GBBS test to either
  `all_gbbs_progs`, if the GBBS test is not randomized, or
  `all_rng_gbbs_progs`, if the test is randomized.  Note that, in
  these lists, the `//benchmarks` prefix on the benchmark name is
  elided.

- For a brand-new (non-randomized) Cilk program built using Make, add
  the Cilk program to the `cilk5` subdirectory, update the Makefile
  therein to build that program, and then add the name of that
  program to the `all_cilk5_progs` list at the top of `run_tests.py`.


# Additional information

## Warnings that are safe to ignore

The following warnings are safe to ignore:

When compiling `rectmul.c`:

    warning: variable `flops`' set but not used

    warning: function `add_matrix` is not needed and will not be emitted

When compiling `heat.c`:

    warning: variable 'l' set but not used 

    warning: variable 'ret' set but not used 

When compiling `lu.c`:

    warning: variable `max_diff`' set but not used 

    warning: variable `L01`' set but not used 

    warning: variable `U10`' set but not used 

At the end of compiling miniFE:

    warning: argument unused during compilation: '-mllvm -csi-tool-bitcode=...'

When compiling and running GBBS (randomized or non-randomized) benchmarks:

    warning: unused type alias 'iter1_t'

    warning: unused type alias 'iter2_t'

    warning: 'aligned_storage' defined as a class template here but previously declared as a struct tempate;

    warning: cast from 'const type-parameter-0-0 *` to 'void *' drops const qualifier

    warning: variable 'reachable' set but not used

    warning: unused variable 'rand_pos'

    usage: /root/.cache/bazel/_bazel_root/...
    Aborted (core dumped)
