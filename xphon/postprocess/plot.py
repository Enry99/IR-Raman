
"""Module for plotting the IR and Raman spectra."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

#TODO: Add peaks identification to the plot.


COLORS = {
    'ir': 'orangered',
    'raman': 'green'
}

COLUMNS = {
    'ir': (2, 3),
    'raman': (2, 6)
}

def plot_spectrum(spectrum : str,
                  broaden_type : str | None = None,
                  fwhm : float = 0,
                  freq_range : tuple[float, float] | None = None):
    """Plot the spectrum with the given parameters.

    Args:
        - spectrum (str): Which spectrum to plot.
        - broaden_type (str): Type of broadening to apply to the spectrum. ('gauss' or 'lorentz')
        - fwhm (float): Broadening FWHM for the spectrum.
        - freq_range (tuple): Frequency range (cm-1) of the spectrum to plot.
    """

    # Read the data
    print(f'Reading {spectrum}_spectrum.dat...')
    data = np.loadtxt(fname=f'{spectrum}_spectrum.dat',
                      dtype=float,
                      skiprows=1,
                      usecols=COLUMNS[spectrum])
    x = data[:, 0]
    y = data[:, 1]

    # Plot the data
    print(f'Plotting {spectrum}...')
    if broaden_type is None:
        _, stemlines, baseline = plt.stem(x, y, markerfmt=' ')
        plt.setp(stemlines, 'color', COLORS[spectrum])
        plt.setp(stemlines, 'linewidth', 0.5)
        plt.setp(baseline, 'color', COLORS[spectrum])

    else:
        from xphon.postprocess.broaden import get_broadened_spectrum
        x, y = get_broadened_spectrum(x, y, fwhm, function=broaden_type)

        plt.plot(x, y, color=COLORS[spectrum])

    if freq_range is not None:
        plt.xlim(freq_range)

    plt.xlabel('Frequency (cm-1)')
    plt.ylabel('Intensity (a.u.)')
    plt.title(f'{spectrum.capitalize()} spectrum')
    figname = f'{spectrum}_spectrum{"_broaden" if broaden_type else ""}.png'
    plt.savefig(figname, dpi=300, bbox_inches='tight')

    print(f'Plot saved in {figname}.')
