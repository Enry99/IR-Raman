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
        parser.add_argument('-broaden', choices=['gauss', 'lorentz'], default='lorentz',
                            help='Type of broadening to apply to the spectrum.')
        parser.add_argument('-fwhm', type=float, default=10.0,
                            help='Broadening FWHM for the spectrum.')
        parser.add_argument('-laser_freq', type=float,
                            help='Frequency in cm^-1 of the laser used to excite the Raman spectrum.')
        parser.add_argument('-temperature', type=float, default=300,
                            help='Temperature in K for the Raman spectrum.')
        parser.add_argument('-range', type=float, nargs=2,
                            help='Frequency range (cm-1) of the spectrum to plot.')
        parser.add_argument('-show_peaks', action='store_true', default=True,
                            help='Show the peaks in the spectrum.')

    @staticmethod
    def run(args : argparse.Namespace):
        from xphon.postprocess.plot import plot_spectrum
        plot_spectrum(spectrum=args.spectrum,
                        broaden_type=args.broaden,
                        fwhm=args.fwhm,
                        laser_freq=args.laser_freq,
                        temperature=args.temperature,
                        freq_range=args.range,
                        show_peaks=args.show_peaks)


    @staticmethod
    def bind_function(parser: argparse.ArgumentParser):
        parser.set_defaults(func=CLICommand.run)
