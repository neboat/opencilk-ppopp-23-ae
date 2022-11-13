import argparse
import csv
import datetime
import logging
import os
import re
import subprocess
import statistics
import sys

from runner import run, get_cpu_ordering, get_n_cpus

logger = logging.getLogger(sys.argv[0])

opencilk_libdir = "/opt/opencilk/lib/clang/14.0.6/lib/x86_64-unknown-linux-gnu/"
top_dir = os.getcwd()
cilkrts_dir = "/opt/cilkrts"
compiler_bin_dir = "/opt/opencilk/bin/"
rawdata_dir = "./rawdata"

###########################################################################
### Test parameters

# The following test suites are supported:
# - 'cilk5' - The Cilk-5 benchmarks
# - 'minife' - The miniFE benchmark
# - 'gbbs' - Deterministic programs from the graph-based benchmark suite (GBBS)
# - 'random' - Assorted randomized Cilk programs
# - 'gbbs-random' - Randomized programs from GBBS
all_test_suites=['cilk5','minife','gbbs','random','gbbs-random']

# The following task-parallel systems are supported:
# - 'serial' - Compile and run the serial projection of the given Cilk code
# - 'opencilk' - Compile and run the Cilk code with OpenCilk
# - 'cilkplus' - Compile and run the Cilk code with Intel Cilk Plus
all_systems=['serial','opencilk','cilkplus']

# The following experiments are supported:
# - 'baseline' - Measure baseline performance of different systems.
# - 'pedigrees' - Measure performance of OpenCilk with pedigree support enabled.
# - 'cilkscale' - Measure performance of OpenCilk with the Cilkscale scalability analyzer.
# - 'cilkscale-bitcode' - Measure performance of OpenCilk with the bitcode-ABI version of Cilkscale.
# - 'dprng' - Measure performance of randomized Cilk programs using different DPRNGs.
all_experiments=['baseline','pedigrees','cilkscale','cilkscale-bitcode','dprng']

# The following options for deterministic parallel random-number generation (DPRNG) are supported:
# - 'dotmix' - Use the Intel Cilk Plus DotMix DPRNG library, which uses pedigrees.
# - 'builtin' - Use the OpenCilk runtime's built-in DPRNG.
all_dprngs = ["dotmix", "builtin"]

# The set of Cilk-5 benchmarks to run
all_cilk5_progs = ['cholesky', 'cilksort', 'fft', 'heat', 'lu', 'matmul', 'nqueens', 'qsort', 'rectmul', 'strassen']

# The set of deterministic GBBS benchmarks to run
all_gbbs_progs=['BFS/NonDeterministicBFS:BFS_main',
                'KCore/JulienneDBS17:KCore_main',
                'TriangleCounting/ShunTangwongsan15:Triangle_main',
                'PageRank:PageRank_main']

# The set of assorted randomized Cilk programs to run
all_randbench_progs=['pi','fib_rng']

# The set of randomized GBBS benchmarks to run
all_rng_gbbs_progs = ["MaximalIndependentSet/RandomGreedy:MaximalIndependentSet_main",
                      "SpanningForest/SDB14:SpanningForest_main"]

###########################################################################
### Utility methods

# Run a given command as a subprocess and wait for it to complete.
def runcmd(subProcCommand):
    logger.info(subProcCommand)
    proc = subprocess.Popen([subProcCommand], shell=True)
    proc.wait()

###########################################################################
### Methods for configuring different builds

### Methods for configuring Makefile build systems

# Get Makefile flag to select a particular system
def make_sysflag(sys):
    match sys:
        case "opencilk": return ""
        case "cilkplus": return "CILKPLUS=1"
        case "serial": return "SERIAL=1"
        case _: raise ValueError("Unrecognized system "+sys)

# Get extra Makefile CFLAGS to enable Cilkscale
def make_cilkscale_cflags(use_bitcode):
    cflags = "-fcilktool=cilkscale"
    if use_bitcode:
        cflags += " -mllvm -csi-tool-bitcode="+opencilk_libdir+"libcilkscale.bc"
    return cflags

# Get extra Makefile LDFLAGS to enable Cilkscale
def make_cilkscale_ldflags(use_bitcode):
    return "-fcilktool=cilkscale"

# Get extra Makefile CFLAGS to enable OpenCilk pedigree support
def make_pedigrees_cflags():
    return ""

# Get extra Makefile LDFLAGS to enable OpenCilk pedigree support
def make_pedigrees_ldflags():
    return "-lopencilk-pedigrees"

# Set environment variables for a given experiment
def set_environ_for_experiment(exp):
    if exp == "pedigrees":
        os.environ['EXTRA_LDLIBS'] = make_pedigrees_ldflags()
    elif exp == "cilkscale":
        os.environ['EXTRA_CFLAGS'] = make_cilkscale_cflags(False)
        os.environ['EXTRA_LDFLAGS'] = make_cilkscale_ldflags(False)
    elif exp == "cilkscale-bitcode":
        os.environ['EXTRA_CFLAGS'] = make_cilkscale_cflags(True)
        os.environ['EXTRA_LDFLAGS'] = make_cilkscale_ldflags(True)

# Unset environment variables for a given experiment
def unset_environ_for_experiment(exp):
    if exp == "pedigrees":
        del os.environ['EXTRA_LDLIBS']
    elif exp == "cilkscale" or exp == "cilkscale-bitcode":
        del os.environ['EXTRA_CFLAGS']
        del os.environ['EXTRA_LDFLAGS']

# Adjust CPU counts for a given system.  Currently, this method simply
# sets cpu_counts to "1" for the serial system.
def fix_cpu_counts(sys, cpu_counts):
    if sys.startswith("serial"):
        return "1"
    return cpu_counts

# Returns True if the given system-experiment pair is valid to test,
# False otherwise.
def sys_exp_compatible(sys, exp):
    if sys == "serial" and exp != "baseline":
        return False
    if sys != "opencilk":
        if exp == "pedigrees" or exp == "cilkscale" or exp == "cilkscale-bitcode":
            return False
    return True

# Returns True if the given system-dprng pair is valid to test, False
# otherwise.
def sys_dprng_compatible(sys, dprng):
    if sys == "serial":
        return False
    if dprng == "builtin" and sys != "opencilk":
        return False
    return True


### Methods to get configuration for Bazel build system

# Configure bazel to build for the given system.  Returns a "--config"
# string to pass to bazel, and also sets one or more environment
# variables.
def set_bazel_sysconfig(sys):
    os.environ['CC'] = os.path.join(compiler_bin_dir,"clang++")
    match sys:
        case "opencilk": return "--config=cilk"
        case "cilkplus":
            os.environ['CPLUS_INCLUDE_PATH'] = os.path.join(cilkrts_dir,"include")
            return "--config=cilkplus"
        case "serial": return "--config=serial"
        case _: raise ValueError("Unrecognized system "+sys)

# Undo configuration for bazel to build for a particular system.
# Unsets environment variables set by set_bazel_sysconfig().
def unset_bazel_sysconfig(sys):
    del os.environ['CC']
    match sys:
        case "cilkplus": del os.environ['CPLUS_INCLUDE_PATH']
        case _: return

# Get bazel config string to build with Cilkscale.
def get_bazel_cilkscale_config(use_bitcode):
    if use_bitcode:
        return "--config=cilkscale --config=cilkscale_bitcode"
    return "--config=cilkscale"

# Get bazel config string to enable OpenCilk pedigree support.
def get_bazel_pedigree_config(sys):
    match sys:
        case "opencilk":
            return "--config=dotmix_opencilk"
        case _:
            return ""

# Get bazel config string to use a particular DPRNG.
def get_bazel_dprng_config(dprng, sys):
    config = ""
    match dprng:
        case "dotmix":
            config = "--config=dotmix"
            if sys == "opencilk":
                config += " " + get_bazel_pedigree_config(sys)
            return config
        case "builtin":
            if sys != "opencilk":
                raise ValueError("Cannot use builtin without opencilk")
            return "--config=dprand"
        case _:
            raise ValueError("Unrecognized dprng "+dprng)

###########################################################################
### Methods for accumulating results into CSVs

# Read raw data from out_csv, aggregate the performance measurements,
# add the aggregated results to accum_data, and update sys_run
# accordingly.
#
# The parse_bench_name_fn argument allows for parsing of the program
# names in out_csv, i.e., in case we wish to separate rows of out_csv
# into different columns (i.e., "systems").  This parameter is used,
# for example, for handling the results of the randomized Cilk
# benchmarks, where each run of the benchmark tests different DPRNGs.
def accumulate_results(out_csv, bench, sys, sys_run, accum_data, parse_bench_name_fn=None):
    with open(out_csv, "r") as out_csv_file:
        # Read the rows of the CSV.
        rows = csv.reader(out_csv_file, delimiter=",")
        for row in rows:
            # Determine the name of the system tested, possibly by
            # parsing the benchmark name in the row.
            sysname = sys
            if parse_bench_name_fn is not None:
                parsed_bench = parse_bench_name_fn(row[0])
                sysname = sys+' '+parsed_bench[1]
            # Get the number of CPUs used.
            num_cpus = row[1]
            # Compute the median of the timing measurements.
            median = statistics.median([float(x) for x in row[2:]])
            # Add the system name and aggregated timing measurement to
            # sys_run and accum_data, respectively.
            if sysname not in sys_run:
                sys_run.append(sysname)
            key = (bench, sysname, num_cpus)
            accum_data[key] = median

# Write the accumulated performance results to a CSV file named
# accum_csv.
def write_accumulated_results(accum_csv, accum_data, prog_run, sys_run, cpu_counts):
    with open(accum_csv, "w") as accum_csv_file:
        # Create a CSV writer.
        accum_csv_writer = csv.writer(accum_csv_file, delimiter=',')
        # Generate a header for the output CSV.
        header = ["benchmark"]+[s+' '+c for s in sys_run for c in fix_cpu_counts(s, cpu_counts).split(',')]
        accum_csv_writer.writerow(header)
        # Iterate over the programs run, which will form the rows of
        # the output CSV.
        for prog in prog_run:
            out_row = [prog]
            # Iterate over the systems run and CPU counts, which will
            # form the columns of the output CSV.
            for s in sys_run:
                for c in fix_cpu_counts(s, cpu_counts).split(','):
                    # Add data to the output row, if we have it.
                    if (prog,s,c) in accum_data:
                        out_row.append(accum_data[(prog,s,c)])
                    else:
                        out_row.append('')
            # Write the row to the CSV.
            accum_csv_writer.writerow(out_row)

# Helper method to combine results of different experiments in
# accum_data.  This method assumes that the same systems and programs
# were run for the experiments to combine.  The combined results will
# be keyed in accum_data, prog_run, and sys_run under new_key.  The
# keys parameter specifies the list of keys to combine.
#
# This method is currently used to combine the results of the
# cilkscale and cilkscale-bitcode experiments.
def combine_keys(accum_data, new_key, keys, prog_run, sys_run, cpu_counts):
    accum_data[new_key] = dict()
    sys_run[new_key] = []
    prog_run[new_key] = []
    # Iterate over the keys (e.g., experiments) to combine.
    for key in keys:
        # Iterate over the systems run for that key.
        for sys in sys_run[key]:
            # Create a new system name by combining the old system
            # name with the old key.
            new_sys = sys+' '+key
            if new_sys not in sys_run[new_key]:
                sys_run[new_key].append(new_sys)

            # Iterate over the programs run for that key and the CPU
            # counts used.
            for prog in prog_run[key]:
                if prog not in prog_run[new_key]:
                    prog_run[new_key].append(prog)

                for c in fix_cpu_counts(sys, cpu_counts).split(','):
                    # Copy data from the old key to the new key.
                    if (prog, sys, c) in accum_data[key]:
                        accum_data[new_key][(prog, new_sys, c)] = accum_data[key][(prog, sys, c)]
                    else:
                        accum_data[new_key][(prog, new_sys, c)] = ''

###########################################################################
## Cilk-5 benchmark handling (cilk5 subdirectory)

# Output parser for Cilk-5 benchmarks.  Extracts running time in
# seconds from output.
def parse_cilk5_output(output, err, prog, prog_args, timings):
    for line in output.split('\n'):
        m = re.match(r"(\d+\.\d+)", line.lower())
        if m:
            key = prog + " " + " ".join(prog_args)
            val = m.group(1)
            if key not in timings:
                timings[key] = []
            timings[key].append(val)

# Get program inputs for the specified Cilk-5 benchmark.
def get_cilk5_input(prog, small_inputs):
    if small_inputs:
        match prog:
            case "cholesky": return ["-n","2000","-z","4000"]
            case "fft": return ["-n","2000000"]
            case "heat": return ["-nx","2048","-ny","2048","-nt","100"]
            case "lu": return ["-n","2048"]
            case "matmul": return ["-n","1024"]
            case "nqueens": return ["11"]
            case "qsort": return ["5000000"]
            case "rectmul": return ["-x","2048","-y","2048","-z","1024"]
            case "strassen": return ["-n","2048"]
            case "cilksort": return ["-n","10000000"]
            case _: raise ValueError("Unrecognized program "+prog)

    match prog:
        case "cholesky": return ["-n","4000","-z","8000"]
        case "fft": return ["-n","20000000"]
        case "heat": return ["-nx","4096","-ny","4096","-nt","200"]
        case "lu": return ["-n","4096"]
        case "matmul": return ["-n","2048"]
        case "nqueens": return ["13"]
        case "qsort": return ["50000000"]
        case "rectmul": return ["-x","4096","-y","4096","-z","2048"]
        case "strassen": return ["-n","4096"]
        case "cilksort": return ["-n","80000000"]
        case _: raise ValueError("Unrecognized program "+prog)

# Build the Cilk-5 benchmark suite for the given system and experiment.
def build_cilk5(sys, exp):
    set_environ_for_experiment(exp)

    subProcCommand = "make -C cilk5 clean; make -C cilk5 CC="+os.path.join(compiler_bin_dir,"clang")+" CXX="+os.path.join(compiler_bin_dir,"clang++")+" -B "+make_sysflag(sys)
    runcmd(subProcCommand)

    unset_environ_for_experiment(exp)

# Run the Cilk-5 tests for all specified systems, experiments, and
# programs, with the given configuration options.
def run_cilk5_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                    accum_data, all_prog_run, all_sys_run, programs=all_cilk5_progs):
    for exp in experiments:
        # The Cilk-5 tests are not used for the DPRNG experiment.
        if exp == 'dprng':
            continue

        # Dictionary to store the results of this experiment.
        exp_data = dict()

        # Iterate over the systems to run.
        for sys in systems:
            if not sys_exp_compatible(sys, exp):
                continue

            # Build the tests
            build_cilk5(sys, exp)

            # Iterate over the programs to run.
            for prog in programs:
                if prog not in all_cilk5_progs:
                    continue
                out_csv = os.path.join(rawdata_dir,
                                       '-'.join(["cilk5",prog,sys,exp,csv_tag])+".csv")
                # Run the program and output results into out_csv
                run(os.path.join("./cilk5/",prog), get_cilk5_input(prog, small_inputs),
                    parse_cilk5_output, trials, fix_cpu_counts(sys, cpu_counts),
                    out_csv)

                # Record that this program was run for this experiment.
                if exp not in all_prog_run:
                    all_prog_run[exp] = []
                if prog not in all_prog_run[exp]:
                    all_prog_run[exp].append(prog)

                # Aggregate the results in out_csv.
                if exp not in all_sys_run:
                    all_sys_run[exp] = []
                accumulate_results(out_csv, prog, sys, all_sys_run[exp], exp_data)

        if not exp_data:
            continue

        # Add the results of this experiment to accum_data.
        if exp not in accum_data:
            accum_data[exp] = dict()
        accum_data[exp] |= exp_data

###########################################################################
## MiniFE benchmark handling (minife subdirectory)

minife_dir = "miniFE/src"

# MiniFE output parser.  Extracts running time in seconds from output.
def parse_minife_output(output, err, prog, prog_args, timings):
    for line in output.split('\n'):
        m = re.match(r"Total Program Time (\d+\.\d+)", line)
        if m:
            key = prog + " " + " ".join(prog_args)
            val = m.group(1)
            if key not in timings:
                timings[key] = []
            timings[key].append(val)

# Get program inputs for the miniFE benchmark.
def get_minife_input(small_inputs):
    if small_inputs:
        return ["--nx","100","--ny","100","--nz","100"]
    return ["--nx","150","--ny","150","--nz","150"]

# Build the miniFE test for the given system and experiment.
def build_minife(sys, exp):
    set_environ_for_experiment(exp)
    os.environ['CC'] = os.path.join(compiler_bin_dir,"clang")
    os.environ['CXX'] = os.path.join(compiler_bin_dir,"clang++")
    os.environ['OMPI_MPICXX'] = os.environ['CXX']

    subProcCommand = "make -C "+minife_dir+" clean; make -C "+minife_dir+" "+make_sysflag(sys)
    runcmd(subProcCommand)

    del os.environ['OMPI_MPICXX']
    del os.environ['CXX']
    del os.environ['CC']
    unset_environ_for_experiment(exp)

# Run the miniFE test for all specified systems, experiments, and
# programs, with the given configuration options.
def run_minife_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                     accum_data, all_prog_run, all_sys_run):
    for exp in experiments:
        # The miniFE test is not used for the DPRNG experiment.
        if exp == 'dprng':
            continue

        exp_data = dict()

        # Iterate over the systems to run.
        for sys in systems:
            if not sys_exp_compatible(sys, exp):
                continue
            # Build the test
            build_minife(sys, exp)
            out_csv = os.path.join(rawdata_dir,
                                   "minife-"+'-'.join([sys,exp,csv_tag])+".csv")
            # Run the test and output the results into out_csv
            run(os.path.join(minife_dir,"miniFE.x"), get_minife_input(small_inputs),
                parse_minife_output, trials, fix_cpu_counts(sys, cpu_counts),
                out_csv)

            # Aggregate the results in out_csv.
            if exp not in all_sys_run:
                all_sys_run[exp] = []
            accumulate_results(out_csv, 'minife', sys, all_sys_run[exp], exp_data)

        if not exp_data:
            continue

        # Record that this program was run for this experiment.
        if exp not in all_prog_run:
            all_prog_run[exp] = []
        if 'minife' not in all_prog_run[exp]:
            all_prog_run[exp].append('minife')

        # Add the results of this experiment to accum_data.
        if exp not in accum_data:
            accum_data[exp] = dict()
        accum_data[exp] |= exp_data

###########################################################################
## GBBS benchmark handling (gbbs subdirectory)

# Get program inputs for the specified GBBS benchmark.
#
# This method takes the number of trials, because we use the "-rounds"
# argument to the binary run multiple trials on the same graph
# efficiently.
def get_gbbs_input(prog, trials, small_inputs):
    if small_inputs:
        return ["-rounds",trials,"-c","-m","-s","-src","10","./gbbs/inputs/soc-LiveJournal1.bin"]
    return ["-rounds",trials,"-c","-m","-s","-src","10","./gbbs/inputs/com-orkut.bin"]

# Parse the short test name from the given GBBS benchmark name.
def get_test_name_from_prog(prog):
    return prog[(prog.find(':')+1):]

# Parse the executable name from the given GBBS benchmark name.
def get_exe_for_prog(prog):
    return re.sub(':','/',prog)

# GBBS output parser.  Extracts the application name, graph name, and
# running time in seconds from output.
def parse_gbbs_output(output, err, prog, prog_args, timings):
    for line in output.split('\n'):
        # Try to get the application name
        m = re.match(r"### Application: ([^\s]+)", line)
        if m:
            app = m.group(1)
            continue

        # Try to get the graph name
        m = re.match(r"### Graph: ([^\s]+)", line)
        if m:
            graph = m.group(1)
            continue

        # Try to get the running time
        m = re.match(r"### Running Time: (\d+\.\d+)", line)
        if m:
            val = m.group(1)
            key = app + " " + graph
            if key not in timings:
                timings[key] = []
            timings[key].append(val)

# Build the specified GBBS benchmark for the given system and experiment
# or DPRNG.
def build_gbbs(sys, exp, dprng, prog):
    config = set_bazel_sysconfig(sys)
    if exp == "cilkscale":
        config += " "+get_bazel_cilkscale_config(False)
    elif exp == "cilkscale-bitcode":
        config += " "+get_bazel_cilkscale_config(True)
    elif exp == "pedigrees":
        config += " "+get_bazel_pedigree_config(sys)

    if dprng != "":
        config += " "+get_bazel_dprng_config(dprng, sys)

    os.chdir(os.path.join(top_dir,"gbbs"))

    subProcCommand = "bazel run "+config+" //benchmarks/"+prog
    runcmd(subProcCommand)

    os.chdir(top_dir)

    unset_bazel_sysconfig(sys)

# Run the deterministic GBBS benchmarks for all specified systems and
# experiments, with the given configuration options.
def run_gbbs_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                   accum_data, all_prog_run, all_sys_run, programs=all_gbbs_progs):
    for exp in experiments:
        # The non-randomized GBBS tests are not used for the DPRNG
        # experiment.
        if exp == 'dprng':
            continue

        exp_data = dict()

        # Iterate over the systems to run.
        for sys in systems:
            if not sys_exp_compatible(sys, exp):
                continue

            # Iterate over the programs to run.
            for prog in programs:
                if prog not in all_gbbs_progs:
                    continue

                test = get_test_name_from_prog(prog)
                # Combine the program.
                build_gbbs(sys, exp, "", prog)
                out_csv = os.path.join(rawdata_dir,
                                       '-'.join(["gbbs",test,sys,exp,csv_tag])+".csv")
                # Run the program and output the results into out_csv.
                run(os.path.join("./gbbs/bazel-bin/benchmarks/",get_exe_for_prog(prog)),
                    get_gbbs_input(prog, trials, small_inputs), parse_gbbs_output,
                    "1", fix_cpu_counts(sys, cpu_counts), out_csv)

                # Record that this program was run for this experiment.
                if exp not in all_prog_run:
                    all_prog_run[exp] = []
                if test not in all_prog_run[exp]:
                    all_prog_run[exp].append(test)

                # Aggregate the results in out_csv.
                if exp not in all_sys_run:
                    all_sys_run[exp] = []
                accumulate_results(out_csv, test, sys, all_sys_run[exp], exp_data)

        if not exp_data:
            continue

        # Add the results of this experiment to accum_data.
        if exp not in accum_data:
            accum_data[exp] = dict()
        accum_data[exp] |= exp_data

###########################################################################
## Randomized Cilk benchmark handling (random subdirectory)

# Output parser for assorted randomized Cilk programs.  Extracts
# running time in seconds from output.
def parse_randbench_output(output, err, prog, prog_args, timings):
    for line in output.split('\n'):
        m = re.match(r"([^\s]+).*,\D+time\D+(\d+\.\d+)", line.lower())
        if m:
            key = m.group(1)
            val = m.group(2)
            if key not in timings:
                timings[key] = []
            timings[key].append(val)

# Get program inputs for the specified randomized Cilk benchmark.
#
# This method takes the number of trials, because we let the
# executable itself run multiple trials efficiently.
def get_randbench_input(prog, trials, small_inputs):
    if small_inputs:
        match prog:
            case "pi": return ["10000000",trials]
            case "fib_rng": return ["35",trials]
            case _: raise ValueError("Unrecognized program "+prog)
    match prog:
        case "pi": return ["100000000",trials]
        case "fib_rng": return ["40",trials]
        case _: raise ValueError("Unrecognized program "+prog)

# Build the randomized Cilk programs for the given system.  These
# programs are hard-coded to test different DPRNGs.
def build_randbench(sys):
    subProcCommand = "make -C random clean; make -C random CC="+os.path.join(compiler_bin_dir,"clang")+" CXX="+os.path.join(compiler_bin_dir,"clang++")+" -B "+make_sysflag(sys)
    runcmd(subProcCommand)

def parse_randbench_name(prog):
    m = re.match(r"([a-zA-Z0-9]+)_([a-zA-Z0-9]+)", prog)
    if m.group(2) == "pedigree":
        return (m.group(1),"dotmix")
    elif m.group(2) == "dprand":
        return (m.group(1),"builtin")
    else:
        raise ValueError("Failed to parse benchmark name: "+prog)

# Run the randomized Cilk programs on all systems, with the given
# configuration options.
def run_randbench_tests(systems, small_inputs, trials, cpu_counts, csv_tag,
                        accum_data, prog_run, sys_run, programs=all_randbench_progs):
    # Iterate over the systems to run.
    for sys in systems:
        if sys == "serial":
            continue
        # Build the tests
        build_randbench(sys)

        # Iterate over the programs to run.
        for prog in programs:
            if prog not in all_randbench_progs:
                continue
            out_csv = os.path.join(rawdata_dir,
                                   '-'.join(["random",prog,sys,csv_tag])+".csv")
            # Run the program and output results into out_csv
            run(os.path.join("./random/",prog), get_randbench_input(prog, trials, small_inputs),
                parse_randbench_output, "1", fix_cpu_counts(sys, cpu_counts),
                out_csv)

            # Record taht this program was run for this experiment.
            if prog not in prog_run:
                prog_run.append(prog)

            # Aggregate the results in out_csv.
            accumulate_results(out_csv, prog, sys, sys_run, accum_data, parse_randbench_name)

## Randomized GBBS benchmark handling (gbbs subdirectory)

# Run the randomized GBBS benchmarks and all specified systems and
# DPRNGs, with the given configuration options.
def run_rng_gbbs_tests(systems, dprngs, small_inputs, trials, cpu_counts, csv_tag,
                       accum_data, prog_run, sys_run, programs = all_rng_gbbs_progs):
    # Iterate over the systems to run.
    for sys in systems:
        # Iterate over the DPRNGs to use.
        for dprng in dprngs:
            if not sys_dprng_compatible(sys, dprng):
                continue
            # Iterate over the programs to run.
            for prog in programs:
                if prog not in all_rng_gbbs_progs:
                    continue
                test = get_test_name_from_prog(prog)
                # Build the test.
                build_gbbs(sys, "", dprng, prog)
                out_csv = os.path.join(rawdata_dir,
                                       '-'.join(["gbbs","random",test,sys,dprng,csv_tag])+".csv")
                # Run the program and output results into out_csv
                run(os.path.join("./gbbs/bazel-bin/benchmarks/",get_exe_for_prog(prog)),
                    get_gbbs_input(prog, trials, small_inputs), parse_gbbs_output,
                    "1", fix_cpu_counts(sys, cpu_counts), out_csv)

                # Record that this program was run for this experiment.
                if test not in prog_run:
                    prog_run.append(test)

                # Aggregate the results in out_csv.
                accumulate_results(out_csv, test, sys+" "+dprng, sys_run, accum_data)

###########################################################################

# Main routine.  Parse command-line arguments and run specified tests.
def main():
    # Setup and parse script arguments.
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-suites", "-u",
                    help="Comma-separated list of test suites to run.  (default: "+','.join(all_test_suites)+")",
                    default=','.join(all_test_suites))
    ap.add_argument("--programs",
                    help="comma-separated list of programs to run.  Programs must be within the test-suites to run.  The miniFE test suite ignores this option.")
    ap.add_argument("--systems", "-y",
                    help="Comma-separated list of systems to test.  (default: "+','.join(all_systems)+")",
                    default=','.join(all_systems))
    ap.add_argument("--experiments", "-x",
                    help="Comma-separated list of experiments to run.  (default: "+','.join(all_experiments)+")",
                    default=','.join(all_experiments))
    ap.add_argument("--small", "-s", help="Run tests with small inputs.", default=False,
                    action=argparse.BooleanOptionalAction)
    ap.add_argument("--cpu-counts", "-c",
                    help="Comma-separated list of cpu counts to use.  (default: "+str(get_n_cpus())+")",
                    default=str(get_n_cpus()))
    ap.add_argument("--trials", "-t", help="Number of trials to run.  (default: 1)", default="1")

    args = ap.parse_args()
    # print(args)

    # The list of test suites to run.
    test_suites = args.test_suites.split(',')
    # The list of systems to use.
    systems = args.systems.split(',')
    # The list of experiment to perform.
    experiments = args.experiments.split(',')
    # Whether or not to use small inputs.
    small_inputs = args.small
    # The list of CPU counts to use.  The runner will parse the CPU
    # architecture on the system to preferentially use CPUs on the
    # same socket(s) and to avoid using hyperthreads.
    cpu_counts = args.cpu_counts
    # Number of times to run each executable.  Each data point will be
    # aggregated as the median of this many runs.
    trials = args.trials
    # If the user provides a list of programs, use that list to
    # down-select the programs to run within the test suites.
    programs = None
    if args.programs is not None:
        programs = args.programs.split(',')
    # Tag all CSVs generated with the year, month, day, hour, and
    # minute when this script is invoked.
    csv_tag = datetime.datetime.now().strftime("%Y%m%d-%H%M")

    logging.basicConfig(level=logging.INFO)

    # Ensure there is a directory for raw data.
    if not os.path.exists(rawdata_dir):
        os.mkdir(rawdata_dir)

    # All aggregated performance results will be placed into this
    # dictionary, indexed by experiment.  Each experiment maps to a
    # dictionary mapping (program, system, cpu-count) to aggregate
    # running time.
    accum_data = dict()
    # This dictionary maps each experiment to a list of programs run
    # as part of that experiment.
    all_prog_run = dict()
    # This dictionary maps each experiment to a list of systems run as
    # part of that experiment.
    all_sys_run = dict()

    # Iterate over the test suites.
    for test_suite in test_suites:
        if test_suite == 'cilk5':
            # Run the Cilk-5 benchmarks for all experiments.
            if programs is not None:
                run_cilk5_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                                accum_data, all_prog_run, all_sys_run, programs)
            else:
                run_cilk5_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                                accum_data, all_prog_run, all_sys_run)
        elif test_suite == 'minife':
            # Run the miniFE benchmark for all experiments.
            run_minife_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                             accum_data, all_prog_run, all_sys_run)
        elif test_suite == 'gbbs':
            # Run the non-randomized GBBS benchmarks for all experiments.
            if programs is not None:
                run_gbbs_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                               accum_data, all_prog_run, all_sys_run, programs)
            else:
                run_gbbs_tests(systems, experiments, small_inputs, trials, cpu_counts, csv_tag,
                               accum_data, all_prog_run, all_sys_run)
        elif test_suite == 'random':
            # The ramdom suite only applies to the DPRNG experiment.
            if 'dprng' not in experiments:
                continue

            # If necessary, initialize the appropriate entries in
            # accum_data, all_prog_run, and all_sys_run.
            if 'dprng' not in accum_data:
                accum_data['dprng'] = dict()
                all_prog_run['dprng'] = []
                all_sys_run['dprng'] = []

            # Run the assorted randomized benchmarks.
            if programs is not None:
                run_randbench_tests(systems, small_inputs, trials, cpu_counts, csv_tag,
                                    accum_data['dprng'], all_prog_run['dprng'],
                                    all_sys_run['dprng'], programs)
            else:
                run_randbench_tests(systems, small_inputs, trials, cpu_counts, csv_tag,
                                    accum_data['dprng'], all_prog_run['dprng'],
                                    all_sys_run['dprng'])
        elif test_suite == 'gbbs-random':
            # This gbbs-random suite only applies to the DPRNG experiment.
            if 'dprng' not in experiments:
                continue

            # If necessary, initialize the appropriate entries in
            # accum_data, all_prog_run, and all_sys_run.
            if 'dprng' not in accum_data:
                accum_data['dprng'] = dict()
                all_prog_run['dprng'] = []
                all_sys_run['dprng'] = []

            # Run the randomized GBBS benchmarks.
            if programs is not None:
                run_rng_gbbs_tests(systems, all_dprngs, small_inputs, trials, cpu_counts,
                                   csv_tag, accum_data['dprng'], all_prog_run['dprng'],
                                    all_sys_run['dprng'], programs)
            else:
                run_rng_gbbs_tests(systems, all_dprngs, small_inputs, trials, cpu_counts,
                                   csv_tag, accum_data['dprng'], all_prog_run['dprng'],
                                    all_sys_run['dprng'])

    # print(accum_data)
    # print(all_prog_run)
    # print(all_sys_run)

    have_all_cilkscale_results = \
        'cilkscale' in experiments and \
        'cilkscale-bitcode' in experiments and \
        'cilkscale' in accum_data and accum_data['cilkscale'] and \
        'cilkscale-bitcode' in accum_data and accum_data['cilkscale-bitcode']
    for exp in experiments:
        # We will separately combine the results of the Cilkscale
        # experiments, so don't generate CSVs of their results here.
        if have_all_cilkscale_results and (exp == 'cilkscale' or exp == 'cilkscale-bitcode'):
            continue

        # Write a CSV of the experiment's results.
        if exp in accum_data and accum_data[exp]:
            accum_csv = '-'.join([exp,csv_tag])+".csv"
            write_accumulated_results(accum_csv, accum_data[exp], all_prog_run[exp],
                                      all_sys_run[exp], cpu_counts)

    # Collect the results of the cilkscale and cilkscale-bitcode
    # experiments to generate a single CSV for comparing their results.
    if have_all_cilkscale_results:
        # Combine the results of the cilkscale and cilkscale-bitcode experiments.
        combined_key = 'cilkscale-compare'
        combine_keys(accum_data, combined_key, ['cilkscale','cilkscale-bitcode'],
                     all_prog_run, all_sys_run, cpu_counts)
        # Write these combined results to a single CSV.
        accum_csv = '-'.join([combined_key,csv_tag])+".csv"
        write_accumulated_results(accum_csv, accum_data[combined_key],
                                  all_prog_run[combined_key], all_sys_run[combined_key],
                                  cpu_counts)

    # Uncomment the following to generate an additional CSV comparing
    # the baseline runtime performance and the performance of OpenCilk
    # with pedigrees enabled.  This CSV was _not_ included as its own
    # figure in the paper.

    # have_baseline_and_pedigress = \
    #     'baseline' in experiments and \
    #     'pedigrees' in experiments and \
    #     'baseline' in accum_data and accum_data['baseline'] and \
    #     'pedigrees' in accum_data and accum_data['pedigrees']
    # if have_baseline_and_pedigress:
    #     # Combine the results of the baseline and pedigrees experiments.
    #     combined_key = 'pedigrees-compare'
    #     combine_keys(accum_data, combined_key, ['baseline','pedigrees'],
    #                  all_prog_run, all_sys_run, cpu_counts)
    #     # Write these combined results to a single CSV.
    #     accum_csv = '-'.join([combined_key,csv_tag])+".csv"
    #     write_accumulated_results(accum_csv, accum_data[combined_key],
    #                               all_prog_run[combined_key], all_sys_run[combined_key],
    #                               cpu_counts)

    return 0

if __name__ == '__main__':
    main()
