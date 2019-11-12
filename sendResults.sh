#!/bin/bash

rsync -ruvPh --delete /scratch/TestBuild/Coverage/html/ /afs/cern.ch/project/sixtrack/coverage/
rsync -ruvPh --delete /scratch/TestBuild/Results/       /afs/cern.ch/project/sixtrack/build_status/
rsync -ruvPh --delete /scratch/TestBuild/*.log          /afs/cern.ch/project/sixtrack/nightly_data/
rsync -ruvPh --delete /scratch/TestBuild/Timing/        /afs/cern.ch/project/sixtrack/nightly_data/tests/
rsync -ruvPh --delete /scratch/TestBuild/Coverage/*.tgz /afs/cern.ch/project/sixtrack/nightly_data/coverage/
