'''
CLI parser for command: raman
'''

import argparse

from xphon.cli.command import CLICommandBase


class CLICommand(CLICommandBase):
    """Launch displacement calculations for Raman spectrum

    Example usage:
    xphon raman
    xphon raman -write-only
    """

    @staticmethod
    def add_arguments(parser : argparse.ArgumentParser):
        parser.add_argument('-write-only', action='store_true',
                            help='Write displaced POSCARs only, do not launch calculations')



    @staticmethod
    def run(args : argparse.Namespace):
        from xphon.calculations.raman import launch_raman_calculations
        launch_raman_calculations(args.write_only)


    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
