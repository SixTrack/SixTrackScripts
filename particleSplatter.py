#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import cm

nPart  = 10000000
emitX  = 1.0
betaX  = 1.0
alphaX = 0.3
gammaX = 1+alphaX**2 / betaX

sigmX  = np.array([[betaX, -alphaX], [-alphaX, gammaX]])
cholX  = np.linalg.cholesky(sigmX*emitX)

print("Input")
print("Emittance: %13.9f" % emitX)
print("Sigma:   [ %13.9f %13.9f ]" % (sigmX[0,0],sigmX[0,1]))
print("         [ %13.9f %13.9f ]" % (sigmX[1,0],sigmX[1,1]))
print("")

distX  = np.random.normal(0.0, 1.0, (nPart,2))
beamX  = np.dot(distX, cholX)

xPos   = beamX[:,1]
xAng   = beamX[:,0]

yPos   = np.zeros(nPart)
yAng   = np.zeros(nPart)

xCov = np.cov(xPos,xAng)
eX   = np.sqrt(np.linalg.det(xCov))
print("Generated Distribution")
print("Emittance: %13.9f" % eX)
print("Sigma:   [ %13.9f %13.9f ]" % (xCov[0,0],xCov[0,1]))
print("         [ %13.9f %13.9f ]" % (xCov[1,0],xCov[1,1]))
print("")

sqrtB = np.sqrt(betaX)
nAng  = np.random.normal(0.0, 1.0, nPart)
yAng  = nAng/sqrtB - alphaX/betaX*xPos

yPos  = (nAng - sqrtB*yAng)*sqrtB/alphaX

if nPart < 1001:
  for i in range(nPart):
    print("X: %13.6f Y: %13.6f X': %13.6f Y': %13.6f" % (xPos[i],yPos[i],xAng[i],yAng[i]))

yCov = np.cov(yPos,yAng)
eY   = np.sqrt(np.linalg.det(xCov))
print("Matched Distribution")
print("Emittance: %13.9f" % eY)
print("Sigma:   [ %13.9f %13.9f ]" % (yCov[0,0],yCov[0,1]))
print("         [ %13.9f %13.9f ]" % (yCov[1,0],yCov[1,1]))
print("")

dErr  = np.sum(yPos-xPos)/nPart
print("Average X-Y: %13.6e" % dErr)

# Plot
figOne = plt.figure(1,figsize=(10, 8),dpi=100)
figOne.clf()

xG = np.arange(-5.0, 5.0, 0.05)
yG = np.arange(-5.0, 5.0, 0.05)

bHist, xG, yG = np.histogram2d(xPos, xAng, bins=(xG, yG))
bHist = bHist/np.max(bHist)

xC = (xG[:-1] + xG[1:])/2
yC = (yG[:-1] + yG[1:])/2

xM, yM = np.meshgrid(xC, yC)

gOne = gridspec.GridSpec(3, 3)
currAx = plt.subplot(gOne[0:2, 0:2])
plt.contour(xM, yM, bHist, levels=[0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

pHist, pG = np.histogram(xPos, bins=200, density=True)
pC = (pG[:-1] + pG[1:])/2
currAx = plt.subplot(gOne[2, 0])
plt.step(pC,pHist,where="mid")
plt.xlabel("X")
plt.xlim(-5,5)
 
pHist, pG = np.histogram(xAng, bins=200, density=True)
pC = (pG[:-1] + pG[1:])/2
currAx = plt.subplot(gOne[2, 1])
plt.step(pC,pHist,where="mid")
plt.xlabel("X'")
plt.xlim(-5,5)

pHist, pG = np.histogram(yPos, bins=200, density=True)
pC = (pG[:-1] + pG[1:])/2
currAx = plt.subplot(gOne[0, 2])
plt.step(pC,pHist,where="mid")
plt.xlabel("Y")
plt.xlim(-5,5)
 
pHist, pG = np.histogram(yAng, bins=200, density=True)
pC = (pG[:-1] + pG[1:])/2
currAx = plt.subplot(gOne[1, 2])
plt.step(pC,pHist,where="mid")
plt.xlabel("Y'")
plt.xlim(-5,5)

plt.show(block=True)
