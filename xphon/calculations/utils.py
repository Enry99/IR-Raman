'''
Common utility functions for IR and Raman calculations
'''

import json
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from ase.io import read
from ase.calculators.vasp import Vasp


@dataclass
class Mode:
    '''
    Class to store all information about a phonon mode:

    - id: index of the mode, starting from 1 for the lowest freq mode
    - id: index of the mode as written in VASP OUTCAR (reverse order)
    - frequency: mode freq. in cm-1
    - eigvec: eigenvector of the mode (list of displacements [[dx dy dz], ...] for each atom)
    - norm: norm of the N-dimensional eigenvector
    '''

    id: int
    id_vasp: int
    frequency: float
    eigvec: list
    norm: float


def get_modes(directory: str):
    '''
    Read phonon modes from vasprun.xml file, excluding imaginary modes.

    Args:
    - directory: path to the directory containing the calculation results
    - natoms: number of atoms in the structure

    Returns:
    - modes_list: list of Mode objects
    '''

    modes_list : list[Mode] = []

    if not Path(f'{directory}/ase-sort.dat').is_file():
        #write fake ase-sort.dat to make ase happy
        atoms = read(f'{directory}/POSCAR')
        with open(f'{directory}/ase-sort.dat', 'w') as f:
            for n in range(len(atoms)):
                f.write('%5i %5i \n' % (n, n))

    vasp = Vasp(directory=directory)
    vasp.read()

    vibr = vasp.get_vibrations()

    frequencies = vibr.get_frequencies()
    frequencies_vasp = np.array([len(frequencies)-i for i in range(len(frequencies))])
    eigenvectors = vibr.get_modes()
    norms = np.array([np.linalg.norm(eig) for eig in eigenvectors])


    real_frequencies_idxs = [i for i in range(len(frequencies)) if frequencies[i].imag == 0]

    for i in real_frequencies_idxs:
        modes_list.append(Mode(i+1,
                               frequencies_vasp[i],
                               frequencies[i].real,
                               eigenvectors[i],
                               norms[i]))

    return modes_list


def get_epsilon(vasprun_path : str):
    '''
    Read dielectric tensor from vasprun.xml file
    '''

    atoms = read(vasprun_path)

    return atoms.calc.results['dielectric_tensor']


def get_born_charges(vasprun_path : str):
    '''
    Read Born charges from vasprun.xml file
    '''

    atoms = read(vasprun_path)

    return atoms.calc.results['born_effective_charges']


def read_input_parameters():
    '''
    Reads input parameters from json file, and atoms from POSCAR

    Returns:
    - atoms: atoms object
    - step_size: step size for finite difference
    - jobscript_path: path to jobscript template
    - submit_command: command to submit job
    '''

    #read settings from json file and initialize parameters####################
    with open('settings.json') as f:
        settings : dict = json.load(f)

        step_size = settings.get('step_size', 0.01)
        jobscript_path = settings['jobscript_path']
        submit_command = settings.get('submit_command', 'sbatch')


    atoms = read('POSCAR')

    return atoms, step_size, jobscript_path, submit_command
