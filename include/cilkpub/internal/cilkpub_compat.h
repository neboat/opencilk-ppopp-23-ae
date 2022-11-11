/* cilkpub_compat.h                  -*-C++-*-
 *
 *************************************************************************
 *
 * Copyright (C) 2013-15 Intel Corporation
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 *  * Neither the name of Intel Corporation nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
 * WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *************************************************************************/

/**
 * @file cilkpub_compat.h
 *
 * @brief Check for various platform-specific constructs that are
 * likely to vary between platforms.
 *
 */
#ifndef __CILKPUB_COMPAT_H_
#define __CILKPUB_COMPAT_H_

// GNU C++ 4.5.1 or later, or VS2010 or later, are known to support std::move
#if (__GNUC__*10000+__GNUC_MINOR__*100+__GNUC_PATCHLEVEL__)>=40501 || _MSC_VER>=1600

// Even though the compiler may support C++11, sometimes a special flag is necessary.
// This next check is looking for specific flags for C++11. 
//
// * Old versions of GCC (e.g., gcc 4.6.3) do not seem to be standards-conforming
//   since they define __cplusplus macro as "1".
// * Recent versions of Visual Studio do not seem to set "cpluscplus" correctly.
//   We just look for _MSC_VER explicitly.   See the following link:
//     https://connect.microsoft.com/VisualStudio/feedback/details/763051/a-value-of-predefined-macro-cplusplus-is-still-199711l
//
#    if (__cplusplus >= 201103L) || defined(__GXX_EXPERIMENTAL_CXX0X__) || (_MSC_VER>=1600)
#        define CILKPUB_HAVE_STD_MOVE 1
#        define CILKPUB_HAVE_CPP11 1
#    endif
#endif

#if (__INTEL_COMPILER >= 1500)
#    define CILKPUB_DEPRECATED_REDUCER_VECTOR 1
#endif

/**
 * OS-independent macro to specify a function that should be inlined
 * in C code.  This code is modified from cilk/common.h.
 *
 * For C++ code, just use the "inline" keyword...
 */
#ifndef __cplusplus
#   if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
        // C99
#       define __CILKPUB_C_INLINE static inline
#   elif defined(_MSC_VER)
        // C89 on Windows
#       define __CILKPUB_C_INLINE __inline
#   else
        // C89 on GCC-compatible systems
#       define __CILKPUB_C_INLINE extern __inline__
#   endif
#endif


#endif // __CILKPUB_COMPAT_H_
