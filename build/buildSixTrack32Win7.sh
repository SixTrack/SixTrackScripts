#!/bin/bash

if [ -z "$1" ]; then
  echo "Please specify a version number"
  exit 1
fi
VERSION=$1
BINS=/h/Code/SixTrack/Releases/$VERSION
BUILD="-DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release"
mkdir -p $BINS

rm -rf build_exec1
mkdir -p build_exec1
cd build_exec1
eval cmake .. -G \"Unix Makefiles\" $BUILD -D64BIT=OFF -D32BIT=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_Win7_static_32bit_double.exe
cd ..

rm -rf build_exec2
mkdir -p build_exec2
cd build_exec2
eval cmake .. -G \"Unix Makefiles\" $BUILD -D64BIT=OFF -D32BIT=ON -DAVX=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_Win7_static_avx_32bit_double.exe
cd ..

rm -rf build_exec3
mkdir -p build_exec3
cd build_exec3
eval cmake .. -G \"Unix Makefiles\" $BUILD -D64BIT=OFF -D32BIT=ON -DBOINC=ON -DAPI=ON -DLIBARCHIVE=ON -DCR=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_boinc_Win7_static_32bit_double.exe
cd ..

rm -rf build_exec4
mkdir -p build_exec4
cd build_exec4
eval cmake .. -G \"Unix Makefiles\" $BUILD -D64BIT=OFF -D32BIT=ON -DBOINC=ON -DAPI=ON -DLIBARCHIVE=ON -DCR=ON -DAVX=ON
make -j4
cp SixTrack_$VERSION_* $BINS/SixTrack_$VERSION\_boinc_Win7_static_avx_32bit_double.exe
cd ..
