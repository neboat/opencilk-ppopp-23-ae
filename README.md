# Introduction

This document describes how to evaluate the artifact for the PPoPP
2023 paper, "OpenCilk: A Modular and Extensible Software
Infrastructure for Fast Task-Parallel Code."  This evaluation supports
assessment of the functionality and reusability of the artifact and
validation of the results of the empirical evaluation, in Section 4
of the paper.

This artifact consists of a Docker image containing precompiled
binaries for OpenCilk as well as source code for all
benchmark programs used in the empirical evaluation of the paper.
Building OpenCilk from source is a time-consuming and
computing-resource-intensive process.  Therefore, we are providing
this Docker image with precompiled binaries to facilitate the
evaluation.  These binaries have been compiled for modern x86-64
processors.

The OpenCilk source code for this artifact, including its LLVM-based
compiler, runtime system, and productivity tools, is archived here:
<https://doi.org/10.5281/zenodo.7336106>.
For reference, a copy of the source code can also be found at
`/usr/local/src/opencilk` within the Docker image.

# Getting started guide

The following steps will guide you through setting up the Docker
image for the artifact evaluation and verifying that it runs as
intended on your system.

*Prerequisites:* These instructions assume you are using a modern
multicore x86-64 machine running a recent version of Linux that
has Docker installed.  In particular, the Docker image has been
tested on x86-64 machines running recent versions of Linux, such
as Ubuntu 22.04, and Docker version 20.10.21.  You can find
instructions on how to install the latest version of Docker at
<https://docs.docker.com/>. For example,
[here](https://docs.docker.com/engine/install/ubuntu/) are the
instructions to install Docker on Ubuntu.

1. Download the Docker image (2.4GB) from <https://people.csail.mit.edu/neboat/opencilk-ppopp-23/docker-opencilk-ppopp-23.tar.gz>:

```console
wget https://people.csail.mit.edu/neboat/opencilk-ppopp-23/docker-opencilk-ppopp-23.tar.gz
```

2. Load the Docker image:

```console
docker load -i docker-opencilk-ppopp-23.tar.gz
```

3. Run the Docker image:

```console
docker run -it opencilk-ppopp-23 /bin/bash
```

4. Enter the test directory inside the Docker container:

```console
cd /usr/local/src/ppopp-23-ae
```

5. Use the `run_tests.py` script with the `--quick-test` flag 
   to verify that the experiments run correctly on programs within
   the various benchmark suites:

```console
python3 ./run_tests.py --quick-test
```

The `run_tests.py` script will produce informational output 
about which test it is building and running as it executes.
The quick-test run takes approximately 5 minutes on a modern
Intel x86-64 system with 8 processor cores, such as an
[AWS c5.4xlarge instance](https://aws.amazon.com/ec2/instance-types/c5/).
If all steps complete successfully, then at the end of the
quick-test run, you should see something like the following
message:

```
Tests completed in 286.733336 seconds.  Run tag: small-20221118-0408.
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
  variety of Cilk programs using either the OpenMP, oneTBB, Cilk Plus
  or OpenCilk runtime systems.  OpenCilk also supports the use of tools,
  such as the Cilkscale scalability analyzer, to analyze task-parallel
  program execution.
- *Figure 3 performance trend:* Across the non-randomized benchmarks,
  the baseline performance of OpenCilk --- without pedigree and DPRNG
  support enabled and without any tool, such as Cilkscale, enabled ---
  is typically equal to or faster than that of Cilk Plus, OpenMP, and 
  oneTBB.  In particular, the parallel running times of these benchmarks
  is often better when using OpenCik.
- *Figure 4 performance trend:* Across the non-randomized benchmarks,
  OpenCik runs efficiently with pedigree and DPRNG support enabled,
  generally incurring low overheads compared to the OpenCilk's
  baseline performance and often outperforming Cilk Plus.
- *Figure 5 performance trend:* On the randomized benchmarks, OpenCilk
  supports efficient use of the DotMix deterministic parallel random-
  number generator (DPRNG), often matching or exceeding the performance
  of Cilk Plus using DotMix.  In addition, these benchmarks typically
  run faster when using OpenCilk's builtin DPRNG rather than DotMix.
- *Figure 6 performance trend:* On the non-randomized benchmarks, the
  bitcode-ABI version of Cilkscale typically runs faster than the
  library version of Cilkscale.

At a high level, you can replicate these results using the following
steps:
1. Run the `run_tests.py` script (with any necessary parameters):

```console
python3 ./run_tests.py
```

2. Copy the CSV files with aggregate results out of the Docker
   container, such as by running commands like the following outside of
   the Docker container, replacing `<tag>` with the run tag reported
   by `run_tests.py`:

```console
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/baseline-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/pedigrees-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/dprng-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/cilkscale-compare-<tag>.csv .
```

3. Examine the CSV files in the spreadsheet program of your choosing,
   such as Google Sheets or Microsoft Excel.

The following sections describe these high-level steps in detail.

## Running `run_tests.py`

You can run all of the benchmark programs for the experiments
described in the paper simply by running `run_tests.py` as follows:

```console
python3 ./run_tests.py
```

Running `run_tests.py` without any command-line arguments
will run all benchmark programs 10 times each and run the
parallel executables only on the number of CPU cores on the system
(excluding hyperthreads/SMT).  Although this default behavior does not
match the experimental setup used in the paper, it runs the
empirical tests more quickly in a manner that nonetheless supports
evaluation of the artifact.  Running `run_tests.py` with these default
parameters takes approximately 2.5 hours on a modern Intel x86-64
system with 8 processor cores and 32GB of RAM (specifically, an AWS
c5.4xlarge instance).

The `run_tests.py` script accepts a variety of options to run
the empirical evaluation in different configurations, in order
to accommodate different computer systems.  The following command
gives an overview of the options that `run_tests.py` accepts:

```console
python3 ./run_tests.py -h
```

Section 4 of the paper describes the system configuration and 
parameters used for the paper's empirical evaluation, including
the number of times each executable was run (20) and the numbers
of CPU processor cores each parallel executable was tested on
(1, 24, and 48).  If you have **ample time** --- several hours
--- **and computing resources** --- at least 48 CPU processor
cores --- you can use the `run_tests.py` script to run the tests
using these parameters as follows:

 ```console
 python3 ./run_tests.py -t 20 -c 1,24,48
 ```

There are several ways to run the application tests more quickly.

- Running `python3 ./run_tests.py` without any arguments
  will run the benchmark programs for all experiments more quickly.
  Compared to using the parameters from the paper, the final 
  performance results may exhibit more variability --- due to
  performing 10 runs per executable instead of 20 --- and it will
  not include 1-core running times for the parallel executables.
  However, such a run should still produce results that demonstrate
  the aforementioned performance trends.

- You can run the benchmark tests with **smaller inputs** by passing
  the `-s` flag to `run_tests.py`.

- You can specify **different CPU counts** to run the parallel
  executables on using the `-c` flag.  For example, on a system with
  24 CPU cores, the flag `-c 1,24` will run all parallel executables
  on 1 and 24 CPU cores.  The `run_tests.py` script will never run
  the executables on more CPU cores than are available on the system,
  regardless of the argument passed to the `-c` flag.

- You can use the `--programs` flag to select a **subset of
  programs** to run.  In particular, the GBBS benchmarks take a
  significant amount of time to compile, and some take substantial
  time to run, especially on 1 processor.  To run only the BFS and KCore
  benchmarks from GBBS, for example, pass
  `--programs BFS/NonDeterministicBFS:BFS_main,KCore/JulienneDBS17:KCore_main`
  to `run_tests.py`.

- You can specify the **number of trials** to run each executable
  using the `-t` flag.  For example, specifying `-t 5` will run each
  executable 5 times.  On a modern Intel x86-64 machine with 8 cores,
  running `run_tests.py` with `-t 5` and no other arguments takes
  approximately 1.5 hours.  Each running time in the final CSVs will be the
  median of the trials performed.  Please note that we do *not* recommend
  running the executables with too few trials, as doing so will
  increase the variability of the aggregated results.

## Getting the CSV files with aggregated results

When the `run_tests.py` script is run to perform all experiments, it 
will generate four CSV files containing aggregated performance results
for those experiments: `baseline-<tag>.csv`, `pedigrees-<tag>.csv`,
`dprng-<tag>.csv`, and `cilkscale-compare-<tag>.csv`.  In these CSV
filenames, `<tag>` denotes a ***run tag***, which identifies the run
by the year, month, day, hour, and minute of the invocation of
`run_tests.py`.  If small inputs are used, the run tag will also 
include the keyword `small`.  On completion, `run_tests.py`
reports the run tag for its run.

You can copy the CSV files produced by `run_tests.py` out of
the Docker container using the `docker cp` command.  For example,
running the following commands outside of the Docker container
--- replacing `<tag>` with the run tag --- will copy the four
CSV files with aggregated performance results out:

```console
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/baseline-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/pedigrees-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/dprng-<tag>.csv .
docker cp `docker ps -alq`:/usr/local/src/ppopp-23-ae/cilkscale-compare-<tag>.csv .
```

Note that `docker ps -alq` provides a convenient way to get the ID
of the latest container created.  If you are using other Docker
containers at the same time, use `docker ps` to find the container
ID corresponding with your run of the `opencilk-ppopp-23-ae` image,
then use that ID in place of `docker ps -alq` in the `docker cp`
commands above.

## Examining the CSV files

The generated CSV files correspond with the empirical evaluation
in the paper as follows:
- The `baseline-<tag>.csv` file contains running-time results for
  the baseline performance of the different systems.  These
  results correspond with Figure 3 in the paper.
- The `pedigrees-<tag>.csv` file contains running-time results for
  the performance of OpenCilk on the non-randomized benchmarks
  when pedigree and DPRNG support is enabled.  These results
  correspond with Figure 4 in the paper.
- The `dprng-<tag>.csv` file contains running-time results for
  the performance of OpenCilk and Cilk Plus on randomized
  benchmarks using different DPRNGs.  These results correspond
  with Figure 5 in the paper.
- The `cilkscale-compare-<tag>.csv` file contains running-time
  results on the non-randomized benchmarks of OpenCilk run with
  either the library-based or bitcode-ABI-based Cilkscale tool.
  These results correspond with Figure 6 in the paper.

In these CSV files, rows identify different programs, and columns
generally identify a system (e.g., Cilk Plus or OpenCilk) and
CPU count.  For example, the column heading `opencilk 8` 
indicates that the running times in that column were produced
by compiling and running the program using OpenCilk on 8 CPU
cores.  The column heading `serial 1` denotes executions on 1 CPU
core of the serial projection of the Cilk program, in which all Cilk
keywords are replaced with their serial C/C++ equivalents.  In the
`dprng-<tag>.csv` file, the column headings also identify the DPRNG
used.  In the `cilkscale-compare-<tag>.csv` file, the keywords
`cilkscale` and `cilkscale-bitcode` in the column headings indicate
that the programs were compiled and run with the library-based or
bitcode-ABI-based versions, respectively, of Cilkscale.

The running times reported in these CSVs are measured in seconds
and are aggregated as the median of the runs of that executable.

For reference, here are four CSV files generated from our own
run of `run_tests.py` on an 8-core Intel x86-64 machine (an AWS
c5.4xlarge instance running Ubuntu 22.04), where `20221117-1533`
is the run tag:

**An example `baseline-<tag>.csv` file:**
```
# cat baseline-20221117-1533.csv
benchmark,serial 1,cilkplus 8,opencilk 8
cholesky,2.5140000000000002,0.5435000000000001,0.444
cilksort,8.604,1.058,1.056
fft,6.3095,0.926,0.893
heat,5.9295,1.0725,1.0665
lu,10.748000000000001,1.375,1.357
matmul,5.51,0.735,0.7444999999999999
nqueens,2.838,0.3835,0.369
qsort,4.725,0.92,0.8605
rectmul,9.367,1.2080000000000002,1.1789999999999998
strassen,9.0515,1.3715000000000002,1.3695
BFS_main,0.6417925,0.0770275,0.077985
KCore_main,11.91,2.17189,2.047855
Triangle_main,140.7875,18.2574,18.1432
PageRank_main,95.18645000000001,10.785,9.884599999999999
minife,41.36465,18.32025,16.9011
```

**An example `pedigrees-<tag>.csv` file:**
```
# cat pedigrees-20221117-1533.csv
benchmark,opencilk 8
cholesky,0.4885
cilksort,1.0575
fft,0.9165000000000001
heat,1.0705
lu,1.3645
matmul,0.736
nqueens,0.373
qsort,0.902
rectmul,1.1844999999999999
strassen,1.362
BFS_main,0.079593
KCore_main,2.076575
Triangle_main,18.20395
PageRank_main,10.204215
minife,16.9366
```

**An example `dprng-<tag>.csv` file:**
```
# cat dprng-20221117-1533.csv
benchmark,cilkplus dotmix 8,opencilk builtin 8,opencilk dotmix 8
pi,1.971,0.5274985000000001,1.6766999999999999
fib_rng,2.4654100000000003,0.707068,2.52131
MaximalIndependentSet_main,0.5498185,0.540934,0.563748
SpanningForest_main,0.40091350000000003,0.4056925,0.406244
```

**An example `cilkscale-compare-<tag>.csv` file:**
```
# cat cilkscale-compare-20221117-1533.csv
benchmark,opencilk cilkscale 8,opencilk cilkscale-bitcode 8
cholesky,2.7885,2.567
cilksort,1.129,1.1155
fft,2.2300000000000004,2.1275
heat,1.086,1.081
lu,1.595,1.5705
matmul,0.7795000000000001,0.7685
nqueens,0.6935,0.6845000000000001
qsort,2.9705,2.7615
rectmul,1.529,1.493
strassen,1.3755,1.3775
BFS_main,0.087335,0.081406
KCore_main,2.4726850000000002,2.36709
Triangle_main,18.047150000000002,17.5631
PageRank_main,19.81455,18.81205
minife,17.30935,16.98815
```

# Additional information

This section describes additional features of the OpenCilk artifact
and the `run_tests.py` script, including information on how to use
OpenCilk manually and how to modify the `run_tests.py` script to run
additional tests.  While this information is not strictly needed to
replicate the empirical results, it may be of interest for reusing
the artifact.

## Verbose output of `run_tests.py`

The `run_tests.py` script will save, within the `rawdata`
subdirectory, the verbose output of building the benchmark programs
as well as the performance results of each run.  The build output
will be written to `rawdata/build-<tag>.out`, and raw
performance data will be written to CSV files within `rawdata`
named with the test suite, program, system, and run tag.

## Using OpenCilk directly

You can use the OpenCilk installation at `/opt/opencilk` within
the Docker image directly to compile and run a Cilk program.  To
compile and link a Cilk program, run the OpenCilk `clang` or
`clang++` binary within `/opt/opencilk/bin` --- for Cilk code
based on C or C++ code, respectively --- and pass it the
`-fopencilk` flag.  The `-fopencilk` flag should be used both
when compiling and linking.  For example, here is how you can
compile the `cholesky` benchmark in the Cilk-5 suite, on the
Docker image under `/usr/local/src/ppopp-23-ae/cilk5`:

```console
cd cilk5
/opt/opencilk/bin/clang -O3 -fopencilk -c cilk5/cholesky.c
/opt/opencilk/bin/clang -O3 -fopencilk -c cilk5/getoptions.c
/opt/opencilk/bin/clang -fopencilk cholesky.o getoptions.o -o cholesky
```

Once the executable is compiled and linked with the appropriate
flags, running the executable normally will automatically use
OpenCilk.

### Using OpenCilk with Cilk Plus, DPRNG support, or Cilkscale

You can also use the same OpenCilk binaries to compile Cilk
programs with the Cilk Plus runtime system or with different
extensions:
- To compile a Cilk program to use the Cilk Plus runtime system,
  pass `-fcilkplus` to the `clang` or `clang++` binary, instead of
  `-fopencilk`, when compiling and linking.  You will also need to
  pass `-I` and `-L` flags to the binary to identify the include
  and lib directories for the Cilk Plus installation, which is
  located at `/opt/cilkrts/` within the Docker image.
- To enable pedigree and DPRNG support within the OpenCilk runtime
  system, link the program with the additional `-lopencilk-pedigrees`
  flag (in addition to the `-fopencilk` flag).
- To use the library version of Cilkscale, compile and link the
  Cilk program with both `-fopencilk` and `-fcilktool=cilkscale`.
  To use the bitcode-ABI version of Cilkscale, when compiling the
  Cilk program, pass the additional flags
  `-mllvm -csi-tool-bitcode=/opt/opencilk/lib/clang/14.0.6/lib/x86_64-unknown-linux-gnu/libcilkscale.bc`.

You can find examples of all of these different uses of OpenCilk
in the raw build output from `run_tests.py`, at
`./rawdata/build-<tag>.out`.

## Generating an additional aggregate CSV file

Near the end of `run_tests.py` is commented-out code to generate a
CSV file, named `pedigrees-compare-<tag>.csv`, that compares the
performance if OpenCilk with pedigree and DPRNG support enabled
against the baseline performance of OpenCilk and Cilk Plus.  This
CSV combines the results in the `baseline-<tag>.csv` and
`pedigrees-<tag>.csv` files.  Although this CSV file does not
directly correspond with a figure in the paper, reviewers may find
this CSV file helpful to review, and should feel free to uncomment
this code to generate this CSV file.

## Adding more tests for `run_tests.py` to run

You can add a new application to an existing test suite by modifying
`run_tests.py` as follows.

- To run additional GBBS tests, add the GBBS test to either
  `all_gbbs_progs`, if the GBBS test is not randomized, or
  `all_rng_gbbs_progs`, if the test is randomized.  Note that, in
  these lists, the `//benchmarks` prefix on the benchmark name is
  elided.  See the [GBBS repository](https://github.com/ParAlg/gbbs/tree/3491d548a3584b6a8f2ce9f90f0dc674c6e58c48)
  for more information on the available GBBS tests.

- You can add a simple Cilk program to the test
  suite by adding the program to the `cilk5` directory and 
  updating the `Makefile` therein.  In particular, for a Cilk
  program that is implemented in a single source file, add the
  source code of that Cilk program to the `cilk5`
  subdirectory and add the name of the program to `ALL_TESTS`
  at the start of `cilk5/Makefile`.  (For more complicated Cilk
  programs, you will need to modify `cilk5/Makefile` appropriately
  to compile the program, using the standard variables `$(CC)`
  `$(CXX)`, `$(CFLAGS)` and `$(LDFLAGS)` to compile and link the
  program.)  Then, modify the `all_cilk5_progs` list at the start of
  `run_tests.py` to include the name of the new program.  Note that
  `run_tests.py` --- specifically, the `parse_cilk5_output` function
  --- expects to the program to report its running time as
  floating-point number alone on a line printed to stdout.

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
