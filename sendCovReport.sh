#!/bin/bash

cd /scratch/TestBuild/Coverage
rsync -rvPh --delete html/ /afs/cern.ch/project/sixtrack/coverage/
