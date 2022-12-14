#ifndef _Vector_hpp_
#define _Vector_hpp_

//@HEADER
// ************************************************************************
// 
//               HPCCG: Simple Conjugate Gradient Benchmark Code
//                 Copyright (2006) Sandia Corporation
// 
// Under terms of Contract DE-AC04-94AL85000, there is a non-exclusive
// license for use of this work by or on behalf of the U.S. Government.
// 
// This library is free software; you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as
// published by the Free Software Foundation; either version 2.1 of the
// License, or (at your option) any later version.
//  
// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//  
// You should have received a copy of the GNU Lesser General Public
// License along with this library; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
// USA
// Questions? Contact Michael A. Heroux (maherou@sandia.gov) 
// 
// ************************************************************************
//@HEADER

#include <vector>

#include <cilk/cilk.h>
// #include <cilk/reducer_opadd.h>

#ifdef SERIAL
#include <cilk/cilk_stub.h>
#endif

namespace miniFE {


template<typename Scalar,
         typename LocalOrdinal,
         typename GlobalOrdinal>
struct Vector {
  typedef Scalar ScalarType;
  typedef LocalOrdinal LocalOrdinalType;
  typedef GlobalOrdinal GlobalOrdinalType;

  Vector(GlobalOrdinal startIdx, LocalOrdinal local_sz)
   : startIndex(startIdx),
     local_size(local_sz),
     coefs(local_size)
  {
    cilk_for(MINIFE_GLOBAL_ORDINAL i=0; i < local_size; ++i) {
	coefs[i] = 0;
    }

  }

  ~Vector()
  {
  }

  GlobalOrdinal startIndex;
  LocalOrdinal local_size;
  std::vector<Scalar> coefs;
};


}//namespace miniFE

#endif

