licenses(["notice"])

cc_binary(
    name = "run_gbbs_experiments",
    srcs = ["run_gbbs_experiments.cc"],
    # linkopts = ["-lpython3.6m"],
    linkopts = ["-lpython3.9"],
    deps = [
        "//benchmarks/SCAN/IndexBased:scan",
        "//benchmarks/SCAN/IndexBased:similarity_measure",
        "//benchmarks/SCAN/IndexBased:utils",
        "//gbbs",
        "//gbbs/helpers:assert",
    ],
)

cc_binary(
    name = "remove_singleton_vertices",
    srcs = ["remove_singleton_vertices.cc"],
    deps = [
        "//gbbs/helpers:parse_command_line",
    ],
)
