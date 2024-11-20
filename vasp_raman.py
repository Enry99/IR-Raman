#!/usr/bin/env python
#
# vasp_raman.py v. 0.6.0
#
# Raman off-resonant activity calculator
# using VASP as a back-end.
#
# Contributors: Alexandr Fonari (Georgia Tech)
# Shannon Stauffer (UT Austin)
#
# URL: http://raman-sc.github.io
#
# MIT license, 2013 - 2016
#


import re
import sys
import json

from ase.io import read, write


def get_modes_from_OUTCAR(outcar_filename, natoms):
    from math import sqrt
    eigvals = [ 0.0 for _ in range(natoms*3) ]
    eigvecs = [ 0.0 for _ in range(natoms*3) ]
    norms   = [ 0.0 for _ in range(natoms*3) ]

    with open(outcar_filename, 'r') as outcar_fh:

        outcar_fh.seek(0) # just in case
        while True:
            line = outcar_fh.readline()
            if not line:
                break

            if "Eigenvectors after division by SQRT(mass)" in line:
                outcar_fh.readline() # empty line
                outcar_fh.readline() # Eigenvectors and eigenvalues of the dynamical matrix
                outcar_fh.readline() # ----------------------------------------------------
                outcar_fh.readline() # empty line

                for i in range(natoms*3): # all frequencies should be supplied, regardless of those requested to calculate
                    outcar_fh.readline() # empty line
                    p = re.search(r'^\s*(\d+).+?([\.\d]+) cm-1', outcar_fh.readline())
                    eigvals[i] = float(p.group(2))

                    outcar_fh.readline() # X         Y         Z           dx          dy          dz
                    eigvec = []

                    for _ in range(natoms):
                        tmp = outcar_fh.readline().split()

                        eigvec.append([ float(tmp[x]) for x in range(3,6) ])

                    eigvecs[i] = eigvec
                    norms[i] = sqrt( sum( [abs(x)**2 for sublist in eigvec for x in sublist] ) )

                return list(reversed(eigvals)), list(reversed(eigvecs)), list(reversed(norms))

        #if we are here, something went wrong
        raise RuntimeError("Couldn't find 'Eigenvectors after division by SQRT(mass)' in OUTCAR. Use 'NWRITE=3' in INCAR.")


def get_epsilon_from_OUTCAR(outcar_filename):
    epsilon = []

    with open(outcar_filename, 'r') as outcar_fh:
        outcar_fh.seek(0) # just in case
        while True:
            line = outcar_fh.readline()
            if not line:
                break

            if "MACROSCOPIC STATIC DIELECTRIC TENSOR" in line:
                outcar_fh.readline()
                epsilon.append([float(x) for x in outcar_fh.readline().split()])
                epsilon.append([float(x) for x in outcar_fh.readline().split()])
                epsilon.append([float(x) for x in outcar_fh.readline().split()])
                return epsilon

        raise RuntimeError("Couldn't find dielectric tensor in OUTCAR")


if __name__ == '__main__':
    from math import pi
    import shutil
    import os
    import datetime

    print("    Raman off-resonant activity calculator,"
           "    using VASP as a back-end."
           ""
           "    Contributors: Alexandr Fonari  (Georgia Tech)"
           "                  Shannon Stauffer (UT Austin)"
           "    MIT License, 2013"
           "    URL: http://raman-sc.github.io"
           "    Started at: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )


    #read settings from json file and initialize parameters###################
    with open('settings.json') as f:
        settings : dict = json.load(f)

        step_size = settings.get('step_size', 0.01)
        gen = settings.get('gen', False)
        VASP_RAMAN_RUN = settings['vasp_command']

    disps = [-1, 1]      # hardcoded for
    coeffs = [-0.5, 0.5] # three point stencil (nderiv=2)
    ###########################################################################


    # read POSCAR and OUTCAR with phonon modes ###############################
    atoms = read('POSCAR.phon', format='vasp')
    natoms = len(atoms)
    volume = atoms.get_volume()

    eigvals, eigvecs, norms = get_modes_from_OUTCAR('OUTCAR.phon', natoms)
    ###########################################################################


    # calculate Raman activity ###############################################
    with open('vasp_raman.dat', 'w') as output_fh:
        output_fh.write("# mode    freq(cm-1)    alpha    beta2    activity\n")

        #loop over phonon modes, excluding the first three (translationsy, imaginary)
        for i, eigval, eigvec, norm in zip(range(3, len(eigvals)), eigvals[3:], eigvecs[3:], norms[3:]):

            print("Mode #%i: frequency %10.7f cm-1; norm: %10.7f" % ( i, eigval, norm ) )

            #initialize empty Raman tensor
            ra = [[0.0 for x in range(3)] for y in range(3)]

            #loop over displacements (+/- step_size)
            for j, displacement in enumerate(disps):
                disp_filename = 'OUTCAR.%04d.%+d.out' % (i, displacement)

                if os.path.isfile(disp_filename):
                    print("File "+disp_filename+" exists, parsing...")
                else:
                    print("File "+disp_filename+" not found, preparing displaced POSCAR")

                    # write displaced POSCAR
                    atoms_displaced = atoms.copy()
                    atoms_displaced.positions = [ [ atoms.positions[k][l] + eigvec[k][l]*step_size*displacement/norm \
                                                  for l in range(3)] for k in range(natoms)]
                    write('POSCAR', atoms_displaced, format='vasp')
                    shutil.copy('POSCAR', 'POSCAR.%04d.%+d.out' % (i, displacement))

                    # run VASP
                    print("Running VASP...")
                    os.system(VASP_RAMAN_RUN)
                    if not os.path.isfile('OUTCAR'):
                        print("ERROR: Couldn't find OUTCAR file, exiting...")
                        sys.exit(1)
                    shutil.move('OUTCAR', disp_filename)

                #get dielectric tensor for this displacement
                eps = get_epsilon_from_OUTCAR(disp_filename)

                #add contribution to Raman tensor
                for m in range(3):
                    for n in range(3):
                        ra[m][n]   += eps[m][n] * coeffs[j]/step_size * norm * volume/(4.0*pi)
                #units: A^2/amu^1/2 =         dimless   * 1/A         * 1/amu^1/2  * A^3

                #end of loop over displacements for this phonon mode

            # Write quantities for this phonon mode to the output file
            # Calculate raman intensity as in https://doi.org/10.1039/C7CP01680H
            alpha = (ra[0][0] + ra[1][1] + ra[2][2])/3.0
            beta2 = 0.5*( (ra[0][0] - ra[1][1])**2 + (ra[0][0] - ra[2][2])**2 + (ra[1][1] - ra[2][2])**2 \
                     + 6.0 * (ra[0][1]**2 + ra[0][2]**2 + ra[1][2]**2) )
            intensity = 45.0*alpha**2 + 7.0*beta2

            print("! %4i  freq: %10.5f  alpha: %10.7f  beta2: %10.7f  activity: %10.7f " % (i, eigval, alpha, beta2, intensity))
            output_fh.write("%03i  %10.5f  %10.7f  %10.7f  %10.7f\n" % (i, eigval, alpha, beta2, intensity))
            output_fh.flush()

