#Created on Wed 20 Nov 2024
#Author: Enrico Pedretti

"""
--------------------------------- Xphon ---------------------------------

Xphon is a small Python package for the calculation of phonon modes,
infrared and Raman spectra of molecules using DFPT in VASP.

In order to run IR and Raman calculations, the user needs to provide
the following input files:
    - INCAR
    - POSCAR
    - KPOINTS
    - POTCAR
    - settings.json
in the working directory.

The INCAR file should contain the following tags:
    EDIFF = 1E-10    !or anyway a very low value
    NELMIN = 10      !(or higher)
    LCHARG = .FALSE. !(to avoid producing hundreds CHGCAR files in Raman calculations)
    LWAVE = .FALSE.  !(to avoid producing hundreds of heavy WAVECAR files in Raman calculations)

The settings.json file should contain these keys:
{
    "step_size": 0.01,  # displacement step size in Angstrom
    "jobscript_path": "path/to/your/jobscript.sh",
    "submit_command": "sbatch" (optional, default is "sbatch")
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

------------------------------ Useful links -----------------------------

Official repository:    https://github.com/Enry99/IR-Raman

"""

__version__ = "0.1"

RAMAN_DIR = 'raman_calcs'
PHONONS_DIR = 'phonons'
