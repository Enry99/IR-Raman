#!/usr/bin/env python3
#


import numpy as np

def get_broadened_spectrum(frequencies : np.ndarray,
                           intensities : np.ndarray,
                           fwhm : float = 10.0,
                           function : str ='lorentz'):
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

    if fwhm < 1e-8:
        raise ValueError("FWHM must be greater than 0.")

    # Normalize intensities
    #intensities /= np.max(np.abs(intensities))

    # Make space for broadened spectrum at boundaries
    fmin = max(min(frequencies) - 5*fwhm, 0)
    fmax = max(frequencies) + 5*fwhm
    erange = np.arange(fmin, fmax, fwhm/10)

    spectrum = 0.0*erange
    for freq, intensity in zip(frequencies, intensities):

        if function=='gauss':
            #normalized gaussian (integral is 1)
            sigma = fwhm / (2 * np.sqrt(2 * np.log(2.)))
            spectrum += intensity / (np.sqrt(2*np.pi)*sigma) * np.exp(-(erange - freq)**2/(2*sigma**2))

            #non normalized f(0)=1
            #x = (erange - freq)/(fwhm/2)
            #spectrum += intensity * np.exp(-np.log(2) * x**2)

        elif function=='lorentz':
            #normalized lorentzian (integral is 1)
            gam = fwhm/2
            spectrum += intensity * (gam/np.pi) / ((erange - freq)**2 + gam**2)

            #non normalized f(0)=1
            #spectrum += intensity / (1 + x**2)

        else:
            raise ValueError("Function must be 'gauss' or 'lorentz'.")

    return erange, spectrum
