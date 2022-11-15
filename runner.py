###########################################################################
### runner.py: Script for repeatedly running an application binary on
### different numbers of processors and collecting performance
### measurements.
###
### Use the run() function to run a particular program binary for a
### specified number of trials and on different CPU counts.  Raw
### performance results will be written to a CSV file.
###########################################################################

import argparse
import csv
import datetime
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

################################################################################
## Utility methods

# Print captured stdout and stderr.
def print_stdout_stderr(out, err, prog, prog_args):
    print()
    print(">> STDOUT (" + prog + " " + " ".join(prog_args) + ")")
    print(str(out,"utf-8"), file=sys.stdout, end='')
    print("<< END STDOUT")
    print()
    print(">> STDERR (" + prog + " " + " ".join(prog_args) + ")")
    print(str(err,"utf-8"), file=sys.stderr, end='')
    print("<< END STDERR")
    print()
    return

# Get the number of CPUs on the system.  Excludes hyperthreads if it
# can parse the CPU configuration of the system.
def get_n_cpus():
    return len(get_cpu_ordering())

# Run the given command as a subprocess.
def run_command(cmd, asyn = False):
    proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if not asyn:
        out,err=proc.communicate()
        return out,err
    else:
        return ""

# Run the command `rcommand` for `trials` times on `P` CPUs.  Uses
# taskset to restrict process to a given list of CPU IDs, if possible.
# In particular, Darwin does not support taskset.
def run_on_p_workers(P, trials, rcommand):
    cpu_ordering = get_cpu_ordering()
    cpu_online = cpu_ordering[:P]

    # time.sleep(0.1)
    if sys.platform != "darwin":
        rcommand = "taskset -c " + ",".join([str(p) for (p,m) in
                                             cpu_online]) + " " + rcommand

    logger.info(rcommand)
    output = ""
    errout = ""
    for t in range(1, int(trials)+1):
        proc = subprocess.Popen([rcommand], shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out,err=proc.communicate()
        output = output + str(out, "utf-8")
        errout = errout + str(err, "utf-8")
    return output,errout

# Attempt to parse the CPU configuration of the system and return a
# list of CPU IDs that:
# 1) excludes hyperthreads, and
# 2) groups CPU IDs on the same socket consecutively.
#
# Parsing the CPU configuration is best-effort.  If it cannot parse
# the CPU configuration, then simply returns a list of P CPU IDs.
def get_cpu_ordering():
    if sys.platform == "darwin":
        # TODO: Replace with something that analyzes CPU configuration on Darwin
        out,err = run_command("sysctl -n hw.physicalcpu_max")
        return [(0, p) for p in range(0,int(str(out, 'utf-8')))]
    else:
        out,err = run_command("lscpu --parse")

    out = str(out, 'utf-8')
    # Identify the available CPU IDs on the system, along with their
    # configuration information (i.e., core and socket IDs).
    avail_cpus = []
    for l in out.splitlines():
        if l.startswith('#'):
            continue
        items = l.strip().split(',')
        cpu_id = int(items[0])
        core_id = int(items[1])
        socket_id = int(items[2])
        avail_cpus.append((socket_id, core_id, cpu_id))

    # Get the set of CPU IDs that correspond with distinct physical
    # cores.
    avail_cpus = sorted(avail_cpus)
    ret = []
    added_cores = dict()
    for x in avail_cpus:
        if x[1] not in added_cores:
            added_cores[x[1]] = True
        else:
            continue
        ret.append((x[2], x[0]))
    return ret

################################################################################
# Run the specified program with the given arguments.
#   prog - Binary executable to run.
#   prog_args - List of arguments to pass to the binary
#   parse_output_fn - Function to parse the output of running the
#     binary to extract the running time.
#   requested_trials - Number of times to rerun the binary.
#   cpu_counts - String describing the set of CPU counts to run the binary on.
#   out_csv - CSV filename where raw performance data will be written.
def run(prog, prog_args, parse_output_fn, requested_trials="1",
        cpu_counts=None, out_csv="out.csv"):
    # Parse cpu_counts argument to get list of CPU counts.
    NCPUS = get_n_cpus()
    if cpu_counts is None:
        cpu_counts = [NCPUS]
    elif cpu_counts == "all":
        cpu_counts = range(1, NCPUS+1)
    else:
        cpu_counts = list(map(int, cpu_counts.split(",")))

    # Join binary name and prog_args list to generate run command.
    run_command = prog + " " + " ".join(prog_args)

    logger.info("Timing " + run_command + " on <= " + str(NCPUS) + " cpus.")

    results = dict()
    last_CPU = NCPUS+1
    # Loop over possible CPU counts.
    for count in range(1, NCPUS+1):
        # If this count is a requested CPU count to use, run the
        # program on that CPU count.
        if count in cpu_counts:
            try:
                timings = dict()
                # Run the program on that CPU count.
                out,err = run_on_p_workers(count, requested_trials,
                                           run_command)
                # Parse the output of the run to extract timings.
                parse_output_fn(out, err, prog, prog_args, timings)
                # Add the timings to the set of results.
                if str(count) not in results:
                    results[str(count)] = timings
                else:
                    results[str(count)].append(timings)
            except KeyboardInterrupt:
                logger.info("Benchmarking stopped early at " +
                            str(count-1) + " cpus.")
                last_CPU = count
                break

    # Determine number of trials run.
    trials = 0
    for cpu_count in results:
        for bench in results[cpu_count]:
            trials = max(trials, len(results[cpu_count][bench]))

    # Output results to the CSV file.
    with open(out_csv, "w") as out_csv_file:
        # # Generate header for CSV file
        # out_csv_file.write("bench,P," + ','.join(["t" + str(i) for i
        #                                           in range(1,trials+1)]) + '\n')
        for cpu_count in results:
            for bench in results[cpu_count]:
                out_csv_file.write(bench + ',' + str(cpu_count) + ','
                                   + ','.join(results[cpu_count][bench]) + '\n')
