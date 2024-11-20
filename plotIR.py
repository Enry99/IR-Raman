#!/usr/bin/env python
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

# defining constants for the lorentzian smearing
epsilon = 1e-8
fwhm=15.0

class Lorentz(object): # inspired from Balint Aradi smearing procedure for DOS analysis in DFTB
  """Lorentzian smearing"""
  def __init__(self, gamma, center, coef):
    self._gamma = gamma
    self._center = center
    self._coef = coef    
  def __call__(self, xx):
    dx = xx - self._center
    return self._coef/(1+4*(dx**2)/((2*self._gamma)**2))

class Mode():
    """
    Structure for storing frequency (self.freq) and eigenvalues (self.values) of each mode. If the frequency is imaginary, it is set to be negative.
    """
    def __init__(self,text):
        tline = text.split('\n')
        if 'f/i' in tline[0]:
            fi_factor = -1.0
        else:
            fi_factor = 1.0
        self.freq=float(re.findall(r'Hz\s+(\d+\.\d+)\s+cm-1',tline[0])[0])*fi_factor
        tmplist = []
        for i in tline[2:]:
            if i.strip():
                tmplist.append([float(x.strip()) for x in i.split()])
        self.values = np.array(tmplist)

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

def parseEigenvectors(nIons,outcar):
    """
    Generates a list of modes (frequency, eigenvector) from eigenvectors.txt file
    """
    outcar_sp=outcar.split('SQRT(mass)')[1]
    EIG_NVIBS = len(re.findall('cm-1',outcar_sp))
    EIG_NROWS = (nIons+3)*EIG_NVIBS+3
    content = []
    for i in outcar_sp.split('\n'):
        if '-----------------------------------------------------------------------------------------' in i: break
        content.append(i)
    eigV = []
    buffer = ""
    for line in content[4:]:
        lst = line.strip()
        if not lst:
            if buffer != "":
                eigV.append(Mode(buffer))
                buffer = ""
        else:
            buffer += '{0}\n'.format(line)
    return eigV

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

def calcIntensities(nIons,eigV,polar):
    """
    Computes the IR intensities
    """
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

def normalize():
    """
    Normalizes the IR intensities
    """
    with open('exact.res.txt','r') as infile:
        values = np.array([y.strip().split() for y in infile.readlines() if y],dtype=float)
    maxval = max(values[:,2])
    values[:,2] /= maxval
    with open('results.txt','w') as outfile:
        for val in values:
            outfile.write('{0:>5d} {1:>10.5f} {2:10.5f}\n'.format(int(val[0]),val[1],val[2]))

if __name__ == "__main__":
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
    nIons = int(re.findall(nionsR,outcar)[0])
    print '\tParsing eigenvectors'
    eigV = parseEigenvectors(nIons,outcar)
    print '\n\n\tParsing Born charges'
    polar = parsePolar(nIons,outcar)
    print '\n\nCalculating intensities'
    print "="*len('Calculating intensities')
    calcIntensities(nIons,eigV,polar)
    print '\texact.res.txt written\n\nNormalizing'
    print "="*len('Normalizing')
    normalize()
    print '\tresults.txt written\n'
    plotIR()
    print '\nGenerating gnuplot script'
    print "="*len('Generating gnuplot script')
    with open('spectrum.gnu','w') as gnu:
        gnu.write("set term aqua enhanced font 'Helvetica,20' # comment for pdf output\n")
        gnu.write("#set term pdf color enhanced font 'Helvetica,20' size 16cm,12cm # uncom")
        gnu.write("ment for pdf output\n#set output 'spectrum.pdf' #uncomment for pdf output\n\n")
        gnu.write("\n#scales\n#set xrange[100:1000]\n#set yrange[0:1]\n\n")
        gnu.write("set xlabel 'Frequency (cm^{-1})'\n")
        gnu.write("set ylabel 'Normalized intensity'\n")
        gnu.write("p 'results.txt' u 2:3 w i t'Normalized IR spectrum','spectrum.txt' w l t'Lorentzian smearing'\n")
    print '\tspectrum.gnu written\n\nSuccessfull termination !'
    
