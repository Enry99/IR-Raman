#!/usr/bin/env python3
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
# Modified by Enrico Pedretti (University of Bologna), 2024
# to add many functionalities: update to python3, launch jobs in parallel,
# read settings from json file, added asymmetric anisotropy contribution.


import os
import re
import json
from math import sqrt, pi

from ase.io import read, write
from ase import Atoms

from xphon.calculations.jobs import launch_jobs
from xphon import RAMAN_DIR, PHONONS_DIR

DISPS = (-1, 1)      # hardcoded for
COEFFS = (-0.5, 0.5) # three point stencil (nderiv=2)

INCAR_TAGS = """
 IBRION = 7
 NSW = 1
 NWRITE = 3
 LEPSILON=.TRUE.
"""

def get_modes_from_OUTCAR(outcar_filename, natoms):
    '''
    Read phonon modes from OUTCAR file, excluding imaginary modes.
    '''

    mode_ids = [] # mode ids starting from 1 for the lowest freq mode
    mode_ids_vasp = [] # mode ids as written in VASP OUTCAR
    eigvals = []
    eigvecs = []
    norms   = []

    with open(outcar_filename, 'r') as outcar_fh:

        while True:
            line = outcar_fh.readline()
            if not line:
                break

            if "Eigenvectors after division by SQRT(mass)" in line:
                outcar_fh.readline() # empty line
                outcar_fh.readline() # Eigenvectors and eigenvalues of the dynamical matrix
                outcar_fh.readline() # ----------------------------------------------------
                outcar_fh.readline() # empty line

                for i in range(natoms*3):
                    outcar_fh.readline() # empty line

                    mode_header_line = outcar_fh.readline()
                    match_regex = re.search(r'^\s*(\d+).+?([\.\d]+) cm-1', mode_header_line)
                    if 'f/i' in mode_header_line:
                        imaginary = True
                    else:
                        imaginary = False


                    outcar_fh.readline()# X         Y         Z           dx          dy          dz
                    eigvec = []
                    for _ in range(natoms):
                        tmp = outcar_fh.readline().split()
                        eigvec.append([ float(tmp[x]) for x in range(3,6) ])



                    if not imaginary:
                        mode_ids = i + 1
                        mode_ids_vasp.append(int(match_regex.group(1)))
                        eigvals.append(float(match_regex.group(2)))
                        eigvecs.append(eigvec)
                        norms.append(sqrt(sum(abs(x)**2 for sublist in eigvec for x in sublist) ))


                #reverse order of modes, since vasp writes them in reverse order (higer freqs first)
                mode_ids = list(reversed(mode_ids))
                mode_ids_vasp = list(reversed(mode_ids_vasp))
                eigvals = list(reversed(eigvals))
                eigvecs = list(reversed(eigvecs))
                norms   = list(reversed(norms))

                return mode_ids, mode_ids_vasp, eigvals, eigvecs, norms

        #if we are here, something went wrong
        raise RuntimeError("Couldn't find 'Eigenvectors after division by SQRT(mass)' in OUTCAR.\
                            Use 'NWRITE=3' in INCAR.")


def get_epsilon_from_OUTCAR(outcar_filename):
    '''
    Read dielectric tensor from OUTCAR file.
    '''
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


def read_input_parameters():
    '''
    Return input parameters from json file, and atoms from POSCAR
    '''

    #read settings from json file and initialize parameters####################
    with open('settings.json') as f:
        settings : dict = json.load(f)

        step_size = settings.get('step_size', 0.01)
        jobscript_path = settings['jobscript_path']
        submit_command = settings.get('submit_command', 'sbatch')


    # read POSCAR and OUTCAR with phonon modes ################################
    atoms = read('POSCAR', format='vasp')

    return atoms, step_size, jobscript_path, submit_command


def write_displaced_POSCARS(atoms : Atoms, step_size: int):
    '''
    Write displaced POSCARs for each phonon mode and displacement
    for the cases not already calculated.
    '''

    natoms = len(atoms)

    # read (non-imaginary) phonon modes from OUTCAR
    mode_ids, _, _, eigvecs, norms = get_modes_from_OUTCAR(f'{PHONONS_DIR}/OUTCAR', natoms)


    #loop over phonon modes and write displaced POSCARs
    os.makedirs(RAMAN_DIR, exist_ok=True)

    dirs_to_run, labels = [], []
    for mode_id, eigvec, norm in zip(mode_ids, eigvecs, norms):

        #loop over displacements (+/- step_size)
        for j, displacement in enumerate(DISPS):

            subdir = f'{RAMAN_DIR}/{mode_id:04d}.{displacement:+d}'
            os.makedirs(subdir, exist_ok=True)

            outcar_path = f'{subdir}/OUTCAR'

            if os.path.isfile(outcar_path):
                try:
                    get_epsilon_from_OUTCAR(outcar_path)
                    continue
                except RuntimeError as e:
                    print(f"{outcar_path}: {e}, re-running.")

            print("Writing files for mode "+str(mode_id)+". displacement "+str(displacement))

            # write displaced POSCAR
            atoms_displaced = atoms.copy()
            atoms_displaced.positions = [ [ atoms.positions[k][l] + eigvec[k][l]*step_size*displacement/norm \
                                            for l in range(3)] for k in range(natoms)]
            write(f'{subdir}/POSCAR', atoms_displaced, format='vasp')
            dirs_to_run.append(subdir)
            labels.append(f'{mode_id:04d}.{displacement:+d}')

    return dirs_to_run, labels


def launch_raman_calculations(write_only : bool = False):

    # read settings from json file and initialize parameters###################
    atoms, step_size, jobscript_path, submit_command = read_input_parameters()

    # write displaced POSCARs for each phonon mode and displacement
    dirs_to_run, labels = write_displaced_POSCARS(atoms, step_size)

    # launch the calculations
    if not write_only:
        launch_jobs(subdir_paths=dirs_to_run,
                    jobscript_path=jobscript_path,
                    submit_command=submit_command,
                    jobnames=labels,
                    incar_tags=INCAR_TAGS)


def write_raman_spectrum():
    '''
    Write the Raman activity, reading the displaced OUTCAR files
    '''

    atoms, step_size, _, _ = read_input_parameters()
    mode_ids, mode_ids_vasp, eigvals, _, norms = get_modes_from_OUTCAR('OUTCAR.phon', len(atoms))


    with open('vasp_raman.dat', 'w') as f:
        f.write("mode    mode_vasp    freq(cm-1)    a    gamma2    delta2    activity\n")

        #loop over phonon modes, excluding the first three (translationsy, imaginary)
        for mode_id, mode_id_vasp, eigval, norm in zip(mode_ids,mode_ids_vasp,eigvals,norms):

            #initialize empty Raman tensor (tensor of polarizability derivatives)
            ra = [[0.0 for x in range(3)] for y in range(3)]

            #loop over displacements (+/- step_size)
            for j, displacement in enumerate(DISPS):

                subdir = f'{RAMAN_DIR}/{mode_id:04d}.{displacement:+d}'
                outcar_path = f'{subdir}/OUTCAR'

                try:
                    eps = get_epsilon_from_OUTCAR(outcar_path)
                except Exception as e:
                    print(f"{outcar_path}: {e}, skipping.")
                    continue

                #add contribution to Raman tensor
                for m in range(3):
                    for n in range(3):
                        #central difference scheme for numerical derivative (https://doi.org/10.1039/C7CP01680H)
                        ra[m][n]   += eps[m][n] * COEFFS[j]/step_size * norm * atoms.get_volume()/(4.0*pi)
                        #units: A^2/amu^1/2 =         dimless   * 1/A         * 1/amu^1/2  * A^3


            # Calculate raman intensity with Placzek approximation
            # (see https://doi.org/10.1021/acs.jctc.9b00584)

            # mean polarizability
            a = 1./3 * (ra[0][0] + ra[1][1] + ra[2][2])

            # anisotropy
            gamma2 = 1./2 * ( (ra[0][0] - ra[1][1])**2 + (ra[0][0] - ra[2][2])**2 + (ra[1][1] - ra[2][2])**2) + \
                    3./4 * ( (ra[0][1] + ra[1][0])**2 + (ra[0][2] + ra[2][0])**2 + (ra[1][2] + ra[2][1])**2)

            # asymmetric anisotropy
            delta2 = 3./4 * ( (ra[0][1] - ra[1][0])**2 + (ra[0][2] - ra[2][0])**2 + (ra[1][2] - ra[2][1])**2)

            # Raman activity
            Iraman = 45.0*a**2 + 7.0*gamma2 + 5*delta2


            #write to output file
            f.write(f"{mode_id:03d}  {mode_id_vasp:03d}   {eigval:10.5f}  {a:10.7f}\
                                {gamma2:10.7f}  {delta2:10.7f} {Iraman:10.7f}\n")
