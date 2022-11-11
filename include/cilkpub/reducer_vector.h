/*  reducer_vector.h                  -*- C++ -*-
 *
 *  Copyright (C) 2013-15 Intel Corporation.  All Rights Reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *  
 *    * Redistributions of source code must retain the above copyright
 *      notice, this list of conditions and the following disclaimer.
 *    * Redistributions in binary form must reproduce the above copyright
 *      notice, this list of conditions and the following disclaimer in
 *      the documentation and/or other materials provided with the
 *      distribution.
 *    * Neither the name of Intel Corporation nor the names of its
 *      contributors may be used to endorse or promote products derived
 *      from this software without specific prior written permission.
 *  
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 *  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 *  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 *  AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
 *  WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 */

/** @file reducer_vector.h
 *
 *  @brief  Defines the monoid and view classes for reducers to create a
 *          standard vector in parallel.  
 *
 *  @warning This header file is deprecated, since Intel Cilk Plus
 *  includes includes an implementation of reducer_vector in versions
 *  15.0 and later.
 *
 *  @version 1.06
 *
 *  @see @ref VectorReducers
 *
 *  @ingroup VectorReducers
 */


#include <cilkpub/internal/cilkpub_compat.h>

#if CILKPUB_DEPRECATED_REDUCER_VECTOR
#   warning "Reducer vector is now defined in cilk/reducer_vector.h.   It is recommended to use cilk::reducer_vector instead of cilkpub::reducer_vector"

#include <cilk/reducer_vector.h>
namespace cilkpub {

  #ifndef CILKPUB_HAVE_CPP11
  #    error "Use of cilkpub::reducer_vector requires C++11 features"
  #endif
  // Define an alias template so that cilkpub versions forward to cilk versions.
  template <typename Type, typename Alloc = std::allocator<Type> >
  using op_vector = cilk::op_vector<Type, Alloc>;
  
} //  namespace cilkpub

#else

// Just include the old implementation.
#    include <cilkpub/internal/reducer_vector_cilkpub.h>

#endif //  CILKPUB_REDUCER_VECTOR_H_INCLUDED
