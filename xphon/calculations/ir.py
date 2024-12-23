#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Enrico Pedretti (University of Bologna), 2024
# Inspired by plot IR (S.Nenon 2015 - VASP_tools https://github.com/sebnenon/VASP_tools)


import sys
import os
import shutil

from xphon.calculations.utils import Mode, read_input_parameters, \
    get_modes, get_born_charges
from xphon.calculations.jobs import launch_jobs
from xphon import PHONONS_DIR


INCAR_TAGS = """
 IBRION = 7
 NSW = 1
 NWRITE = 3
 LEPSILON=.TRUE.
"""

def launch_ir_calculation():
    '''
    Launches the DFPT calculation for IR intensities
    '''

    _, _, jobscript_path, submit_command = read_input_parameters()


    os.makedirs(PHONONS_DIR, exist_ok=True)
    shutil.copyfile('POSCAR', f'{PHONONS_DIR}/POSCAR')

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

    if not os.path.isfile(f'{PHONONS_DIR}/vasprun.xml'):
        sys.exit(f"vasprun.xml file not found in {PHONONS_DIR}")


    print(f"Reading eigenvectors from {PHONONS_DIR}/vasprun.xml")
    modes_list = get_modes(PHONONS_DIR)


    print(f"Reading Born charges from {PHONONS_DIR}/vasprun.xml")
    born_charges = get_born_charges(f'{PHONONS_DIR}/vasprun.xml')


    print("Computing IR intensities...")
    with open('ir_spectrum.dat', 'w') as f:
        f.write("mode    mode_vasp    freq(cm-1)    intensity\n")

        #loop over phonon modes
        for mode in modes_list:

            intensity = get_ir_intensity_for_mode(mode, born_charges)

            #write to output file
            f.write(f"{mode.id:03d}  {mode.id_vasp:03d}   {mode.frequency:10.5f}  {intensity:10.7f}\n")

    print("IR spectrum written to ir_spectrum.dat")
