#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""SixTrack Quick Build

  SixTrack Quick Build
 ======================
  Do a quick build and test of SixTrack
  By: Veronica Berglyd Olsen
      CERN (BE-ABP-HSS)
      Geneva, Switzerland

  This script will run builds and tests based on a fuzzy list of input parameters.
  These can be, in no particular order:

   * Compilers:         gfortran, ifort, nagfor
   * Build Types:       debug, release
   * Build Flags:       Any flag that is accepted by the CMake. BUILD_TESTING is implied.
   * Run Tests:         fast, medium, slow, fastmedium, gonuts (last one runs '-E prob')
   * Delete Work Dir:   clean, messy (for do clean up, and don't, respectively)
   * Show Build Output: buildout, nobuildout
   * Show Test Output:  testout, notestout
   * Show Output:       spammy, quiet (sets both of the above at the same time)

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
nTest = 14

setupLogging(dLog,True)

logger.info("*"*80)
logger.info("* Starting New Quick Build Session")
logger.info("*"*80)

mirrorRepo(dSource)

# Help message

theHelp = """
 So, you don't know what to do?
 This script will run builds and tests based on a fuzzy list of input parameters.
 These can be, in no particular order:
  * Compilers:         gfortran, ifort, nagfor
  * Build Types:       debug, release
  * Build Flags:       Any flag that is accepted by the CMake. BUILD_TESTING is implied.
  * Run Tests:         fast, medium, slow, fastmedium, gonuts (last one runs '-E prob')
  * Delete Work Dir:   clean, messy (for do clean up, and don't, respectively)
  * Show Build Output: buildout, nobuildout
  * Show Test Output:  testout, notestout
  * Show Output:       spammy, quiet (sets both of the above at the same time)
"""

# Parse arguments, but don't be difficult!

chkType  = "b"
chkRef   = "refs/heads/master"
theComps = []
theTypes = []
theFlags = []
theTest  = "-L fast"
buildOut = False
testOut  = True
doClean  = True

for inArg in sys.argv[1:]:
  if inArg[:2] == "b:":
    chkType = "b"
    chkRef  = "refs/heads/%s" % inArg[2:]
  elif inArg[:3] == "pr:":
    chkType = "pr"
    chkRef  = "refs/pull/%s/head" % inArg[3:]
  elif inArg[:4] == "tag:":
    chkType = "pr"
    chkRef  = "refs/tags/%s" % inArg[4:]
  elif inArg in ("gfortran","ifort","nagfor"):
    theComps.append(inArg)
  elif inArg in ("debug","release"):
    theTypes.append(inArg)
  elif inArg == "fast":
    theTest = "-L fast"
  elif inArg == "medium":
    theTest = "-L medium"
  elif inArg == "slow":
    theTest = "-L slow"
  elif inArg == "fastmedium":
    theTest = "-L \"fast|medium\""
  elif inArg == "gonuts":
    theTest = "-E prob"
  elif inArg in ("buildout","spammy"):
    buildOut = True
  elif inArg in ("nobuildout","quiet"):
    buildOut = False
  elif inArg in ("testdout","spammy"):
    testOut = True
  elif inArg in ("notestdout","quiet"):
    testOut = False
  elif inArg in "clean":
    doClean = True
  elif inArg in "messy":
    doClean = False
  elif inArg == inArg.upper():
    theFlags.append(inArg)
  elif inArg in ("help","-help","--help","-h","what","wtf","huh","why","butwhy","ffs","dafuq"):
    print(theHelp)
    exit(0)
  else:
    logger.error("Unrecognised argument '%s'" % inArg)
    print("")
    print(theHelp)
    exit(0)

if len(theComps) == 0:
  theComps = ["gfortran"]
if len(theTypes) == 0:
  theTypes = ["release"]

logger.info("")
logger.info("Arguments:")
logger.info(" * Will checkout:     %s" % chkRef)
logger.info(" * Will build with:   %s" % ",".join(theComps))
logger.info(" * Will build types:  %s" % ",".join(theTypes))
logger.info(" * Will build flags:  %s" % " ".join(theFlags))
logger.info(" * Will test with:    %s" % theTest)
logger.info(" * Will clean up:     %s" % str(doClean))
logger.info(" * Will build output: %s" % str(buildOut))
logger.info(" * Will test output:  %s" % str(testOut))

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
exCode = system("rm -rf build/")
for aComp in theComps:
  for aType in theTypes:
    cmdStr = "./cmake_six %s %s BUILD_TESTING %s" % (aComp,aType," ".join(theFlags))
    if not buildOut:
      cmdStr += " > /dev/null"
    logger.info("Running: %s" % cmdStr)
    exCode = system(cmdStr)
    bldPass[aComp+" "+aType] = exCode == 0

logger.info("")
logger.info("Running Tests:")

bldDir  = path.join(workDir,"build")
tstPass = {}
for aBuild in listdir(bldDir):
  theBuild = path.join(bldDir,aBuild)
  if path.isdir(theBuild):
    logger.info("Entering in: %s" % aBuild)
    chdir(theBuild)
    cmdStr = "ctest %s -j%d" % (theTest,nTest)
    if not testOut:
      cmdStr += " > /dev/null"
    logger.info("Running: %s" % cmdStr)
    exCode = system(cmdStr)
    tstPass[aBuild] = exCode == 0

logger.info("")
logger.info(" Summary:")
logger.info("="*80)
logger.info("")
for aBuild in bldPass:
  if aBuild:
    bRes = "   Passed"
  else:
    bRes = "***Failed"
  bDesc = "Build: %s %s" % (aBuild," ".join(theFlags))
  logger.info(" %s %s%s" % (bDesc,"."*(68-len(bDesc)),bRes))

for aTest in tstPass:
  if aTest:
    bRes = "   Passed"
  else:
    bRes = "***Failed"
  tDesc = "Test: %s" % (aTest[18:].replace("BUILD_TESTING","").replace("_"," ").strip())
  logger.info(" %s %s%s" % (tDesc,"."*(68-len(tDesc)),bRes))

chdir(workDir)
if path.isdir(workDir) and doClean:
  stdOut, stdErr, exCode = sysCall("rm -rf %s" % gitHash)

logger.info("")
logger.info("="*80)
logger.info("")
