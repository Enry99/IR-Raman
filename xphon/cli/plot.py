'''
CLI parser for command: plot
'''

import argparse

from xphon.cli.command import CLICommandBase


class CLICommand(CLICommandBase):
    """Plot spectrum, reading from the corresponding file.

    Example usage:
    xphon plot ir -broaden lorentz -fwhm 15 -range 400 4000
    xphon plot raman
    """

    @staticmethod
    def add_arguments(parser : argparse.ArgumentParser):
        parser.add_argument('spectrum',
                            choices=['ir', 'raman'],
                            help='Which spectrum to plot.')
        parser.add_argument('-broaden', choices=['gauss', 'lorentz'],
                            help='Type of broadening to apply to the spectrum.')
        parser.add_argument('-fwhm', type=float, default=15.0,
                            help='Broadening FWHM for the spectrum.')
        parser.add_argument('-range', type=float, nargs=2,
                            help='Frequency range (cm-1) of the spectrum to plot.')

    @staticmethod
    def run(args : argparse.Namespace):
        from xphon.postprocess.plot import plot_spectrum
        plot_spectrum(args.spectrum, args.broaden, args.fwhm, args.range)


    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
