#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

nPart = 1000000

nRnd = np.random.uniform(0.0, 1.0, nPart)
pDist = np.zeros(nPart)

cMax = 2.0
cMin = 0.0

# CCC = ONEONE -EXP( -(CMAX+CMIN)*(CMAX-CMIN)/TWOTWO )
# BOXMUL = SQRT( CMIN**2 -TWOTWO*LOG( ONEONE-CCC*RAND() ) )

cFac = 1.0 - np.exp(-(cMax+cMin)*(cMax-cMin)/2.0)
# for i in range(nPart):
#   pDist[i] = np.sqrt(cMin**2 - 2.0*np.log(1.0-cFac*nRnd[i]))

# CCC = ONEONE -EXP( -CMAX**2/TWOTWO )
# BOXMUL = SQRT( -TWOTWO*LOG( ONEONE-CCC*RAND() ) )
cFac = 1.0 - np.exp(-cMax**2/2.0)
for i in range(int(nPart/2)):
  rad = np.sqrt(-2.0*np.log(1.0-cFac*nRnd[2*i]))
  # rad = np.sqrt(cMin**2 - 2.0*np.log(1.0-cFac*nRnd[2*i]))
  # rad = np.sqrt(1.0-2.0*np.log(nRnd[2*i]))
  pDist[2*i]   = rad*np.cos(2.0*np.pi*nRnd[2*i+1])
  pDist[2*i+1] = rad*np.sin(2.0*np.pi*nRnd[2*i+1])

# Plot
figOne = plt.figure(1,figsize=(10, 8),dpi=100)
figOne.clf()

pHist, pG = np.histogram(pDist, bins=200, density=True)
pC = (pG[:-1] + pG[1:])/2
plt.step(pC,pHist,where="mid")

plt.show(block=True)
