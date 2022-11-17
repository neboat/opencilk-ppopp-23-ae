# Introduction

This document describes how to evaluate the artifact for the PPoPP
2023 paper submission, "NAC: A Moduler and Extensible Software
Infrastructure for Fast Task-Parallel Code."  This evaluation supports
assessment of the functionality and reusability of the artifact (red
badge) and validation of the results of the empirical evaluation,
in Section 4 of the paper (blue badge).

In this artifact and document, the paper's anonymized names for the
system and its components have been deanonymized:
- The name of the system, "NAC," has been deanonymized to "OpenCilk."
- The name for the scalability analyzer, "NAC SA," has been
  deanonymized to "Cilkscale."

This artifact consists of a Docker image containing precompiled
binaries for the OpenCilk system as well as source code for all
benchmark programs used in the empirical evaluation of the paper.
Building OpenCilk from source is a time-consuming and
computing-resource-intensive process.  Therefore, we are providing
this Docker image with precompiled binaries to facilitate this
evaluation.  These binaries have been compiled for Intel x86-64.

The source code for OpenCilk, including the compiler, runtime
system, and tools, can be found in `/usr/local/src/opencilk`
within the Docker image.

# Getting started guide

The following steps guide you through setting up the Docker image
for the artifact evaluation and verifying that it runs as intended
on your system.

*Prerequisites:* The Docker image has been tested on Intel x86-64
machines running recent versions of Linux, such as Ubuntu 22.04,
and Docker version 20.10.21.  You can find instructions on how to
install a recent version of Docker on <https://docs.docker.com/>.
For example, [here](https://docs.docker.com/engine/install/ubuntu/)
are the instructions to install Docker on Ubuntu.

1. Download the Docker image from <https://people.csail.mit.edu/neboat/opencilk-ppopp-23-ae/docker-opencilk-ppopp-23-ae.tar.gz>:

```console
wget https://people.csail.mit.edu/neboat/opencilk-ppopp-23-ae/docker-opencilk-ppopp-23-ae.tar.gz
```

2. Load the Docker image:

```console
docker load -i docker-opencilk-ppopp-23-ae.tar.gz
```

3. Run the Docker image:

```console
docker run -it opencilk-ppopp-23-ae /bin/bash
```

4. Once inside the container, enter the test directory:

```console
cd /usr/local/src/ppopp-23-ae
```

5. Use the `run_tests.py` script with the `--quick-test` flag 
   to verify that the experiments run correctly on the various
   benchmark suites:

```console
python3 ./run_tests.py --quick-test
```

The `run_tests.py` script will produce informational output 
about the tests it is building and running as it executes.
The quick-test run takes approximately 6.5 minutes on a modern
Intel x86-64 system with 8 processor cores, such as an
[AWS c5.4xlarge instance](https://aws.amazon.com/ec2/instance-types/c5/).
If all steps complete successfully, then at the end of the
quick-test run, you should see something like the following
message:

```console
Tests completed in 397.1234 seconds.
```

# Step-by-step instructions

These instructions will guide you through using the Docker image to 
evaluate the artifact by rerunning the experiments for the empirical 
evaluation of the paper (Section 4).  In particular, these steps will
produce four CSV files that are analogous to Figures 3-6 in Section 4.

Although we cannot guarantee that you can exactly replicate the running
times presented in the paper --- due to differences in computer
hardware and system configuration --- you can use this artifact to 
replicate the following results:
- *OpenCilk functionality:* OpenCilk supports compiling and running a
  variety of Cilk programs using either the Cilk Plus or OpenCilk 
  runtime systems.
- *Figure 3 performance trend:* Across the non-randomized benchmarks,
  the baseline performance of OpenCilk in generally faster than Cilk
  Plus, especially for parallel execution.
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
steps:
1. Run the `run_tests.py` script with appropriate parameters.

2. Copy the aggregate CSV files out of the Docker image, e.g., by
   running commands like the following outside of Docker, replacing
   `<tag>` with the appropriate tag identifying the run.

```console
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/baseline-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/pedigrees-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/dprng-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/cilkscale-compare-<tag>.csv .
```

3. Examine these CSV files in whichever spreadsheet program you 
   prefer, such as Google Sheets or Microsoft Excel.

The following sections describe these high-level steps in detail.

## Running `run_tests.py`

The `run_tests.py` script accepts a variety of options to run
the empirical evaluation in different configurations, in order
to accommodate different computer systems.  The following command
gives an overview of the options that `run_tests.py` accepts:

```console
python3 ./run_tests.py -h
```

Section 4 describes the system configuration and parameters used for
the paper's empirical evaluation, including the number of times each
executable was run (20) and the numbers of CPU processor cores tested
on (1, 24, and 48).  If you have **ample time** --- approximately a
day --- **and computer resources** --- at least 48 CPU processor cores
--- you can use the `run_tests.py` script to run the tests using
similar parameters on your system as follows:

 ```console
 python3 ./run_tests.py -t 20 -c 1,24,48
 ```

There are several ways to run the application tests and thereby
evaluate the artifact more quickly.

- By default, running `python3 ./run_tests.py` without any arguments
  will run all benchmark programs with 5 trials each and run the 
  parallel executables only on the number of CPU cores on the system.
  These defaults will run the application tests more quickly, but
  the final performance results may exhibit more variability between
  runs, and it will not include 1-core running times for the parallel
  executables.  ***TODO: Example running time of this configuration.***

- You can run the benchmark tests with **smaller inputs** by passing
  the `-s` flag to `run_tests.py`.

- You can specify **different CPU counts** to run the parallel
  executables on using the `-c` flag.  For example, on a system with
  24 CPU cores, the flag `-c 1,24` will run all parallel executables
  on 1 and 24 CPU cores.

- You can select a **subset of the programs** to run using the
  `--programs` flag.  In particular, the GBBS benchmarks take a
  significant amount of time to compile, and some take substantial
  time to run.  To run only the BFS and KCore benchmarks from GBBS,
  for example, pass
  `--programs BFS/NonDeterministicBFS:BFS_main,KCore/JulienneDBS17:KCore_main`
  to `run_tests.py`.

- You can run specify the **number of trials** to run each executable
  using the `-t` flag.  For example, specifying `-t 10` will run each
  executable 10 times, and specifying `-t 3` will run each executable
  3 times.  Each running time in the final CSVs will be the median of
  all trials.  Please note that we do not recommend running the 
  executables with fewer trials, as doing so will increase the 
  variability of the measured results.

## Getting the CSV files

When the `run_tests.py` script is run to perform all experiments, it 
will generate four CSV files containing aggregated performance results
for those experiments: `baseline-<tag>.csv`, `pedigrees-<tag>.csv`,
`dprng-<tag>.csv`, and `cilkscale-compare-<tag>.csv`.  In these CSV
filenames, `<tag>` denotes with a ***run tag***, which includes the
year, month, day, hour, and minute of the invocation of the 
`run_tests.py` script.  If small inputs are used, the run tag will
also include the keyword `small`.

You can copy the CSV files produced by `run_tests.py` out of
the Docker image using the `docker cp` command on each file.
For example, running the following commands outside of the Docker
image will copy out the four CSV files with aggregated
performance results, replacing `<tag>` with the true run tag:

```console
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/baseline-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/pedigrees-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/dprng-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/cilkscale-compare-<tag>.csv .
```

Note that `docker ps -alq` provides a convenient way to get the ID
of the latest container created.  If you are using other Docker
containers at the same time, use `docker ps` to find the container
ID corresponding with your run of the `opencilk-ppopp-23-ae` image.

## Examining the CSV files

The generated CSV files correspond with the empirical evaluation
in the paper as follows:
- The `baseline-<tag>.csv` file contains performance results for
  the baseline performance of the different systems.  These
  results correspond with Figure 3 in the paper.
- The `pedigrees-<tag>.csv` file contains performance results for
  the performance of OpenCilk on the non-randomized benchmarks
  when pedigree and DPRNG support is enabled.  These results
  correspond with Figure 4 in the paper.
- The `dprng-<tag>.csv` file contains performance results for
  the performance of OpenCilk and Cilk Plus on randomized
  benchmarks using different DPRNGs.  These results correspond
  with Figure 5 in the paper.
- The `cilkscale-compare-<tag>.csv` file contains performance
  results on the non-randomized benchmarks of OpenCilk run with
  either the library-based or bitcode-ABI-based Cilkscale tool.
  These results correspond with Figure 6 in the paper.

In these CSV files, rows identify different programs, and columns
generally identify the system (e.g., Cilk Plus or OpenCilk) and
CPU count.  For example, the column heading `opencilk 8` 
indicates that the running times in that column were produced
by compiling and running the program using OpenCilk on 8 CPU
cores.  In the `dprng-<tag>.csv` file, the column headings also
identify the DPRNG used.  In the `cilkscale-compare-<tag>.csv`
file, the keywords `cilkscale` and `cilkscale-bitcode` in the
column headings indicate that the programs were compiled and run
with the library-based or bitcode-ABI-based versions,
respectively, of Cilkscale.

# Extensions

TODO: Revise this part

## Using OpenCilk directly

Note: The source code for OpenCilk is available in
`/usr/local/src/opencilk`, if you would like to examine it.

## Adding more tests to run

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

The `run_tests.py` script will save within the `./rawdata` subdirectory
the verbose output of building the benchmark programs as well as the
performance results of each run.  The build output will be 
written to `./rawdata/build-<tag>.out`, and the raw performance data
for a given program run will be written to a CSV in `./rawdata`
named with the test suite, program, system, and run tag.

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


--------
Old content

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
