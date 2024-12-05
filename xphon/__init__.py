#Created on Wed 20 Nov 2024
#Author: Enrico Pedretti

"""
--------------------------------- Xphon ---------------------------------

Xphon is a small Python package for the calculation of phonon modes,
infrared and Raman spectra of molecules using DFPT in VASP.

In order to run IR and Raman calculations, you need the following input files in the working directory:
- INCAR
- POSCAR
- KPOINTS
- POTCAR
- settings.json

The INCAR file should contain the following tags:
    EDIFF = 1E-10
    PREC = Accurate
    NELMIN = 10
    ISMEAR = 0
    SIGMA = 0.01
    ISYM = 0
    LCHARG = .FALSE.
    LWAVE = .FALSE.

Warning: DO NOT include specifig tags for phonons/dielectric tensor calculations, such as `IBRION` or `LEPSILON`, as they are automatically appended to the INCAR by this program.

The settings.json file should contain these keys:
{
    "step_size": 0.01,  # displacement step size in Angstrom
    "jobscript_path": "path/to/your/jobscript.sh",
    "submit_command": "sbatch"
}

Workflow:
1) First, you need to run a phonon calculation with VASP, which also gives the IR spectrum.
   $ xphon ir

2) Then you need can run the Raman calculations (in parallel):
    $ xphon raman

To get the spectra, use the following commands:
    $ xphon write ir
    $ xphon write raman

After writing, you can plot the spectra using the following commands:
    $ xphon plot ir
    $ xphon plot raman

More details can be found in the README of the repository.

------------------------------ Useful links -----------------------------

Official repository:    https://github.com/Enry99/IR-Raman

"""

__version__ = "0.1"

RAMAN_DIR = 'raman_calcs'
PHONONS_DIR = 'phonons'
