'''
CLI parser for command: write
'''

import argparse

from xphon.cli.command import CLICommandBase


class CLICommand(CLICommandBase):
    """Get results from OUTCAR(s) and write spectrum to file.

    Example usage:
    xphon write ir
    xphon write raman
    """

    @staticmethod
    def add_arguments(parser : argparse.ArgumentParser):
        parser.add_argument('spectrum',
                            choices=['ir', 'raman'],
                            help='Which spectrum to write to file.')

    @staticmethod
    def run(args : argparse.Namespace):
        if args.spectrum == 'ir':
            from xphon.calculations.ir import write_ir_spectrum
            write_ir_spectrum()
        elif args.spectrum == 'raman':
            from xphon.calculations.raman import write_raman_spectrum
            write_raman_spectrum()

    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
