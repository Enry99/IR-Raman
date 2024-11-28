#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Enrico Pedretti

'''
Module for launching the jobs in parallel
'''

from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys

TEST = False


def launch_jobs(*,
                subdir_paths : list[str],
                jobscript_path : str,
                submit_command : str,
                jobnames : list[str],
                incar_tags : str):
    '''
    Launch the calculations.
    Writes the job ids in a txt file

    Args:
    - subdir_paths : list of paths to the directories where the calculations are to be launched
    - jobscript_path : path to the jobscript
    - submit_command : command to launch the jobscript
    - jobnames : list of jobnames (for Slurm only)

    '''
    main_dir = os.getcwd()

    submitted_jobs = []
    for j_dir, jobname in zip(subdir_paths, jobnames):

        shutil.copyfile(jobscript_path, f'{j_dir}/jobscript.sh')
        shutil.copyfile('INCAR', f'{j_dir}/INCAR')
        shutil.copyfile('KPOINTS', f'{j_dir}/KPOINTS')
        shutil.copyfile('POTCAR', f'{j_dir}/POTCAR')

        os.chdir(j_dir)   ####################

        # modify INCAR, adding the tags
        with open('INCAR', 'r',encoding=sys.getfilesystemencoding()) as f:
            lines = f.readlines()
        with open('INCAR', 'w',encoding=sys.getfilesystemencoding()) as f:
            f.writelines(lines)
            f.write(incar_tags)

        #change job title (only for slumr jobscripts)
        with open('jobscript.sh', 'r',encoding=sys.getfilesystemencoding()) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "job-name" in line:
                    lines[i] = f"{line.split('=')[0]}={jobname}\n"
                    break
        with open('jobscript.sh', 'w',encoding=sys.getfilesystemencoding()) as f:
            f.writelines(lines)

        launch_string = f"{submit_command} jobscript.sh"
        if TEST: print(launch_string) #pylint: disable=multiple-statements
        else:
            outstring = subprocess.getoutput(launch_string) #launches the jobscript from j_dir
            print(outstring)
            submitted_jobs.append(int(outstring.split()[-1]))
        os.chdir(main_dir) ####################

    with open("submitted_jobs.txt", "a",encoding=sys.getfilesystemencoding()) as f:
        f.writelines([f'{job}\n' for job in submitted_jobs])


def get_running_jobs():
    '''
    Get the running jobs by interrogating the scheduler
    '''
    running_jobs = subprocess.getoutput("squeue --me").split("\n")[1:]
    running_job_ids = [int(job.split()[0]) for job in running_jobs]

    return running_job_ids


def _cancel_jobs(ids : list[int]):
    '''
    Cancel the jobs with the given ids
    '''
    for job_id in ids:
        os.system(f"scancel {job_id}")


def scancel():
    '''
    Cancel all the running jobs For the current xphon session.
    Associated to the command 'xphon scancel' in the CLI.
    '''

    #read submitted jobs from .submitted_jobs.txt
    if Path("submitted_jobs.txt").exists():
        with open("submitted_jobs.txt", "r",encoding=sys.getfilesystemencoding()) as f:
            submitted_jobs = f.readlines()
            submitted_job_ids = [int(job.strip()) for job in submitted_jobs]
    else:
        submitted_job_ids = []

    running_jobs = get_running_jobs()
    job_ids_to_cancel = [job for job in running_jobs if job in submitted_job_ids]

    if len(job_ids_to_cancel) == 0:
        print("No jobs to cancel.")
        return

    print(f"Cancelling jobs {job_ids_to_cancel}.")
    _cancel_jobs(job_ids_to_cancel)
    print("All jobs cancelled.")
