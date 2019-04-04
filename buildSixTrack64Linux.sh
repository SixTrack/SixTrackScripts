#!/bin/bash

if [ -z "$1" ]; then
  echo "Please specify a version number"
  exit 1
fi
VERSION=$1
BINS=/afs/cern.ch/user/v/volsen/SixTrack/Releases/$VERSION
BUILD="-DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release"
mkdir -p $BINS

rm -rf build_exec1
mkdir -p build_exec1
cd build_exec1
eval cmake .. $BUILD
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_Linux_static_64bit_double
cd ..

rm -rf build_exec2
mkdir -p build_exec2
cd build_exec2
eval cmake .. $BUILD -DAVX=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_Linux_static_avx_64bit_double
cd ..

rm -rf build_exec3
mkdir -p build_exec3
cd build_exec3
eval cmake .. $BUILD -DBOINC=ON -DAPI=ON -DLIBARCHIVE=ON -DCR=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_boinc_Linux_static_64bit_double
cd ..

rm -rf build_exec4
mkdir -p build_exec4
cd build_exec4
eval cmake .. $BUILD -DBOINC=ON -DAPI=ON -DLIBARCHIVE=ON -DCR=ON -DAVX=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_boinc_Linux_static_avx_64bit_double
cd ..
