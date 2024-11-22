'''
Common utility functions for IR and Raman calculations
'''

import re
import json
from math import sqrt
from dataclasses import dataclass

from ase.io import read


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


def get_modes_from_OUTCAR(outcar_filename, natoms):
    '''
    Read phonon modes from OUTCAR file, excluding imaginary modes.

    Args:
    - outcar_filename: path to OUTCAR file
    - natoms: number of atoms in the structure

    Returns:
    - modes_list: list of Mode objects
    '''

    modes_list : list[Mode] = []

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
                    # 60 f  =    5.519867 THz    34.682350 2PiTHz  184.122959 cm-1    22.828327 meV
                    match_regex = re.search(r'^\s*(\d+).+?([\.\d]+) cm-1', mode_header_line)
                    if 'f/i' in mode_header_line:
                        imaginary = True
                    else:
                        imaginary = False


                    outcar_fh.readline()# X         Y         Z           dx          dy          dz
                    eigvec = []
                    for _ in range(natoms):
                        tmp = outcar_fh.readline().split()
                        eigvec.append([ float(tmp[x]) for x in range(3,6) ]) #range(3,6) -> dx dy dz



                    if not imaginary:
                        modes_list.append(
                            Mode(id=i+1,
                                 id_vasp=int(match_regex.group(1)),
                                 frequency=float(match_regex.group(2)),
                                 eigvec=eigvec,
                                 norm=sqrt(sum(abs(x)**2 for sublist in eigvec for x in sublist)))
                                )


                #reverse order of modes, since vasp writes them in reverse order (higer freqs first)
                mode_ids = list(reversed(mode_ids))
                mode_ids_vasp = list(reversed(mode_ids_vasp))
                frequencies = list(reversed(frequencies))
                eigvecs = list(reversed(eigvecs))
                norms   = list(reversed(norms))

                return modes_list

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


    # read POSCAR and OUTCAR with phonon modes ################################
    atoms = read('POSCAR', format='vasp')

    return atoms, step_size, jobscript_path, submit_command