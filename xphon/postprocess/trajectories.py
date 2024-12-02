
'''
Module to write the animated trajectories of the vibrational modes
'''

from pathlib import Path

from ase.calculators.vasp import Vasp
from ase import units
from ase.vibrations import VibrationsData
from ase.io import read, Trajectory

from xphon import PHONONS_DIR


def write_mode(vibrations : VibrationsData, n=None, kT=units.kB * 300, nimages=30):
    """Write mode number n to trajectory file. If n is not specified,
    writes all non-zero modes."""
    if n is None:
        for index, energy in enumerate(vibrations.get_energies()):
            if abs(energy) > 1e-5:
                write_mode(vibrations, n=index, kT=kT, nimages=nimages)
        return

    else:
        n %= len(vibrations.get_energies())

    with Trajectory(f'{n}.traj', 'w') as traj:
        for image in (vibrations.iter_animated_mode(n,temperature=kT, frames=nimages)):
            traj.write(image)


def write_vibrations():
    """Write all vibrational modes to trajectory files."""


    if not Path(f'{PHONONS_DIR}/ase-sort.dat').is_file():
        #write fake ase-sort.dat to make ase happy
        atoms = read(f'{PHONONS_DIR}/POSCAR')
        with open(f'{PHONONS_DIR}/ase-sort.dat', 'w') as f:
            for n in range(len(atoms)):
                f.write('%5i %5i \n' % (n, n))

    vasp = Vasp(directory=PHONONS_DIR)
    vasp.read()

    vibrations = vasp.get_vibrations()

    write_mode(vibrations)