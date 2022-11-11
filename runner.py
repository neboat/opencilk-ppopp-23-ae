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

def get_n_cpus():
    return len(get_cpu_ordering())

def run_command(cmd, asyn = False):
    proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if not asyn:
        out,err=proc.communicate()
        return out,err
    else:
        return ""

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

        # print(">> STDOUT (" + rcommand + ")")
        # print(str(out,"utf-8"), file=sys.stdout, end='')
        # print("<< END STDOUT")
        # print()
        # print(">> STDERR (" + rcommand + ")")
        # print(str(err,"utf-8"), file=sys.stderr, end='')
        # print("<< END STDERR")

        output = output + str(out, "utf-8")
        errout = errout + str(err, "utf-8")
    return output,errout

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

def run(prog, prog_args, parse_output_fn, requested_trials="1",
        cpu_counts=None, out_csv="out.csv"):
    # get benchmark runtimes
    NCPUS = get_n_cpus()
    if cpu_counts is None:
        cpu_counts = [NCPUS]
    elif cpu_counts == "all":
        cpu_counts = range(1, NCPUS+1)
    else:
        cpu_counts = list(map(int, cpu_counts.split(",")))

    run_command = prog + " " + " ".join(prog_args)

    logger.info("Timing " + run_command + " on <= " + str(NCPUS) + " cpus.")

    results = dict()
    last_CPU = NCPUS+1
    for count in range(1, NCPUS+1):
        if count in cpu_counts:
            try:
                timings = dict()
                out,err = run_on_p_workers(count, requested_trials,
                                           run_command)
                parse_output_fn(out, err, prog, prog_args, timings)
                if str(count) not in results:
                    results[str(count)] = timings
                else:
                    results[str(count)].append(timings)
            except KeyboardInterrupt:
                logger.info("Benchmarking stopped early at " +
                            str(count-1) + " cpus.")
                last_CPU = count
                break

    trials = 0
    for cpu_count in results:
        for bench in results[cpu_count]:
            trials = max(trials, len(results[cpu_count][bench]))

    # Output results to the CSV file
    with open(out_csv, "w") as out_csv_file:
        # out_csv_file.write("bench,P," + ','.join(["t" + str(i) for i
        #                                           in range(1,trials+1)]) + '\n')
        for cpu_count in results:
            for bench in results[cpu_count]:
                out_csv_file.write(bench + ',' + str(cpu_count) + ','
                                   + ','.join(results[cpu_count][bench]) + '\n')
