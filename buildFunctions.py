#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""SixTrack Nightly Builds

  SixTrack Nightly Builds
 =========================
  Loop through and build SixTrack with various compilers and flags
  By: Veronica Berglyd Olsen
      CERN (BE-ABP-HSS)
      Geneva, Switzerland

"""

import json
import logging
import hashlib
import requests
import subprocess
from os import path, chdir, getcwd, system
from datetime import datetime

logger = logging.getLogger("SixTrackTestBuild")

# Set up logging
def setupLogging(dLog,fPlain=False):
  if fPlain:
    logFmt = logging.Formatter(fmt="%(message)s")
  else:
    logFmt = logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s  %(message)s",datefmt="%Y-%m-%d %H:%M:%S")

  if not fPlain:
    fHandle = logging.FileHandler(dLog+"/testBuildSixTrack-"+datetime.now().strftime("%Y-%m")+".log")
    fHandle.setLevel(logging.DEBUG)
    fHandle.setFormatter(logFmt)
    logger.addHandler(fHandle)

  cHandle = logging.StreamHandler()
  cHandle.setLevel(logging.DEBUG)
  cHandle.setFormatter(logFmt)
  logger.addHandler(cHandle)

  logger.setLevel(logging.DEBUG)

# Wrapper function for system calls
def sysCall(callStr):
  sysP = subprocess.Popen([callStr], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  stdOut, stdErr = sysP.communicate()
  return stdOut.decode("utf-8"), stdErr.decode("utf-8"), sysP.returncode

# Command line output wrapper
def logWrap(outTag, stdOut, stdErr, exCode):
  outLns = stdOut.split("\n")
  errLns = stdErr.split("\n")
  for outLn in outLns:
    if outLn.strip() == "":
      continue
    logger.debug("%s> %s" % (outTag, outLn))
  if exCode is not 0:
    for errLn in errLns:
      if errLn.strip() == "":
        continue
      logger.error("%s> %s" % (outTag, errLn))
    logger.error("%s> Exited with code %d" % (outTag, exCode))
    exit(1)

def cmakeSixReturn(stdOut, stdErr):
  outLns = stdOut.split("\n")
  errLns = stdErr.split("\n")
  bPath  = ""
  if len(outLns) > 1:
    tmpData = outLns[-2].split()
    if len(tmpData) > 0:
      bPath = tmpData[-1]
  return bPath

def ctestReturn(stdOut, stdErr):
  outLns  = stdOut.split("\n")
  tFailed = ""
  if len(outLns) <= 2:
    logger.debug("CTEST> %s" % outLns[-1])
  else:
    atSum  = False
    atFail = False
    for outLn in outLns:
      outLn = outLn.strip()
      if outLn == "":
        atSum = True
        continue
      if not atSum:
        continue
      if not outLn == "":
        logger.debug("CTEST> %s" % outLn.strip())
      if outLn.strip() == "The following tests FAILED:":
        atFail = True
        continue
      if atFail:
        splFail = outLn.split()
        if len(splFail) == 4:
          if splFail[3] == "(Failed)":
            tFailed += splFail[2]+", "
    if atFail:
      tFailed = tFailed[:-2]
  return tFailed

def ctestResult(stdOut, stdErr):
  outLns = stdOut.split("\n")
  nTotal = 0
  nPass  = 0
  nFail  = 0
  tFail  = []
  if len(outLns) <= 2:
    logger.debug("CTEST> %s" % outLns[-1])
  else:
    for outLn in outLns:
      outBit = outLn.strip().replace("*"," ").split()
      if len(outBit) < 6:
        continue
      if outBit[1] != "Test" or outBit[2][:1] != "#":
        continue
      nTotal += 1
      if outBit[5] == "Passed":
        nPass += 1
      if outBit[5] == "Failed":
        nFail += 1
        tFail.append(outBit[3])
  return nTotal, nPass, nFail, tFail

def ctestCoverage(stdOut,stdErr):
  outLns = stdOut.split("\n")
  cLOC = 0
  nLOC = 0
  nTot = 1
  if len(outLns) < 3:
    logger.error("CCOV> Cannot parse coverage output")
  else:
    cLoc = (outLns[0].split())[-1]
    nLoc = (outLns[1].split())[-1]
    nTot = (outLns[2].split())[-1]
  return nTot, cLoc, nLoc

def writeResults(theData, theTarget, theLabel):
  try:
    with open("%s/%s.json" % (theTarget, theLabel), mode="w+") as outFile:
      json.dump(theData, outFile)
    logger.debug(" * Writing data for SixTrack website")
  except Exception as e:
    logger.error(" * Failed to write data for SixTrack website")
    logger.error(str(e))

def sendData(theData):
  stUrl = "http://sixtrack.web.cern.ch/SixTrack/build_status.php"
  try:
    retVal = requests.post(stUrl, data=theData)
    logger.debug(" * Sending data: %s" % retVal.text)
  except:
    logger.error(" * Failed to send data to SixTrack website")

def hashIt(theType, theCommand):
  return "%s_%s" % (theType, hashlib.md5(theCommand.encode()).hexdigest())

def getExecTime(tPath):
  simTime = path.join(tPath,"sim_time.dat")
  if not path.isfile(simTime):
    return None
  with open(simTime,mode="r") as tFile:
    for tLine in tFile:
      if len(tLine) < 49:
        continue
      tName = tLine[:32].strip()
      tVal  = tLine[35:49].strip()
      if tName == "Stamp_BeforeExit":
        return tVal
  return "Unknown"

def getSimMeta(mPath, mValue):
  simMeta = path.join(mPath,"sim_meta.dat")
  if not path.isfile(simMeta):
    return None
  with open(simMeta,mode="r") as mFile:
    for mLine in mFile:
      if len(mLine) < 50:
        continue
      mName = mLine[:32].strip()
      mVal  = mLine[35:50].strip()
      if mName == mValue:
        return mVal
  return "Unknown"

def dumpStdFiles(stdOut,stdErr,fName):
  with open("stdout_"+fName+".log",mode="w") as outFile:
    outFile.write(stdOut)
  with open("stderr_"+fName+".log",mode="w") as outFile:
    outFile.write(stdErr)
  return

def getSixTrackVersion(dSource):
  stdOut, stdErr, exCode = sysCall("cat %s | grep 'version = '" % path.join(dSource,"source","version.f90"))
  tmpLn = stdOut.strip().split()
  if len(tmpLn) > 0:
    return tmpLn[-1].replace("\"","")
  else:
    return "Unknown"

def mirrorRepo(dSource):
  """Create a mirror of the repository
  """
  mirrorPath = path.join(dSource,"SixTrack.git")
  workingDir = getcwd()
  chdir(dSource)

  if path.isdir(mirrorPath):
    chdir(mirrorPath)
    logger.info("Updating the SixTrack repository ...")
    stdOut, stdErr, exCode = sysCall("git remote update")
  else:
    logger.info("Cloning the SixTrack repository")
    exCode = system("git clone https://github.com/SixTrack/SixTrack.git --mirror")
    if exCode != 0:
      endExec("Failed to clone SixTrack repository")
    chdir(mirrorPath)

  chdir(workingDir)

  return

def getCommitFromRef(dSource, gitRef):
  """Get the commit hash for a given ref
  """
  mirrorPath = path.join(dSource,"SixTrack.git")
  workingDir = getcwd()
  chdir(mirrorPath)

  stdOut, stdErr, exCode = sysCall("git show-ref %s" % gitRef)
  if exCode == 0:
    gitHash = stdOut[0:40]
  else:
    logger.error("Unknown ref '%s'" % gitRef)
    return gitHash, "", ""
  stdOut, stdErr, exCode = sysCall("git show -s --format=%%ci %s | tail -n1" % gitHash)
  gitTime = stdOut.strip()
  stdOut, stdErr, exCode = sysCall("git log --format=%%B -n 1 %s | head -n1" % gitHash)
  gitMsg = stdOut.strip()

  chdir(workingDir)

  return gitHash, gitTime, gitMsg

