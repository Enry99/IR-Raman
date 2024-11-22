'''
CLI parser for command: ir
'''

import argparse

from xphon.cli.command import CLICommandBase


class CLICommand(CLICommandBase):
    """Launch phonon calculation for IR spectrum

    Example usage:
    xphon ir
    xphon ir -write-only
    """

    @staticmethod
    def add_arguments(parser : argparse.ArgumentParser):
        return

    @staticmethod
    def run(args : argparse.Namespace):
        from xphon.calculations.ir import launch_ir_calculation
        launch_ir_calculation()


    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
