#!/usr/bin/env python3
#


import numpy as np

def get_broadened_spectrum(frequencies : np.ndarray,
                           intensities : np.ndarray,
                           fwhm : float = 15.0,
                           function : str ='Lorentzian'):
    """
    Broaden the spectrum using a Gaussian or Lorentzian function.

    Args:
    - frequencies : np.ndarray
        Array of frequencies.
    - intensities : np.ndarray
        Array of intensities.
    - fwhm : float
        The broadening parameter (half of FWHM)
    - function : str
        Type of broadening function ('Gaussian' or 'Lorentzian').
    """

    # Normalize intensities
    intensities /= np.max(np.abs(intensities))

    # Make space for broadened spectrum at boundaries
    fmin = min(frequencies)
    fmax = max(frequencies)
    erange = np.arange(fmin-40*fwhm,fmax+40*fwhm,fwhm/10)

    spectrum = 0.0*erange
    for freq, intensity in zip(frequencies, intensities):

        if function=='Gaussian':
            #normalized gaussian (integral is 1)
            sigma = fwhm / (2 * np.sqrt(2 * np.log(2.)))
            spectrum += intensity / (np.sqrt(2*np.pi)*sigma) * np.exp(-(erange - freq)**2/(2*sigma**2))

            #non normalized f(0)=1
            #x = (erange - freq)/(fwhm/2)
            #spectrum += intensity * np.exp(-np.log(2) * x**2)

        elif function=='Lorentzian':
            #normalized lorentzian (integral is 1)
            gam = fwhm/2
            spectrum += intensity * (gam/np.pi) / ((erange - freq)**2 + gam**2)

            #non normalized f(0)=1
            #spectrum += intensity / (1 + x**2)

    return erange, spectrum
