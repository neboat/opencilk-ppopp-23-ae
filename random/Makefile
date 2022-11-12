CXX = clang++

ifeq ($(CILKPLUS),1)
	CILKPLUS_RTS = /opt/cilkrts
	CILK_CFLAGS = -fcilkplus -I$(CILKPLUS_RTS)/include -DCILKPLUS
	CILK_LDFLAGS = -fcilkplus -L$(CILKPLUS_RTS)/lib -Wl,-rpath,$(CILKPLUS_RTS)/lib
else
	CILK_CFLAGS = -fopencilk -DOPENCILK
	CILK_LDFLAGS = -fopencilk -lopencilk-pedigrees
endif

CXXFLAGS = $(CILK_CFLAGS) -I../include -O3 $(EXTRA_CFLAGS)
LDFLAGS = $(CILK_LDFLAGS) -ltcmalloc $(EXTRA_LDFLAGS)

TARGETS = fib_rng pi

.PHONY: all default clean

default : all

all : $(TARGETS)

clean :
	rm -f $(TARGETS) *.o *~
