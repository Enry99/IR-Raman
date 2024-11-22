#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#############################################
#                                           #
#              plot IR                      #
#              S.Nenon 2015                 #
#                                           #
#############################################
# todo: clean



import sys
import os
import numpy as np
import re

from xphon.calculations.utils import get_modes_from_OUTCAR, read_input_parameters
from xphon import PHONONS_DIR

INCAR_TAGS = """
 LEPSILON=.TRUE.
"""

# defining constants for the lorentzian smearing
epsilon = 1e-8
fwhm=15.0

class Lorentz(object): # inspired from Balint Aradi smearing procedure for DOS analysis in DFTB
  #TODO: use the one from raman. That is normalized, this is not.
  """Lorentzian smearing"""
  def __init__(self, gamma, center, coef):
    self._gamma = gamma
    self._center = center
    self._coef = coef
  def __call__(self, xx):
    return self._coef/(1+((xx - self._center)**2)/((self._gamma)**2))



def readfile(file):
    """
    Transforms the input text file into an array
    """
    # get file content
    with open(file,'r') as f:
        content=[line.strip() for line in f.readlines()]
    # remove blank lines
    for i in range(len(content)):
        if content[i] == '':
            del(content[i])
    # generate array
    values=np.zeros((len(content),2))
    for i in range(len(content)):
        tmp= [float(x) for x in content[i].split()]
        values[i,0]=tmp[1]
        values[i,1]=tmp[2]
    return values

def plotIR():
    """
    Generates a lorentzian spectrum
    """
    gamma=fwhm/2.0
    print 'Parsing file'
    print "="*len('Parsing file')
    values=readfile('results.txt')
    print '\tdone...'
    min_freq=values[-1,0]
    max_freq=values[0,0]
    freq_step=(max_freq-min_freq)/1000.0
    print "\nInitial values"
    print "="*len("Initial values")
    print "\tMax. freq.: {0}".format(max_freq)
    print "\tMin. freq.: {0}".format(min_freq)
    print "\tFreq. step: {0} cm-1".format(freq_step)
    print "\nGenerating Lorentzians"
    print "="*len("Generating Lorentzians")
    print "\tFWHM: {0} cm-1".format(gamma*2)
    smearer=[]
    for i in values:
        smearer.append(Lorentz(gamma,i[0],i[1]))
    print '\tdone...'
    print "\nGenerating spectrum"
    print "="*len("Generating spectrum")
    nItem = 1000
    result = np.zeros((nItem, 2), dtype=float)
    freq = min_freq
    lasti=0
    for i in range(len(result)):
        sys.stdout.write("\r[{0:20s}]".format(int(float(i)/float(len(result))*20)*"#"))
        sum = 0.0
        for func in smearer:
            sum += func(freq)
        result[i,0] = freq
        result[i,1] = sum
        freq += freq_step
    with open('spectrum.txt','w') as spec:
        for i in result:
            if i[1] not in ['inf','nan']:
                spec.write("{0:.10f}  {1:.10f}\n".format(i[0],i[1]))
    print '\n\tspectrum.txt written'


def parsePolar(nIons,outcar):
    """
    Generates a list of arrays containing Born Charges from born.txt file
    """
    # ================== Get born Charges =====================
    bornLines = 4 * nIons + 1
    # get born charges
    outcar_sp=outcar.split('in |e|, cummulative output')[1]
    bCharges=[]
    outcar_lines = outcar_sp.split('\n')
    bCharges.extend(outcar_lines[2:bornLines+1])
    Polar = []
    buffer = ""
    start = False
    for line in bCharges:
        lst = line.strip()
        if 'ion' in lst:
            if start:
                pol = []
                for i in buffer.split('\n'):
                    if i.strip():
                        pol.append([float(x.strip()) for x in i.split()[1:]])
                Polar.append(np.array(pol))
                buffer = ""
            else:
                start = True
        else:
            buffer += '{0}\n'.format(line)
    pol = []
    for i in buffer.split('\n'):
        if i.strip():
            pol.append([float(x.strip()) for x in i.split()[1:]])
    Polar.append(np.array(pol))
    return Polar


def get_ir_intensities(nIons,eigV,polar):
    """
    Computes the IR intensities
    """

    #Formula: https://utheses.univie.ac.at/detail/9139#, (Eq. 2.51)
    with open('exact.res.txt','w') as outfile:
        for mm in range(len(eigV)):
            int = 0.0
            eigVals = eigV[mm].values
            freq = eigV[mm].freq
            for alpha in range(3):
                sumpol = 0.0
                for atom in range(nIons):
                    tmpval = eigVals[atom,3]*polar[atom][alpha,0]\
                    + eigVals[atom,4]*polar[atom][alpha,1]\
                    + eigVals[atom,5]*polar[atom][alpha,2]
                    sumpol += tmpval
                int += sumpol**2
            outfile.write('{0:03d} {1:.5f} {2:.5f}\n'.format(mm+1,freq,int))


def write_ir_spectrum():

    atoms, _, _, _ = read_input_parameters()
    natoms = len(atoms)

    if not os.path.isfile(f'{PHONONS_DIR}/OUTCAR'):
        sys.exit(f"OUTCAR file not found in {PHONONS_DIR}")


    print 'Opening OUTCAR file'
    print "="*len('Opening OUTCAR file')
    nionsR = re.compile(r'NIONS\s+=\s+(\d+)')
    try:
        with open('OUTCAR','r') as buffer:
            outcar=buffer.read()
    except:
        sys.exit('OUTCAR file not found. Please try again in the folder containing OUTCAR')
    # test born charges
    if not re.search('BORN',outcar):
        sys.exit('Born charges are not present in OUTCAR')
    natoms = int(re.findall(nionsR,outcar)[0])


    print(f"Reading eigenvectors from {PHONONS_DIR}/OUTCAR")
    modes_list = get_modes_from_OUTCAR(f'{PHONONS_DIR}/OUTCAR', natoms)

    print '\n\n\tParsing Born charges'
    polar = parsePolar(nIons,outcar)
    print '\n\nCalculating intensities'
    print "="*len('Calculating intensities')
    calcIntensities(nIons,eigV,polar)
    print '\texact.res.txt written\n\nNormalizing'

    print '\tresults.txt written\n'
    plotIR()

