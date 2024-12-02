'''
CLI parser for command: write
'''

import argparse

from xphon.cli.command import CLICommandBase


class CLICommand(CLICommandBase):
    """Get results from vasprun.xml(s) and write spectrum to file.

    Example usage:
    xphon write ir
    xphon write raman
    xphon write trajs
    """

    @staticmethod
    def add_arguments(parser : argparse.ArgumentParser):
        parser.add_argument('what',
                            choices=['ir', 'raman', 'trajs'],
                            help='Which spectrum to write to file.')

    @staticmethod
    def run(args : argparse.Namespace):
        if args.what == 'ir':
            from xphon.calculations.ir import write_ir_spectrum
            write_ir_spectrum()
        elif args.what == 'raman':
            from xphon.calculations.raman import write_raman_spectrum
            write_raman_spectrum()
        elif args.what == 'trajs':
            from xphon.postprocess.trajectories import write_vibrations
            write_vibrations()


    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
