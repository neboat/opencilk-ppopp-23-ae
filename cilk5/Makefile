ALL_TESTS = fft cholesky nqueens qsort rectmul strassen cilksort heat lu matmul

CC ?= clang
CXX ?= clang++

CFLAGS = -Wall -O3
CXXFLAGS = -Wall -O3
LDFLAGS =
LDLIBS = -ltcmalloc

PRESERVE_ALL_SPAWNS_FLAG = -mllvm -simplifycfg-preserve-all-spawns -mllvm -tasksimplify-preserve-all-spawns

ifeq ($(SERIAL),1)
	CILKFLAG ?=
	SERIAL_FLAGS = -DSERIAL
	CFLAGS += $(SERIAL_FLAGS)
	CXXFLAGS += $(SERIAL_FLAGS)
endif

ifeq ($(CILKPLUS),1)
	CILKPLUS_RTS ?= /opt/cilkrts
	CFLAGS += -I$(CILKPLUS_RTS)/include
	CILKFLAG = -fcilkplus
	LDFLAGS = -L$(CILKPLUS_RTS)/lib -Wl,-rpath,$(CILKPLUS_RTS)/lib
else ifeq ($(OPENMP),1)
	CFLAGS += -fopencilk -fopenmp -ftapir=omptask -mllvm -omp-bc-path=/usr/local/src/ppopp-23-ae/extra-bitcode-abis/omp-task-rt-abi.bc -DOMPTASK $(PRESERVE_ALL_SPAWNS_FLAG)
	CXXFLAGS += -fopencilk -fopenmp -ftapir=omptask -mllvm -omp-bc-path=/usr/local/src/ppopp-23-ae/extra-bitcode-abis/omp-task-rt-abi.bc -DOMPTASK $(PRESERVE_ALL_SPAWNS_FLAG)
	LDFLAGS = -fopenmp
else ifeq ($(TBB),1)
	CFLAGS += -fopencilk -ftapir=lambda -mllvm -tapir-runtime-bc-path=/usr/local/src/ppopp-23-ae/extra-bitcode-abis/tbb-bc-abi.bc
	CXXFLAGS += -fopencilk -ftapir=lambda -mllvm -tapir-runtime-bc-path=/usr/local/src/ppopp-23-ae/extra-bitcode-abis/tbb-bc-abi.bc
	LDFLAGS = -ltbb -lstdc++ -L/usr/local/lib -Wl,-rpath,/usr/local/lib
else
	CILKFLAG ?= -fopencilk
endif

CFLAGS += $(CILKFLAG) $(EXTRA_CFLAGS)
CXXFLAGS += $(CILKFLAG) $(EXTRA_CFLAGS)
LDFLAGS += $(CILKFLAG) $(EXTRA_LDFLAGS)
LDLIBS += $(EXTRA_LDLIBS)

.PHONY : default clean

default: all

all: $(ALL_TESTS)

%.o : %.c
	$(CC) $(CFLAGS) -c $<

%.o : %.cpp
	$(CXX) $(CXXFLAGS) -c $<

%.o : %.cc
	$(CXX) $(CXXFLAGS) -c $<

cholesky: getoptions.o cholesky.o
cilksort: getoptions.o cilksort.o
fft: getoptions.o fft.o
heat: getoptions.o heat.o
lu: getoptions.o lu.o
matmul: getoptions.o matmul.o
nqueens: getoptions.o nqueens.o
rectmul: getoptions.o rectmul.o
strassen: getoptions.o strassen.o
qsort: qsort.o

fft cholesky : LDLIBS += -lm

# qsort : CXXFLAGS += -falign-functions=32

% : %.o
	$(CXX) $(LDFLAGS) $^ $(LDLIBS) -o $@

clean :
	rm -f $(ALL_TESTS) *.o *.d* *~
