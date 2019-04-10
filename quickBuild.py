#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""SixTrack Quick Build

  SixTrack Quick Build
 ======================
  Do a quick build and test of SixTrack
  By: Veronica Berglyd Olsen
      CERN (BE-ABP-HSS)
      Geneva, Switzerland

"""

import sys
import logging
from os import path, chdir, mkdir,system,listdir
from buildFucntions import *

logger = logging.getLogger("SixTrackTestBuild")

##
#  Settings
##

dRoot    = "/scratch/TestBuild"
dSource  = "/scratch/TestBuild/Source/Mirror"
dLog     = "/scratch/Temp/"
dTemp    = "/scratch/Temp/"
dLibs    = "/scratch/TestBuild/Source/SixTrack/lib"

nBld  = 8
nTest = 10
nCov  = 14

setupLogging(dLog,True)

logger.info("*"*80)
logger.info("* Starting New Quick Build Session")
logger.info("*"*80)

mirrorRepo(dSource)

# Parse arguments, but don't be difficult

chkType  = "b"
chkRef   = "refs/heads/master"
theComps = []
theFlags = ["BUILD_TESTING"]
theTest  = "-L fast"
showStd  = False

for anArg in sys.argv[1:]:
  if anArg[:2] == "b:":
    chkType = "b"
    chkRef  = "refs/heads/%s" % anArg[2:]
  elif anArg[:3] == "pr:":
    chkType = "pr"
    chkRef  = "refs/pull/%s/head" % anArg[3:]
  elif anArg[:4] == "tag:":
    chkType = "pr"
    chkRef  = "refs/tags/%s" % anArg[4:]
  elif anArg == "gfortran":
    theComps.append("gfortran")
  elif anArg == "ifort":
    theComps.append("ifort")
  elif anArg == "nagfor":
    theComps.append("nagfor")
  elif anArg == "fast":
    theTest = "-L fast"
  elif anArg == "medium":
    theTest = "-L medium"
  elif anArg == "fastmedium":
    theTest = "-E prob"
  elif anArg == "gonuts":
    theTest = "-E prob"
  elif anArg == "spammy":
    showStd = True
  else:
    theFlags.append(anArg)

if len(theComps) == 0:
  theComps = ["gfortran"]

logger.info("")
logger.info("Arguments:")
logger.info(" * Will checkout:    %s" % chkRef)
logger.info(" * Will build with:  %s" % ",".join(theComps))
logger.info(" * Will build flags: %s" % " ".join(theFlags))
logger.info(" * Will test with:   %s" % theTest)
logger.info(" * Will show stdout: %s" % str(showStd))

gitHash, gitTime, gitMsg = getCommitFromRef(dSource, chkRef)

logger.info("")
logger.info("Repository:")
logger.info(" * Git Hash: %s" % gitHash)
logger.info(" * Git Time: %s" % gitTime)
logger.info(" * Git Msg:  %s" % gitMsg)

# Check out the source

logger.info("")
logger.info("Checking Out SixTrack:")

workDir = path.join(dTemp,gitHash)
chdir(dTemp)
if path.isdir(workDir):
  stdOut, stdErr, exCode = sysCall("rm -rf %s" % gitHash)
  if exCode == 0:
    logger.info("Deleting folder: %s ... OK" % workDir)
  else:
    logger.error("Deleting folder: %s ... Failed" % workDir)
    exit(1)

mkdir(workDir)
chdir(workDir)

exCode = system("git clone %s ." % path.join(dSource,"SixTrack.git"))
exCode = system("git fetch origin %s:tmpbranch" % chkRef)
exCode = system("git checkout --detach %s" % gitHash)
exCode = system("mv lib lib.old")
exCode = system("ln -s %s lib" % dLibs)

logger.info("")
logger.info("Building SixTrack:")

bldPass = {}
for aComp in theComps:
  exCode = system("rm -rf build/")
  exCode = system("./cmake_six %s release %s" % (aComp," ".join(theFlags)))
  bldPass[aComp] = exCode == 0

logger.info("")
logger.info("Running Tests:")

bldDir  = path.join(workDir,"build")
tstPass = {}
for aBuild in listdir(bldDir):
  theBuild = path.join(bldDir,aBuild)
  if path.isdir(theBuild):
    logger.info("Entering in: %s" % aBuild)
    chdir(theBuild)
    exCode = system("ctest %s -j%d" % (theTest,nTest))
    tstPass[aBuild] = exCode == 0
# SixTrack_cmakesix_BUILD_TESTING_gfortran_release

logger.info("")
logger.info("="*100)
logger.info("")
logger.info("Build Summary:")
for aBuild in bldPass:
  if aBuild:
    bRes = "Passed"
  else:
    bRes = "Failed"
  logger.info(" * Build with %-72s : %s" % (aBuild,bRes))

logger.info("")
logger.info("Tests Summary:")
for aTest in tstPass:
  if aTest:
    bRes = "Passed"
  else:
    bRes = "Failed"
  tDesc = aTest[18:].replace("BUILD_TESTING","").replace("_"," ").strip()
  logger.info(" * Tests with %-72s : %s" % (tDesc,bRes))

logger.info("")
logger.info("="*100)
logger.info("")
