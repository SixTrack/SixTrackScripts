#!/bin/bash

rsync -rvPh --delete /scratch/TestBuild/Coverage/html/ /afs/cern.ch/project/sixtrack/coverage/
rsync -rvPh --delete /scratch/TestBuild/Results/       /afs/cern.ch/project/sixtrack/build_status/
