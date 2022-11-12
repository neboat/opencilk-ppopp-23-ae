#-----------------------------------------------------------------------

MINIFE_TYPES =  \
        -DMINIFE_SCALAR=double   \
        -DMINIFE_LOCAL_ORDINAL=int      \
        -DMINIFE_GLOBAL_ORDINAL=int

MINIFE_MATRIX_TYPE = -DMINIFE_CSR_MATRIX
# MINIFE_MATRIX_TYPE = -DMINIFE_ELL_MATRIX

#-----------------------------------------------------------------------

ifeq ($(SERIAL),1)
	EXTRA_CFLAGS += -DSERIAL
	CILKFLAG =
else ifeq ($(CILKPLUS),1)
	CILKPLUS_RTS=/opt/cilkrts
	EXTRA_CFLAGS += -DCILKPLUS -I$(CILKPLUS_RTS)/include
	CILKFLAG ?= -fcilkplus
	EXTRA_LDFLAGS += -L$(CILKPLUS_RTS)/lib -Wl,-rpath,$(CILKPLUS_RTS)/lib
else
	CILKFLAG ?= -fopencilk
endif

CFLAGS = -O2 -mavx $(CILKFLAG) $(EXTRA_CFLAGS)
CXXFLAGS = $(CFLAGS)

# For debugging, the macro MINIFE_DEBUG will cause miniFE to dump a log file
# from each proc containing various information.
# This macro will also enable a somewhat expensive range-check on indices in
# the exchange_externals function.

# CPPFLAGS = -I. -I../utils -I../fem $(MINIFE_TYPES) -DMINIFE_DEBUG -DHAVE_MPI -DMPICH_IGNORE_CXX_SEEK
CPPFLAGS = -I. -I../utils -I../fem $(MINIFE_TYPES) $(MINIFE_MATRIX_TYPE) -DHAVE_MPI -DMPICH_IGNORE_CXX_SEEK

LDFLAGS=$(EXTRA_LDFLAGS)
LIBS=-ltcmalloc $(EXTRA_LDLIBS)

# The MPICH_IGNORE_CXX_SEEK macro is required for some mpich versions,
# such as the one on my cygwin machine.

# MPICC=/usr/lib64/openmpi/bin/mpicc
# MPICXX=/usr/lib64/openmpi/bin/mpic++
MPICC=mpicc
MPICXX=mpic++

#CXX=mpiicpc
#CC=mpiicc
CC=$(MPICC)
CXX=$(MPICXX)
include make_targets

