# Introduction

This document describes how to evaluate the artifact for the PPoPP
2023 paper submission, "NAC: A Moduler and Extensible Software
Infrastructure for Fast Task-Parallel Code."  This evaluation supports
assessment of the functionality and reusability of the artifact (red
badge) and validation of the results of the empirical evaluation,
in Section 4 of the paper (blue badge).

In this artifact and document, the paper's anonymized names for the
system and its components have been replaced with their true names:
- The name of the system, "NAC," has been deanonymized to "OpenCilk."
- The name for the scalability analyzer, "NAC SA," has been
  deanonymized to "Cilkscale."

This artifact consists of a Docker image containing precompiled
binaries for the whole OpenCilk system as well as source code for all
benchmark programs used in the empirical evaluation of the paper
(Section 4).  Building OpenCilk from source is a time-consuming and
computing-resource-intensive process, which is why we are providing
the Docker image with precompiled binaries.

Although it's not the focus of this artifact evaluation, if you wish,
you can browse the OpenCilk source code in the directory
`/usr/local/src/opencilk` within the Docker image.

# Getting started guide

This Docker image has been tested on Intel x86_64 machines running
recent versions of Linux, such as Ubuntu 22.04, and Docker version
20.10.21.

1. Download the Docker image from <>:

	```wget <>```

2. Load the Docker image:

    ```docker load -i docker-opencilk-ppopp-23-ae.tar.gz```

3. Run the Docker image:

    ```docker run -it opencilk-ppopp-23-ae:latest /bin/bash```

4. Once inside the container, enter the test directory:

    ```cd /usr/local/src/ppopp-23-ae```

5. Use the `run_tests.py` script with `--fast` to verify that the
   experiments run correctly on the various benchmark suites:

    ```python3 ./run_tests.py --quick-test```

The quick-test run takes about 6.5 minutes on a system with 8
processor cores.

Note: The source code for OpenCilk is available in
`/usr/local/src/opencilk`, if you would like to examine it.

TODO: Finish "Getting started" section.


# Step-by-step instructions

These instructions guide you through evaluating the artifact by
rerunning the application tests for the empirical evaluation (Section
4) of the paper.  In particular, these steps will run the tests to
produce four CSV files that are analogous to Figures 3-6 in Section 4.

Although we cannot guarantee that you can exactly replicate the
running times in the paper, you can use this artifact to replicate the
following results:
- *OpenCilk functionality:* OpenCilk supports compiling and running a
  wide variety of Cilk programs.
- *OpenCilk support for task-parallel runtimes:* The OpenCilk system
  supports compiling and running these programs to run using either
  the Cilk Plus or Opencilk runtime systems.
- *Figure 3 performance trend:* Across the non-randomized benchmarks,
  the baseline performance of OpenCilk in generally faster than Cilk
  Plus, especially for parallel execution.  (Figure 3)
- *Figure 4 performane trend:* Across the non-randomized benchmarks,
  OpenCik runs efficient with pedigree and DPRNG support enabled,
  generally incurring low overheads compared to the OpenCilk's
  baseline performance and often outperforming Cilk Plus.
- *Figure 5 performance trend:* On randomized benchmarks, OpenCilk
  supports efficient use of the DotMix DORNG, often outperforming Cilk
  Plus using DotMix.  In addition, OpenCilk's builtin DPRNG improves
  the performance of these benchmarks compared to using DotMix.
- *Figure 6 performance trend:* The bitcode-ABI version of Cilkscale
  generally runs faster than the library version of Cilkscale.

At a high level, you can replicate these results using the following
high-level steps:
1. Run the `./run_tests.py` with appropriate parameters (see below).

2. Copy the aggregate CSV files out of the docker image:

    ```docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/*.csv .```

3. Examine these CSV files in whichever program you prefer, e.g.,
   Google Sheets or Microsoft Excel.

## Parameters for `run_tests.py`

Section 4 describes the system configuration and parameters used for
the paper's empirical evaluation, including the number of times each
executable was run (20) and the numbers of CPU processor cores tested
on (1, 24, and 48).  If you have ample time --- approximately a day
--- and computer resources --- at least 48 CPU processor cores --- you
can use the `run_tests.py` script to run the tests using similar
parameters on your system as follows:

    python3 ./run_tests.py -t 20 -c 1,24,48


EDIT THIS:


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


## CSV files

Each CSV file is tagged with the date, hour, and minute when
`run_tests.py` was invoked.  The tag may be prefixed with `small` if
small inputs were used.  The CSV files correspond with the figures in
Section 4 of the paper as follows:

- The file `baseline-<tag>.csv` presents the baseline performance
  measurements for the non-randomized benchmark programs.  These
  results correspond with Figure 3.

- The file `pedigrees-<tag>.csv` presents the performance results on
  the non-randomized benchmark programs with DPRNG support is enabled.
  These results correspond with Figure 4.

- The file `dprng-<tag>.csv` presents the performance results on the
  randomized benchmarks.  These results correspond with Figure 5.

- The file `cilkscale-compare-<tag>.csv` presents the performance
  comparison between the two versions of the Cilkscale scalability
  analyzer --- one of which, labeled `cilkscale`, is implemented as a
  standard library, the other, labeled `cilkscale-bitcode` is
  implemented using a bitcode-ABI file.  These results correspond with
  Figure 6.



The script will emit output as it compiles and runs all of the
application tests.  Ultimately, the script will produce four CSV
files, each of which corresponds with a Figure from Section 4 of the
paper:


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


# Troubleshooting



# Additional information

## Build warnings that are safe to ignore

The following warnings in the verbose build output (saved in
`./rawdata/build-<tag>.out`) are safe to ignore:

When compiling `qsort.cpp`:

	warning: 'bind2nd<std::less<int>, int>' is deprecated

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
