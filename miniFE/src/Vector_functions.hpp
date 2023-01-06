#ifndef _Vector_functions_hpp_
#define _Vector_functions_hpp_

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
#include <sstream>
#include <fstream>

#ifdef HAVE_MPI
#include <mpi.h>
#endif

#ifdef MINIFE_HAVE_TBB
#include <LockingVector.hpp>
#endif

#include <TypeTraits.hpp>
#include <Vector.hpp>

#include <cilk/cilk.h>

#ifdef SERIAL
#include <cilk/cilk_stub.h>
#endif

#define USE_REDUCERS 0

#if USE_REDUCERS
#ifdef CILKPLUS
#include <cilk/reducer_opadd.h>
#else
#include <cilk/opadd_reducer.h>
#endif
#else
#include <cilk/cilk_api.h>
#endif // USE_REDUCERS

#if defined(OMPTASK) || defined(TBB)
extern "C" int __rts_get_num_workers();
extern "C" int __rts_get_worker_id();
#endif

namespace miniFE {


template<typename VectorType>
void write_vector(const std::string& filename,
                  const VectorType& vec)
{
  int numprocs = 1, myproc = 0;
#ifdef HAVE_MPI
  MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
  MPI_Comm_rank(MPI_COMM_WORLD, &myproc);
#endif

  std::ostringstream osstr;
  osstr << filename << "." << numprocs << "." << myproc;
  std::string full_name = osstr.str();
  std::ofstream ofs(full_name.c_str());

  typedef typename VectorType::ScalarType ScalarType;

  const std::vector<ScalarType>& coefs = vec.coefs;
  for(int p=0; p<numprocs; ++p) {
    if (p == myproc) {
      if (p == 0) {
        ofs << vec.local_size << std::endl;
      }
  
      typename VectorType::GlobalOrdinalType first = vec.startIndex;
      for(size_t i=0; i<vec.local_size; ++i) {
        ofs << first+i << " " << coefs[i] << std::endl;
      }
    }
#ifdef HAVE_MPI
    MPI_Barrier(MPI_COMM_WORLD);
#endif
  }
}

template<typename VectorType>
void sum_into_vector(size_t num_indices,
                     const typename VectorType::GlobalOrdinalType* indices,
                     const typename VectorType::ScalarType* coefs,
                     VectorType& vec)
{
  typedef typename VectorType::GlobalOrdinalType GlobalOrdinal;
  typedef typename VectorType::ScalarType Scalar;

  GlobalOrdinal first = vec.startIndex;
  GlobalOrdinal last = first + vec.local_size - 1;

  std::vector<Scalar>& vec_coefs = vec.coefs;

  for(size_t i=0; i<num_indices; ++i) {
    if (indices[i] < first || indices[i] > last) continue;
    size_t idx = indices[i] - first;
    vec_coefs[idx] += coefs[i];
  }
}

#ifdef MINIFE_HAVE_TBB
template<typename VectorType>
void sum_into_vector(size_t num_indices,
                     const typename VectorType::GlobalOrdinalType* indices,
                     const typename VectorType::ScalarType* coefs,
                     LockingVector<VectorType>& vec)
{
  vec.sum_in(num_indices, indices, coefs);
}
#endif

//------------------------------------------------------------
//Compute the update of a vector with the sum of two scaled vectors where:
//
// w = alpha*x + beta*y
//
// x,y - input vectors
//
// alpha,beta - scalars applied to x and y respectively
//
// w - output vector
//
template<typename VectorType>
void
  waxpby(typename VectorType::ScalarType alpha, const VectorType& x,
         typename VectorType::ScalarType beta, const VectorType& y,
         VectorType& w)
{
  typedef typename VectorType::ScalarType ScalarType;

#ifdef MINIFE_DEBUG
  if (y.local_size < x.local_size || w.local_size < x.local_size) {
    std::cerr << "miniFE::waxpby ERROR, y and w must be at least as long as x." << std::endl;
    return;
  }
#endif

  const int n = x.coefs.size();
  const ScalarType* xcoefs = &x.coefs[0];
  const ScalarType* ycoefs = &y.coefs[0];
        ScalarType* wcoefs = &w.coefs[0];

#ifdef OMPTASK
#pragma omp parallel
  {
    #pragma omp single
    {
#endif
  cilk_for(int i = 0; i < n; i++) {
    wcoefs[i] = alpha*xcoefs[i] + beta*ycoefs[i];
  }
#ifdef OMPTASK
    }
  }
#endif

}

//------------------------------------------------------------
//Compute the update of a vector with the sum of two scaled vectors where:
//
// w = alpha*x + beta*y
//
// x,y - input vectors
//
// alpha,beta - scalars applied to x and y respectively
//
// w - output vector
//
template<typename VectorType>
void
  daxpby(typename VectorType::ScalarType alpha, const VectorType& x,
         typename VectorType::ScalarType beta, VectorType& y)
{
  typedef typename VectorType::ScalarType ScalarType;

#ifdef MINIFE_DEBUG
  if (y.local_size < x.local_size || w.local_size < x.local_size) {
    std::cerr << "miniFE::waxpby ERROR, y and w must be at least as long as x." << std::endl;
    return;
  }
#endif

  const MINIFE_LOCAL_ORDINAL n   = x.coefs.size();
  const ScalarType* const xcoefs = &x.coefs[0];
  	ScalarType* const ycoefs = &y.coefs[0];

#ifdef OMPTASK
#pragma omp parallel
  {
    #pragma omp single
    {
#endif
  if(beta == 1 && alpha == 1) {
  	cilk_for(int i = 0; i < n; i++) {
		ycoefs[i] += xcoefs[i];
  	}
  } else if(beta == 1) {
  	cilk_for(int i = 0; i < n; i++) {
		ycoefs[i] += alpha*xcoefs[i];
  	}
  } else if(beta == 0) {
  	cilk_for(int i = 0; i < n; i++) {
		ycoefs[i] = alpha*xcoefs[i];
  	}
  } else if(alpha == 0) {
  	cilk_for(int i = 0; i < n; i++) {
		ycoefs[i] *= beta;
  	}
  } else {
  	cilk_for(int i = 0; i < n; i++) {
		ycoefs[i] = alpha*xcoefs[i] + beta*ycoefs[i];
  	}
  }
#ifdef OMPTASK
    }
  }
#endif
}

//Like waxpby above, except operates on two sets of arguments.
//In other words, performs two waxpby operations in one loop.
template<typename VectorType>
void
  fused_waxpby(typename VectorType::ScalarType alpha, const VectorType& x,
         typename VectorType::ScalarType beta, const VectorType& y,
         VectorType& w,
         typename VectorType::ScalarType alpha2, const VectorType& x2,
         typename VectorType::ScalarType beta2, const VectorType& y2,
         VectorType& w2)
{
  typedef typename VectorType::ScalarType ScalarType;

#ifdef MINIFE_DEBUG
  if (y.local_size < x.local_size || w.local_size < x.local_size) {
    std::cerr << "miniFE::waxpby ERROR, y and w must be at least as long as x." << std::endl;
    return;
  }
#endif

  const int n = x.coefs.size();
  const ScalarType* xcoefs = &x.coefs[0];
  const ScalarType* ycoefs = &y.coefs[0];
        ScalarType* wcoefs = &w.coefs[0];

  const ScalarType* x2coefs = &x2.coefs[0];
  const ScalarType* y2coefs = &y2.coefs[0];
        ScalarType* w2coefs = &w2.coefs[0];

#ifdef OMPTASK
#pragma omp parallel
  {
    #pragma omp single
    {
#endif
  cilk_for(int i=0; i<n; ++i) {
    wcoefs[i] = alpha*xcoefs[i] + beta*ycoefs[i];
    w2coefs[i] = alpha2*x2coefs[i] + beta2*y2coefs[i];
  }
#ifdef OMPTASK
    }
  }
#endif
}

#if !USE_REDUCERS
template<typename Scalar>
struct Scalar_TLS {
  Scalar val;
} __attribute__((aligned(64)));
#endif

//-----------------------------------------------------------
//Compute the dot product of two vectors where:
//
// x,y - input vectors
//
// result - return-value
//
template<typename Vector>
typename TypeTraits<typename Vector::ScalarType>::magnitude_type
  dot(const Vector& x,
      const Vector& y)
{
  const int n = x.coefs.size();

#ifdef MINIFE_DEBUG
  if (y.local_size < n) {
    std::cerr << "miniFE::dot ERROR, y must be at least as long as x."<<std::endl;
    n = y.local_size;
  }
#endif

  typedef typename Vector::ScalarType Scalar;
  typedef typename TypeTraits<typename Vector::ScalarType>::magnitude_type magnitude;

  const Scalar* xcoefs = &x.coefs[0];
  const Scalar* ycoefs = &y.coefs[0];
  //magnitude result = 0;
#if USE_REDUCERS
#ifdef CILKPLUS
  cilk::reducer_opadd<Scalar> result_reducer(0);
#else
  cilk::opadd_reducer<Scalar> result_reducer = 0;
#endif
#else
  Scalar result = 0;
#endif // USE_REDUCERS

#ifdef OMPTASK
#pragma omp parallel
  {
    #pragma omp single
    {
#endif
#if !USE_REDUCERS
#ifndef SERIAL
#if defined(OMPTASK) || defined(TBB)
  int num_workers = __rts_get_num_workers();
#else
  int num_workers = __cilkrts_get_nworkers();
#endif
  Scalar_TLS<Scalar> *result_reducer = new Scalar_TLS<Scalar>[num_workers];
  for (int i = 0; i < num_workers; ++i) {
    result_reducer[i].val = 0;
  }
#else
  Scalar result_reducer = 0;
#endif // SERIAL
#endif // !USE_REDUCERS
  cilk_for(int i=0; i<n; ++i) {
#if USE_REDUCERS
    result_reducer += xcoefs[i]*ycoefs[i];
#else // USE_REDUCERS
#ifndef SERIAL
#if defined(OMPTASK) || defined(TBB)
    result_reducer[__rts_get_worker_id()].val += xcoefs[i]*ycoefs[i];
#else
    result_reducer[__cilkrts_get_worker_number()].val += xcoefs[i]*ycoefs[i];
#endif
#else
    result_reducer += xcoefs[i]*ycoefs[i];
#endif // SERIAL
#endif // USE_REDUCERS
  }
#if !USE_REDUCERS
#ifndef SERIAL
  for (int i = 0; i < num_workers; ++i) {
    result += result_reducer[i].val;
  }
  delete[] result_reducer;
#else
  result = result_reducer;
#endif // SERIAL
#endif // !USE_REDUCERS
#ifdef OMPTASK
    }
  }
#endif

#ifdef HAVE_MPI
#if USE_REDUCERS
#ifdef CILKPLUS
  magnitude local_dot = result_reducer.get_value(), global_dot = 0;
#else
  magnitude local_dot = result_reducer, global_dot = 0;
#endif
#else
  magnitude local_dot = result, global_dot = 0;
#endif // USE_REDUCERS
  MPI_Datatype mpi_dtype = TypeTraits<magnitude>::mpi_type();  
  MPI_Allreduce(&local_dot, &global_dot, 1, mpi_dtype, MPI_SUM, MPI_COMM_WORLD);
  return global_dot;
#else
#if USE_REDUCERS
#ifdef CILKPLUS
  return result_reducer.get_value();
#else
  return result_reducer;
#endif // CILKPLUS
#else
  return result;
#endif // USE_REDUCERS
#endif // HAVE_MPI
}

template<typename Vector>
typename TypeTraits<typename Vector::ScalarType>::magnitude_type
  dot_r2(const Vector& x)
{
  const MINIFE_LOCAL_ORDINAL n = x.coefs.size();

#ifdef MINIFE_DEBUG
  if (y.local_size < n) {
    std::cerr << "miniFE::dot ERROR, y must be at least as long as x."<<std::endl;
    n = y.local_size;
  }
#endif

  typedef typename Vector::ScalarType Scalar;
  typedef typename TypeTraits<typename Vector::ScalarType>::magnitude_type magnitude;

  const Scalar* xcoefs = &x.coefs[0];
#if USE_REDUCERS
#ifdef CILKPLUS
  cilk::reducer_opadd<Scalar> result_reducer(0);
#else
  cilk::opadd_reducer<Scalar> result_reducer = 0;
#endif
#else
  Scalar result = 0;
#endif // USE_REDUCERS

#ifdef OMPTASK
#pragma omp parallel
  {
    #pragma omp single
    {
#endif
#if !USE_REDUCERS
#ifndef SERIAL
#if defined(OMPTASK) || defined(TBB)
  int num_workers = __rts_get_num_workers();
#else
  int num_workers = __cilkrts_get_nworkers();
#endif
  Scalar_TLS<Scalar> *result_reducer = new Scalar_TLS<Scalar>[num_workers];
  for (int i = 0; i < num_workers; ++i) {
    result_reducer[i].val = 0;
  }
#else
  Scalar result_reducer = 0;
#endif // SERIAL
#endif // !USE_REDUCERS
  cilk_for(int i=0; i<n; ++i) {
#if USE_REDUCERS
    result_reducer += xcoefs[i] * xcoefs[i];
#else
#ifndef SERIAL
#if defined(OMPTASK) || defined(TBB)
    result_reducer[__rts_get_worker_id()].val += xcoefs[i] * xcoefs[i];
#else
    result_reducer[__cilkrts_get_worker_number()].val += xcoefs[i] * xcoefs[i];
#endif
#else
    result_reducer += xcoefs[i] * xcoefs[i];
#endif // SERIAL
#endif // USE_REDUCERS
  }
#if !USE_REDUCERS
#ifndef SERIAL
  for (int i = 0; i < num_workers; ++i) {
    result += result_reducer[i].val;
  }
  delete[] result_reducer;
#else
  result = result_reducer;
#endif // SERIAL
#endif // USE_REDUCERS
#ifdef OMPTASK
    }
  }
#endif

#ifdef HAVE_MPI
#if USE_REDUCERS
#ifdef CILKPLUS
  magnitude local_dot = result_reducer.get_value(), global_dot = 0;
#else
  magnitude local_dot = result_reducer, global_dot = 0;
#endif
#else
  magnitude local_dot = result, global_dot = 0;
#endif // USE_REDUCERS
  MPI_Datatype mpi_dtype = TypeTraits<magnitude>::mpi_type();  
  MPI_Allreduce(&local_dot, &global_dot, 1, mpi_dtype, MPI_SUM, MPI_COMM_WORLD);
  return global_dot;
#else
#if USE_REDUCERS
#ifdef CILKPLUS
  return result_reducer.get_value();
#else
  return result_reducer;
#endif
#else
  return result;
#endif // USE_REDUCERS
#endif // HAVE_MPI
}

}//namespace miniFE

#endif

