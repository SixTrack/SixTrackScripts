#!/bin/bash

rsync -rvPh --delete /scratch/TestBuild/Coverage/html/ /afs/cern.ch/project/sixtrack/coverage/
rsync -rvPh --delete /scratch/TestBuild/Results/       /afs/cern.ch/project/sixtrack/build_status/
rsync -rvPh --delete /scratch/TestBuild/*.log          /afs/cern.ch/project/sixtrack/nightly_data/
rsync -rvPh --delete /scratch/TestBuild/Timing/        /afs/cern.ch/project/sixtrack/nightly_data/tests/
rsync -rvPh --delete /scratch/TestBuild/Coverage/*.tgz /afs/cern.ch/project/sixtrack/nightly_data/coverage/
