#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""SixTrack Nightly Builds

  SixTrack Nightly Builds
 =========================
  Loop through and build SixTrack with various compilers and flags
  By: Veronica Berglyd Olsen
      CERN (BE-ABP-HSS)
      Geneva, Switzerland

  Package Dependencies:
   - gcovr : for generating the coverage report in html

"""

import sys
import time
import logging
from os import path, chdir, mkdir, listdir, system
from datetime import datetime
from buildFunctions import *

logger = logging.getLogger("SixTrackTestBuild")

##
#  Settings
##

dRoot    = "/scratch/TestBuild"
dLog     = "/scratch/TestBuild/Logs"
dSource  = "/scratch/TestBuild/Source/SixTrack"
dResults = "/scratch/TestBuild/Results"
testTime = "/scratch/TestBuild/Timing"
testCov  = "/scratch/TestBuild/Coverage"

nBld  = 8
nTest = 10
nCov  = 14

theCompilers = {
  "g" : {"exec" : "gfortran", "enabled" : True, "version": "--version"},
  "i" : {"exec" : "ifort",    "enabled" : True, "version": "--version"},
  "n" : {"exec" : "nagfor",   "enabled" : True, "version": "-V"}
}

ctFF = "-L 'fast'"
ctFE = "-L 'fast|error'"
ctFM = "-L 'fast|medium|error'"
ctNS = "-E 'prob'"
ctNE = "-E 'prob|error'"

theBuilds = {
  # Label                 Compilers      Options                             Tests (rel/dbg)
  "Standard Single"    : [["g","i","n"], "32BITM -64BITM -CRLIBM -DISTLIB",  [None,None]],
  "Standard Double"    : [["g","i","n"], "",                                 [ctNS,ctNE]],
  "Standard Quad"      : [["g","i","n"], "128BITM -64BITM -CRLIBM -DISTLIB", [None,None]],
  "Standard AVX2"      : [["g","i","n"], "AVX2",                             [ctNE,ctFF]],
  "Round Up"           : [["g","i","n"], "-ROUND_NEAR ROUND_UP",             [None,None]],
  "Round Down"         : [["g","i","n"], "-ROUND_NEAR ROUND_DOWN",           [None,None]],
  "Round Zero"         : [["g","i","n"], "-ROUND_NEAR ROUND_ZERO",           [None,None]],
  "Checkpoint/Restart" : [["g","i","n"], "CR",                               [ctNE,ctFF]],
  "BOINC Support"      : [["g","i","n"], "CR BOINC -STATIC",                 [ctNE,ctFF]],
  "Fortran I/O"        : [["g","i","n"], "FIO",                              [ctFF,ctFF]],
  "HDF5"               : [["g"],         "HDF5",                             [None,None]],
  "Pythia"             : [["g","i","n"], "PYTHIA",                           [None,None]],
  "Beam-Gas"           : [["g","i","n"], "BEAMGAS",                          [None,None]],
# "Fluka Coupling"     : [["g","i","n"], "FLUKA",                            [None,None]],
  "Merlin Scattering"  : [["g","i","n"], "MERLINSCATTER",                    [None,None]],
  "Geant4 Scattering"  : [["g","i","n"], "G4COLLIMATION -STATIC -ZLIB",      [None,None]],
  "DEBUG Flag"         : [["g","i","n"], "DEBUG",                            [None,None]],
}

# theBuilds = {
#   "Standard Double" : [["g"], "", [ctFF,ctFF]],
# }

setupLogging(dLog)

logger.info("*"*80)
logger.info("* Starting New Test Build Session")
logger.info("*"*80)

# Get compiler versions
cExecs = []
for bComp in theCompilers.keys():
  cExecs.append(theCompilers[bComp]["exec"])
  cStart = time.time()
  stdOut, stdErr, exCode = sysCall("%s %s" % (theCompilers[bComp]["exec"], theCompilers[bComp]["version"]))
  cEnd   = time.time()
  tmpLn  = (stdOut+stdErr).split("\n")
  theCompilers[bComp]["version"] = tmpLn[0]
  theCompilers[bComp]["enabled"] = exCode == 0
  if exCode == 0:
    logger.info("Using %s: %s" % (theCompilers[bComp]["exec"],theCompilers[bComp]["version"]))
  else:
    logger.error("There is a problem with the %s compiler" % theCompilers[bComp]["exec"])
    logWrap("COMPILER",stdOut,stdErr,exCode)
  if cEnd - cStart > 180:
    logger.error("There is a problem with the %s compiler - too slow to execute" % theCompilers[bComp]["exec"])
    theCompilers[bComp]["enabled"] = False

# Repository
chdir(dSource)
logger.info("Entering directory: %s" % dSource)
logger.info("Updating source ...")

stdOut, stdErr, exCode = sysCall("git remote update")
logWrap("GIT",stdOut,stdErr,exCode)

stdOut, stdErr, exCode = sysCall("git checkout master")
logWrap("GIT",stdOut,stdErr,exCode)

stdOut, stdErr, exCode = sysCall("git pull")
logWrap("GIT",stdOut,stdErr,exCode)

logger.info("Done!")

# Meta Data

stdOut, stdErr, exCode = sysCall("git log -n1 --pretty=format:%H")
gitHash  = stdOut.strip()
prevHash = "None"
logger.info("Current git hash: %s" % gitHash)

stdOut, stdErr, exCode = sysCall("git show -s --format=%%ci %s | tail -n1" % gitHash)
gitTime = (stdOut.strip())[:19]
logger.info("Commit date: %s" % gitTime)

if path.isfile(path.join(dRoot,"prevHash.dat")):
  with open(path.join(dRoot,"prevHash.dat"),mode="r") as hFile:
    prevHash = hFile.read()
with open(path.join(dRoot,"prevHash.dat"),mode="w") as hFile:
  hFile.write(gitHash)

logger.info("Previous git hash: %s" % prevHash)
if gitHash == prevHash:
  logger.info("No change to origin/master since last time. Exiting.")
  logger.info("")
  exit(0)

# We're Running This!

# Stop BOINC
exCode = system("boinccmd --set_run_mode never && boinccmd --set_gpu_mode never")
logger.info("Disabling BOINC: %d" % exCode)

stdOut, stdErr, exCode = sysCall("uname -rsm")
runOS = stdOut.strip()
logger.info("Running on: %s" % runOS)

stVers = getSixTrackVersion(dSource)
logger.info("SixTrack Version: %s" % stVers)

tJobs = []
for bBuild in theBuilds:
  if theBuilds[bBuild][2][0] is not None or theBuilds[bBuild][2][1] is not None:
    tJobs.append(bBuild)

theMeta = {
  "action"    : "meta",
  "runtime"   : time.time(),
  "hash"      : gitHash,
  "ctime"     : gitTime,
  "os"        : runOS,
  "stvers"    : stVers,
  "complist"  : ",".join(cExecs),
  "buildlist" : ",".join(theBuilds.keys()),
  "testlist"  : ",".join(tJobs),
  "endtime"   : -1,
  "coverage"  : False,
  "covloc"    : 0,
  "ncovloc"   : 0,
  "totloc"    : 0,
  "prevcov"   : "",
}
writeResults(theMeta, dResults, "meta")

##
#  Build Submodules
##

stdOut, stdErr, exCode = sysCall("./buildLibraries.sh boinc")
if exCode == 0:
  logger.info("BOINC build successful")
else:
  logger.info("BOINC build failed")

stdOut, stdErr, exCode = sysCall("./buildLibraries.sh hdf5")
if exCode == 0:
  logger.info("HDF5 build successful")
else:
  logger.info("HDF5 build failed")

stdOut, stdErr, exCode = sysCall("./buildLibraries.sh pythia")
if exCode == 0:
  logger.info("Pythia build successful")
else:
  logger.info("Pythia build failed")

##
#  Builds
##

logger.info("Executing build queue ...")
bCount   = 0
cTests   = []
cCleanup = []
theTypes = ["Release","Debug"]
for bComp in theCompilers.keys():
  for iType in range(2):
    for bBuild in theBuilds.keys():

      bldExec = theCompilers[bComp]["exec"]
      bldType = theTypes[iType]
      bldComp = theBuilds[bBuild][0]
      bldOpts = theBuilds[bBuild][1]
      testCmd = theBuilds[bBuild][2][iType]
      bCount += 1

      # Build Command
      sysCmd = "./cmake_six %s %s %s" % (bldExec,bldType.lower(),bldOpts)
      sysCmd = sysCmd.strip()
      if testCmd is not None:
        sysCmd += " BUILD_TESTING"

      logger.info("Build %03d: %s" % (bCount, sysCmd))

      # Results Record
      bStatus = {
        "action"    : "build",
        "timestamp" : time.time(),
        "hash"      : gitHash,
        "compiler"  : bldExec,
        "type"      : bldType,
        "build"     : False,
        "flag"      : bBuild,
        "command"   : sysCmd,
        "buildno"   : bCount,
        "success"   : False,
        "path"      : "",
        "testcmd"   : "",
        "buildtime" : -1,
      }

      # Check if Should Be Built
      if bComp in bldComp and theCompilers[bComp]["enabled"]:

        # Execute Build
        tStart = time.time()
        stdOut, stdErr, exCode = sysCall(sysCmd)
        dumpStdFiles(stdOut,stdErr,"build")
        tEnd = time.time() - tStart

        # Parse Results
        if exCode == 0:
          logger.info(" * Build Successful!")
          bPath = cmakeSixReturn(stdOut,stdErr)
          stdOut, stdErr, bexCode = sysCall("mv std*.log %s" % bPath)
          logger.info(" * Executable in: %s" % bPath)
          bStatus["success"] = True
          bStatus["path"]    = bPath
          if testCmd is not None:
            bStatus["testcmd"] = "ctest %s -j%d" % (testCmd,nTest)
            logger.info(" * Adding executable to test queue")
            cTests.append(bStatus)
          else:
            cCleanup.append(bPath)
        else:
          logger.warning(" * Build Failed!")

        bStatus["build"]     = True
        bStatus["buildtime"] = tEnd
  
      else:
        logger.info(" * Build Skipped")

      # Send Report
      writeResults(bStatus, dResults, hashIt("build",bStatus["command"]))

logger.info("Build queue done!")

##
#  Tests
##

logger.info("Executing test queue ...")
tCount = 0
ntTot  = 0
ntPass = 0
ntFail = 0
for toRun in cTests:
  tCount += 1
  chdir(path.join(dSource,toRun["path"]))
  logger.info("Test %03d: %s" % (tCount, toRun["path"]))
  logger.info(" * Command: %s" % (toRun["testcmd"]))
  tStatus = toRun
  tStatus["action"]    = "test"
  tStatus["testno"]    = tCount
  tStatus["timestamp"] = time.time()

  tStart = time.time()
  stdOut, stdErr, exCode = sysCall(toRun["testcmd"])
  dumpStdFiles(stdOut,stdErr,"test")
  tEnd = time.time() - tStart
  tStatus["testtime"] = tEnd

  chdir(dSource)
  if exCode == 0:
    logger.info(" * Tests Passed!")
    tStatus["passtests"] = True
    cCleanup.append(toRun["path"])
  else:
    logger.warning(" * Tests Failed!")
    tStatus["passtests"] = False

  nTotal, nPass, nFail, tFail = ctestResult(stdOut,stdErr)
  for failName in tFail:
    logger.warning(" * Failed: %s" % failName)

  tStatus["failed"] = ", ".join(tFail)
  tStatus["ntotal"] = nTotal
  tStatus["npass"]  = nPass
  tStatus["nfail"]  = nFail

  ntTot  += nTotal
  ntPass += nPass
  ntFail += nFail

  # Send Report
  writeResults(tStatus, dResults, hashIt("test",tStatus["command"]))

  # Log Timing
  for tItem in listdir(path.join(toRun["path"],"test")):
    if tItem[:6] == "error_":
      continue
    tPath = path.join(toRun["path"],"test",tItem)
    if path.isdir(tPath):
      execTime = getExecTime(tPath)
      if execTime is None:
        continue
      timPath = path.join(testTime,tItem+".log")
      if tItem in tFail:
        tRes = "Failed"
      else:
        tRes = "Passed"
      with open(timPath,mode="a") as outFile:
        tStamp = datetime.fromtimestamp(tStatus["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        outFile.write("[%s]  %40s  %19s  %14s  %6s  Build: %s\n" % (
          tStamp,
          gitHash,
          gitTime,
          execTime,
          tRes,
          tStatus["command"][12:]
        ))

logger.info("Test queue done!")

##
#  Coverage
##

logger.info("Beginning coverage ...")

chdir(dSource)
sysCmd = "./cmake_six gfortran release BUILD_TESTING COVERAGE"
logger.info("Coverage Build: %s" % sysCmd)
tStart = time.time()
stdOut, stdErr, bexCode = sysCall(sysCmd)
dumpStdFiles(stdOut,stdErr,"build")
tEnd = time.time() - tStart

if bexCode == 0:
  logger.info(" * Coverage Build Successful!")
  bPath = cmakeSixReturn(stdOut,stdErr)
  stdOut, stdErr, bexCode = sysCall("mv std*.log %s" % bPath)
  logger.info(" * Executable in: %s" % bPath)

  # Run Tests
  chdir(path.join(dSource,bPath))
  sysCmd = "ctest -E prob -j%d" % nCov
# sysCmd = "ctest -R dynk -j%d" % nCov
  logger.info("Coverage Test: %s" % sysCmd)
  tStart = time.time()
  stdOut, stdErr, texCode = sysCall(sysCmd)
  dumpStdFiles(stdOut,stdErr,"test")
  tEnd = time.time() - tStart

  if texCode == 0:
    logger.info(" * Coverage Tests Completed!")
    # cCleanup.append(bPath)
  else:
    logger.warning(" * Coverage Tests Failed!")

  # Compute Coverage w/CMake
  sysCmd = "ctest -D NightlyCoverage | tail -n4"
  logger.info("Calculating Coverage: %s" % sysCmd)
  stdOut, stdErr, cexCode = sysCall(sysCmd)
  dumpStdFiles(stdOut,stdErr,"coverage")

  nTot, cLoc, nLoc = ctestCoverage(stdOut,stdErr)
  theMeta["coverage"] = True
  theMeta["covloc"]   = cLoc
  theMeta["ncovloc"]  = nLoc
  theMeta["totloc"]   = nTot
  rCov = 100*int(cLoc)/int(nTot)

  logger.info(" * Coverage is: %6.2f %%" % rCov)

  if path.isfile(path.join(dRoot,"prevCoverage.dat")):
    with open(path.join(dRoot,"prevCoverage.dat"),mode="r") as cFile:
      theMeta["prevcov"] = cFile.read()
  with open(path.join(dRoot,"prevCoverage.dat"),mode="w") as cFile:
    cFile.write("%s;%s;%s;%s" % (gitHash,nTot,cLoc,nLoc))
  with open(path.join(dRoot,"Coverage.log"),mode="a") as outFile:
    outFile.write("%40s  %19s  %8s  %8s  %8s  %7.3f\n" % (
      gitHash,gitTime,cLoc,nLoc,nTot,rCov
    ))

  # Create HTML Report w/gcovr
  chdir(path.join(dSource,bPath))
  cPath = path.join(testCov,"html")
  if not path.isdir(cPath):
    mkdir(cPath)
  stdOut, stdErr, exCode = sysCall("rm %s/*" % cPath)
  stdOut, stdErr, exCode = sysCall("echo \"%s\" > %s/githash.txt" % (gitHash,cPath))
  stdOut, stdErr, exCode = sysCall("echo \"%s\" >> %s/githash.txt" % (gitTime,cPath))
  stdOut, stdErr, exCode = sysCall(
    "gcovr -o %s/index.html -p -s --html-details --html-medium-threshold 50 --html-high-threshold 80 --html-title SixTrack" % cPath
  )
  if exCode == 0:
    logger.info(" * Generated Report!")
    logWrap("GCOVR", stdOut, stdErr, exCode)
    chdir(testCov)
    stdOut, stdErr, exCode = sysCall("tar -czf %s.tgz html" % gitHash)
  else:
    logger.warning(" * Generating Report Failed!")

else:
  logger.warning(" * Coverage Build Failed!")

chdir(dSource)
logger.info("Coverage done!")

##
#  Memory Usage
##

logger.info("Beginning memory usage ...")

chdir(dSource)
sysCmd = "./cmake_six gfortran release BUILD_TESTING MEMUSAGE"
logger.info("MemUsage Build: %s" % sysCmd)
tStart = time.time()
stdOut, stdErr, bexCode = sysCall(sysCmd)
dumpStdFiles(stdOut,stdErr,"build")
tEnd = time.time() - tStart

if bexCode == 0:
  logger.info(" * Memory Usage Build Successful!")
  bPath = cmakeSixReturn(stdOut,stdErr)
  stdOut, stdErr, bexCode = sysCall("mv std*.log %s" % bPath)
  logger.info(" * Executable in: %s" % bPath)

  # Run Tests
  chdir(path.join(dSource,bPath))
  sysCmd = "ctest -E 'prob|error' -j%d" % nCov
# sysCmd = "ctest -R dynk -j%d" % nCov
  logger.info("Memory Usage Test: %s" % sysCmd)
  tStart = time.time()
  stdOut, stdErr, texCode = sysCall(sysCmd)
  dumpStdFiles(stdOut,stdErr,"test")
  tEnd = time.time() - tStart

  if texCode == 0:
    logger.info(" * Memory Usage Tests Completed!")
    cCleanup.append(bPath)
  else:
    logger.warning(" * Memory Usage Tests Failed!")

  # Compute Memory Usage
  for tItem in listdir("test"):
    tPath = path.join("test",tItem)
    if path.isdir(tPath):
      memHWM   = getSimMeta(tPath,"Exec_VmHWM[MiB]")
      memPeak  = getSimMeta(tPath,"Exec_VmPeak[MiB]")
      memAlloc = getSimMeta(tPath,"PeakDynamicMemAlloc[MiB]")
      if memHWM is None and memPeak is None and memAlloc is None:
        continue
      with open(path.join(dRoot,"MemUsage.log"),mode="a") as outFile:
        outFile.write("%40s  %19s  %-40s  %12s  %12s  %12s\n" % (
          gitHash,gitTime,tItem,memAlloc,memHWM,memPeak
        ))

else:
  logger.warning(" * Memory Usage Build Failed!")

chdir(dSource)
logger.info("Memory usage done!")

##
#  Cleanup
##

logger.info("Beginning cleanup ...")
for rPath in cCleanup:
  stdOut, stdErr, exCode = sysCall("rm -r %s" % rPath)
  if exCode == 0:
    logger.info("Deleting: %s ... OK" % rPath)
  else:
    logger.info("Deleting: %s ... Failed" % rPath)
logger.info("Cleanup done!")

##
#  Finish
##

theMeta["endtime"] = time.time()
writeResults(theMeta, dResults, "meta")

with open(path.join(dRoot,"Builds.log"),mode="a") as outFile:
  outFile.write("%40s  %19s  %-10s  %19s  %19s  %5d  %5d  %5d  %5d  %5d  %s\n" % (
    gitHash,gitTime,stVers,
    datetime.fromtimestamp(theMeta["runtime"]).strftime("%Y-%m-%d %H:%M:%S"),
    datetime.fromtimestamp(theMeta["endtime"]).strftime("%Y-%m-%d %H:%M:%S"),
    bCount,tCount,
    ntTot,ntPass,ntFail,
    theMeta["os"]
  ))

# Start BOINC
exCode = system("boinccmd --set_run_mode auto && boinccmd --set_gpu_mode auto")
logger.info("Enabling BOINC: %d" % exCode)

logger.info("All Done!")
logger.info("")
