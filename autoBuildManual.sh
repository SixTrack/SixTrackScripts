#!/bin/bash

mkdir -pv build
cd build

if [ -f "../cmake_six" ]; then
  echo "Attemting to run the script from within the repository."
  echo "This should no be done. Please copy this script to a separate folder and run it there."
  exit 1
fi

if [ ! -d "SixTrack/.git" ]; then
  echo "SixTrack source missing, pulling ..."
  git clone https://github.com/SixTrack/SixTrack.git SixTrack
fi
cd SixTrack
git fetch origin master
git pull

if [ -f "../lastCommit.txt" ]; then
  echo "Found last commit file"
  LAST=$(cat ../lastCommit.txt)
  echo "Last hash:    $LAST"
else
  LAST="None"
  echo "Last hash:    $LAST"
fi

CURR=$(git rev-parse HEAD)
echo "Current hash: $CURR"

if [ "$LAST" != "$CURR" ]; then
  cd doc
  echo "Hashes differ. Building manual."
  ./generateForWeb.sh &> ../../htmlBuild.log
  echo "Uploading to website."
  rsync -avPh html/ /afs/cern.ch/project/sixtrack/docs/
  echo $CURR > ../../lastCommit.txt
else
  echo "No change. Exiting."
fi
