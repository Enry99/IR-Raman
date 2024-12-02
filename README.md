# IR-Raman
Xphon is a small Python package for the calculation of phonon modes, infrared and Raman spectra of molecules using DFPT in VASP.

Inspired by the scripts [VASP_tools](https://github.com/sebnenon/VASP_tools) (IR) and [raman-sc/VASP](https://github.com/raman-sc/VASP) (Raman). \
The [ASE](https://wiki.fysik.dtu.dk/ase/) library is used for reading/writing POSCAR files.

Installation
----
First, clone the repository in your local machine with:

`git clone https://github.com/Enry99/IR-Raman`

Once the download is completed, go inside the downloaded folder and run:

`bash install.sh`

to add the executable in the `PATH` variable. With this operation, you can launch the program from any folder.

Finally, if you do not have it already, you need to install [ASE](https://wiki.fysik.dtu.dk/ase/) with:

`pip install ase==3.23.0`


Usage
----

In order to run IR and Raman calculations, the user needs to provide the following input files:
- INCAR
- POSCAR
- KPOINTS
- POTCAR
- settings.json

in the working directory.

The INCAR file should contain the following tags:

    EDIFF = 1E-10    !or anyway a very low value
    NELMIN = 10      !(or higher)
    ISYM = 0
    PREC = Accurate
    LCHARG = .FALSE. !(to avoid producing hundreds CHGCAR files in Raman calculations)
    LWAVE = .FALSE.  !(to avoid producing hundreds of heavy WAVECAR files in Raman calculations)

Note that a high ENCUT is usually suggested for phonon calculations.

The settings.json file should contain these keys:

    "step_size": 0.01,
    "jobscript_path": "path/to/your/jobscript.sh",
    "submit_command": "sbatch"


Workflow:
1) First, you need to run a phonon calculation with VASP, which also gives the IR spectrum.

   `$ xphon ir`

2) Then you need can run the Raman calculations (in parallel):

    `$ xphon raman`

To get the spectra, use the following commands:

    $ xphon write ir
    $ xphon write raman

After writing, you can plot the spectra using the following commands:

    $ xphon plot ir
    $ xphon plot raman