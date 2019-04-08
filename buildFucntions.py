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

import logging
import requests
import subprocess
from os import path
from datetime import datetime
from hashlib import md5

logger = logging.getLogger("SixTrackTestBuild")

# Set up logging
def setupLogging(dLog):
  logFmt = logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s  %(message)s",datefmt="%Y-%m-%d %H:%M:%S")

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
    logger.error("CCOV> Cannot parse covergae output")
  else:
    cLoc = (outLns[0].split())[-1]
    nLoc = (outLns[1].split())[-1]
    nTot = (outLns[2].split())[-1]
  return nTot, cLoc, nLoc

def sendData(theData):
  stUrl = "http://sixtrack.web.cern.ch/SixTrack/build_status.php"
  try:
    retVal = requests.post(stUrl, data=theData)
    logger.debug(" * Sending data: %s" % retVal.text)
  except:
    logger.error(" * Failed to send data to SixTrack website")

def genApiKey(keyFile):
  try:
    with open(keyFile,mode="r") as inFile:
      keySalt = inFile.read().strip()
  except:
    logger.error(" * Could not find API key file")
  return md5((datetime.now().strftime("%Y%m%d")+"-"+keySalt).encode("utf-8")).hexdigest()

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
