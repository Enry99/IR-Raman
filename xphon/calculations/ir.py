#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# plot IR (S.Nenon 2015 - VASP_tools https://github.com/sebnenon/VASP_tools)
#
# Modified by Enrico Pedretti (University of Bologna), 2024


import sys
import os

from xphon.calculations.utils import Mode, read_input_parameters, \
    get_modes_from_OUTCAR, get_Born_charges_from_OUTCAR
from xphon.calculations.jobs import launch_jobs
from xphon import PHONONS_DIR


INCAR_TAGS = """
 LEPSILON=.TRUE.
"""

def launch_ir_calculation():
    '''
    Launches the DFPT calculation for IR intensities
    '''

    _, _, jobscript_path, submit_command = read_input_parameters()

    launch_jobs(subdir_paths=[PHONONS_DIR],
                jobscript_path=jobscript_path,
                submit_command=submit_command,
                jobnames=['phon'],
                incar_tags=INCAR_TAGS)


def get_ir_intensity_for_mode(mode : Mode, born_charges : list):
    """
    Computes the IR intensity for the given mode,
    using the formula in: https://utheses.univie.ac.at/detail/9139#, (Eq. 2.51)

    Args:
    - mode: phonon mode
    - born_charges: Born charges

    Returns:
    - ir_intensity: IR intensity for the mode
    """

    intensity = 0.0
    for alpha in range(3):

        innersums = 0.0
        for l in range(len(born_charges)): #natoms
            for beta in range(3): #cartesian components of the displacement
                innersums += born_charges[l][alpha][beta]*mode.eigvec[l][beta]

        intensity += innersums**2

    return intensity


def write_ir_spectrum():
    '''
    Writes the IR spectrum to file
    '''

    atoms, _, _, _ = read_input_parameters()
    natoms = len(atoms)

    if not os.path.isfile(f'{PHONONS_DIR}/OUTCAR'):
        sys.exit(f"OUTCAR file not found in {PHONONS_DIR}")


    print(f"Reading eigenvectors from {PHONONS_DIR}/OUTCAR")
    modes_list = get_modes_from_OUTCAR(f'{PHONONS_DIR}/OUTCAR', natoms)


    print(f"Reading Born charges from {PHONONS_DIR}/OUTCAR")
    born_charges = get_Born_charges_from_OUTCAR(f'{PHONONS_DIR}/OUTCAR', natoms)


    with open('ir_spectrum.dat', 'w') as f:
        f.write("mode    mode_vasp    freq(cm-1)    intensity\n")

        #loop over phonon modes
        for mode in modes_list:

            intensity = get_ir_intensity_for_mode(mode, born_charges)

            #write to output file
            f.write(f"{mode.id:03d}  {mode.id_vasp:03d}   {intensity:10.7f}\n")
