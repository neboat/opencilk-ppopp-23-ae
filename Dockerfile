FROM ubuntu:22.04

# NOTE: Don't use ADD; ADD will decompress the file
COPY opencilk.tar.gz /usr/local/src/opencilk.tar.gz

# Note that it is possible to specify a sequence of RUN commands, but there
# are various issues with this practice. The first issue is that each separate
# RUN command creates an extra layer of information that is stored with the
# container, which significantly bloats the image. Essentially these layers are
# diffs, so if we extract the opencilk tar in a step separate from removing the
# extracted files then Docker still stores those files in one of the layers, thus
# causing the Docker image to increase in size.

# Step 1: Install build dependencies (TODO: may be possible to install less)
# Step 2: Untar, build, and install OpenCilk
# Step 3: Remove the build files and apt-get cache files
RUN echo "Installing packages..." \
  && apt-get update -qq > /dev/null \
  && apt-get install -qqy --no-install-recommends \
    cmake \
    clang \
    lld \
    make \
    python3 \
    libpython3-stdlib \
    libtcmalloc-minimal4 \
    libopenmpi-dev \
    > /dev/null \
  && echo "Installing Bazel..." \
  && apt install apt-transport-https curl gnupg \
  && curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg \
  && mv bazel-archive-keyring.gpg /usr/share/keyrings \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list \
  && apt update -qq > /dev/null \
  && apt install -qqy --no-install-recommends bazel \
  && echo "Building OpenCilk..." \
  && tar -C /usr/local/src -xzf /usr/local/src/opencilk.tar.gz \
  && mkdir -p /usr/local/src/opencilk/build \
  && /usr/local/src/ppopp-23-ae/build-opencilk /usr/local/src/opencilk/opencilk-project \
    /usr/local/src/opencilk/build \
  && echo "Building CilkRTS..." \
  && /usr/local/src/ppopp-23-ae/build-cilkrts /usr/local/src/ppopp-23-ae/cilkrts \
    /usr/local/src/ppopp-23-ae/cilkrts/build \
  && echo "Cleaning temporary files..." \
  && rm -rf /usr/local/src/opencilk/build \
  && rm -rf /usr/local/src/ppopp-23-ae/cilkrts/build \
  && rm -rf /var/lib/apt/lists/* \
  && echo "DOCKER IMAGE BUILT"
