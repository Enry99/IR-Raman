
"""Module for plotting the IR and Raman spectra."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

COLORS = {
    'ir': 'orangered',
    'raman': 'green'
}

COLUMNS = {
    'ir': (1, 2),
    'raman': (2, 6)
}

def plot_spectrum(spectrum : str,
                  broaden_type : str | None = None,
                  fwhm : float = 0,
                  freq_range : tuple[float, float] | None = None):
    """Plot the spectrum with the given parameters.

    Args:
        - spectrum (str): Which spectrum to plot.
        - broaden_type (str): Type of broadening to apply to the spectrum.
        - fwhm (float): Broadening FWHM for the spectrum.
        - freq_range (tuple): Frequency range (cm-1) of the spectrum to plot.
    """

    # Read the data
    data = np.loadtxt(fname=f'{spectrum}_spectrum.dat',
                      dtype=float,
                      skiprows=1,
                      usecols=COLUMNS[spectrum])
    x = data[:, 0]
    y = data[:, 1]

    # Plot the data
    if broaden_type is None:
        plt.stem(x, y, linefmt=f'{COLORS[spectrum]}-', markerfmt=' ')

    else:
        from xphon.postprocess.broaden import get_broadened_spectrum
        x, y = get_broadened_spectrum(x, y, gam=fwhm/2, function=broaden_type)

        plt.plot(x, y, color=COLORS[spectrum])

    if freq_range is not None:
        plt.xlim(freq_range)

    plt.xlabel('Frequency (cm-1)')
    plt.ylabel('Intensity')
    plt.title(f'{spectrum.capitalize()} spectrum')
    plt.savefig(f'{spectrum}_spectrum.png', dpi=300, bbox_inches='tight')