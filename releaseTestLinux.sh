#!/bin/bash

cd /home/vkbo/Temp
mkdir -pv SixTrackLinux
cd SixTrackLinux
if [ ! -d ".git" ]; then
    git clone https://github.com/SixTrack/SixTrack.git .
fi

rm *_test*.log
git fetch master
git pull

rm -rf build_testStandard
mkdir -p build_testStandard
cd build_testStandard
cmake .. -DCMAKE_Fortran_COMPILER=gfortran -DBUILD_TESTING=ON | tee ../cmake_testStandard.log
make -j4 | tee ../make_testStandard.log
cd ..

rm -rf build_testCR
mkdir -p build_testCR
cd build_testCR
cmake .. -DCMAKE_Fortran_COMPILER=gfortran -DBUILD_TESTING=ON -DCR=ON | tee ../cmake_testCR.log
make -j4 | tee ../make_testCR.log
cd ..

cd build_testStandard
ctest -L fast -E elens -j4 | tee ../ctestFast_testStandard.log
cd ..

cd build_testCR
ctest -L fast -E elens -j4 | tee ../ctestFast_testCR.log
cd ..

cd build_testStandard
ctest -L medium -E elens -j4 | tee ../ctestMedium_testStandard.log
cd ..

cd build_testCR
ctest -L medium -E elens -j4 | tee ../ctestMedium_testCR.log
cd ..
