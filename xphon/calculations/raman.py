#!/usr/bin/env python3
#
# Author: Enrico Pedretti (University of Bologna), 2024
#
# Inspired by vasp_raman.py v. 0.6.0 by
# Alexandr Fonari (Georgia Tech) and hannon Stauffer (UT Austin)
# URL: http://raman-sc.github.io


import os
from math import pi

from ase.io import write
from ase import Atoms

from xphon.calculations.utils import Mode, read_input_parameters, \
    get_modes, get_epsilon
from xphon.calculations.jobs import launch_jobs
from xphon import RAMAN_DIR, PHONONS_DIR


DISPS = (-1, 1)      # hardcoded for
COEFFS = (-0.5, 0.5) # three point stencil (nderiv=2)


INCAR_TAGS = """
 LEPSILON=.TRUE.
"""

def write_displaced_POSCARS(atoms : Atoms, step_size: int):
    '''
    Write displaced POSCARs for each phonon mode and displacement
    for the cases not already calculated.
    '''

    natoms = len(atoms)

    # read (non-imaginary) phonon modes
    modes_list = get_modes(PHONONS_DIR)


    #loop over phonon modes and write displaced POSCARs
    os.makedirs(RAMAN_DIR, exist_ok=True)

    dirs_to_run, labels = [], []
    for mode in modes_list:

        #loop over displacements (+/- step_size)
        for j, displacement in enumerate(DISPS):

            subdir = f'{RAMAN_DIR}/{mode.id:04d}.{displacement:+d}'
            os.makedirs(subdir, exist_ok=True)

            vasprun_path = f'{subdir}/vasprun.xml'

            if os.path.isfile(vasprun_path):
                try:
                    get_epsilon(vasprun_path)
                    continue
                except RuntimeError as e:
                    print(f"{vasprun_path}: {e}, re-running.")

            print(f"Writing files for mode {mode.id}, displacement {displacement:+d}")

            # write displaced POSCAR
            atoms_displaced = atoms.copy()
            atoms_displaced.positions = [ [ atoms.positions[k][l] + mode.eigvec[k][l]*step_size*displacement/mode.norm \
                                            for l in range(3)] for k in range(natoms)]
            write(f'{subdir}/POSCAR', atoms_displaced, format='vasp')
            dirs_to_run.append(subdir)
            labels.append(f'{mode.id:04d}.{displacement:+d}')

    return dirs_to_run, labels


def launch_raman_calculations(write_only : bool = False):
    '''
    Generate displaced POSCARs and launch the calculations in parallel
    '''

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


def get_raman_tensor_for_mode(mode : Mode, step_size : float, volume : float):
    '''
    Calculate Raman tensor for a given mode, reading the displaced epsilons

    Args:
    - mode: Mode object
    - step_size: displacement step size
    - volume: volume of the unit cell

    Returns:
    - ra: Raman tensor (polarizability derivatives) (3x3 matrix)
    '''
    #initialize empty Raman tensor (tensor of polarizability derivatives)
    ra = [[0.0 for x in range(3)] for y in range(3)]

    #loop over displacements (+/- step_size)
    for j, displacement in enumerate(DISPS):

        subdir = f'{RAMAN_DIR}/{mode.id:04d}.{displacement:+d}'
        vasprun_path = f'{subdir}/vasprun.xml'

        try:
            eps = get_epsilon(vasprun_path)
        except Exception as e:
            print(f"{vasprun_path}: {e}, skipping.")
            continue

        #add contribution to Raman tensor
        for m in range(3):
            for n in range(3):
                #central difference scheme for numerical derivative (https://doi.org/10.1039/C7CP01680H)
                ra[m][n]   += eps[m][n] * COEFFS[j]/step_size * mode.norm * volume/(4.0*pi)
                #units: A^2/amu^1/2 =         dimless   * 1/A         * 1/amu^1/2  * A^3

    return ra


def get_raman_data_for_mode(ra):
    '''
    Calculate raman intensity with Placzek approximation
    (see https://doi.org/10.1021/acs.jctc.9b00584)

    Args:
    - ra: Raman tensor (polarizability derivatives) (3x3 matrix)

    Returns:
    - a: mean polarizability
    - gamma2: anisotropy
    - delta2: asymmetric anisotropy
    - Iraman: Raman intensity
    '''


    # mean polarizability
    a = 1./3 * (ra[0][0] + ra[1][1] + ra[2][2])

    # anisotropy
    gamma2 = 1./2 * ( (ra[0][0] - ra[1][1])**2 + (ra[0][0] - ra[2][2])**2 + (ra[1][1] - ra[2][2])**2) + \
            3./4 * ( (ra[0][1] + ra[1][0])**2 + (ra[0][2] + ra[2][0])**2 + (ra[1][2] + ra[2][1])**2)

    # asymmetric anisotropy
    delta2 = 3./4 * ( (ra[0][1] - ra[1][0])**2 + (ra[0][2] - ra[2][0])**2 + (ra[1][2] - ra[2][1])**2)

    # Raman activity
    Iraman = 45.0*a**2 + 7.0*gamma2 + 5*delta2

    return a, gamma2, delta2, Iraman


def write_raman_spectrum():
    '''
    Write the Raman activity, reading the displaced files
    '''

    print("Reading Raman data from vasprun.xml files...")
    atoms, step_size, _, _ = read_input_parameters()
    modes_list = get_modes(PHONONS_DIR)

    print('Calculating Raman activity...')
    with open('raman_spectrum.dat', 'w') as f:
        f.write("mode    mode_vasp    freq(cm-1)    a    gamma2    delta2    activity\n")

        #loop over phonon modes
        for mode in modes_list:

            ra = get_raman_tensor_for_mode(mode, step_size, atoms.get_volume())

            #calculate Raman activity
            a, gamma2, delta2, activity = get_raman_data_for_mode(ra)

            #write to output file
            f.write(f"{mode.id:03d}  {mode.id_vasp:03d}  {mode.frequency:10.5f}  "\
                    f"{a:10.7f}  {gamma2:10.7f}  {delta2:10.7f}  {activity:10.7f}\n")

    print("Raman spectrum written to raman_spectrum.dat")
