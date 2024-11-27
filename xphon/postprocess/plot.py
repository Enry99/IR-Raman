
"""Module for plotting the IR and Raman spectra."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks


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
                  laser_freq : float | None = None,
                  temperature : float = 300,
                  freq_range : tuple[float, float] | None = None,
                  show_peaks : bool = False):
    """Plot the spectrum with the given parameters.

    Args:
        - spectrum (str): Which spectrum to plot.
        - broaden_type (str): Type of broadening to apply to the spectrum. ('gauss' or 'lorentz')
        - fwhm (float): Broadening FWHM for the spectrum.
        - laser_freq (float): Frequency in cm^-1 of the laser used to excite the Raman spectrum.
        - temperature (float): Temperature in K for the Raman spectrum.
        - freq_range (tuple): Frequency range (cm-1) of the spectrum to plot.
        - show_peaks (bool): Whether to show the peaks in the spectrum.
    """

    # Read the data
    print(f'Reading {spectrum}_spectrum.dat...')
    data = np.loadtxt(fname=f'{spectrum}_spectrum.dat',
                      dtype=float,
                      skiprows=1,
                      usecols=COLUMNS[spectrum])
    x = data[:, 0]
    y = data[:, 1]


    # Prefactor as calculated in CRYSTAL
    if spectrum == 'raman' and laser_freq is not None:
        print('Applying Laser frequency correction...')
        # Bose occupancy factor
        B = 1/( 1 - np.exp(-1.9865e-23 * laser_freq / (1.38064852e-23 * temperature) ))
        #print(f'Bose factor: {B}')
        y = y * B/(30*x) * (x - laser_freq)**4 # Correct the Raman spectrum


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

        if show_peaks: #plot the peaks points and also the frequency labels
            print('Finding peaks...')
            peaks, _ = find_peaks(y, prominence=0.01, wlen=20)
            plt.plot(x[peaks], y[peaks], 'ro', markersize=3)
            for i, peak in enumerate(peaks):
                plt.text(x[peak], y[peak]+0.01, f'{int(x[peak])}',
                         fontsize=8, ha='center', va='bottom')


    if freq_range is not None:
        plt.xlim(freq_range)

    plt.xlabel('Frequency (cm-1)')
    plt.ylabel('Intensity (a.u.)')
    plt.title(f'{spectrum.capitalize()} spectrum')
    figname = f'{spectrum}_spectrum{"_broaden" if broaden_type else ""}.png'
    plt.savefig(figname, dpi=300, bbox_inches='tight')

    print(f'Plot saved in {figname}.')
