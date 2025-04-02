"""
https://gemini-iraf-flamingos-2-cookbook.readthedocs.io/en/latest/Processing.html
https://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/03-02-Real-dark-current-noise-and-other-artifacts.html
"""

from pathlib import Path

from astropy.io import fits
from astropy import units as u
from astropy.nddata import CCDData
from ccdproc import Combiner, ImageFileCollection

import settings as s

calibration_folder = Path(s.calibration_folder)
imgs = ImageFileCollection(calibration_folder)

print(imgs.filter(obstype="dark").summary["file", "obstype", "exptime"])

times = [3, 60] # 3 second exposures mostly measure read noise

for time in times:
    to_combine = []
    for filename in imgs.filter(obstype="DARK", exptime=time).files:
        with fits.open(filename) as hdul:
            to_combine.append(CCDData(hdul[1].data, unit=u.adu))
    combiner = Combiner(to_combine)

    # Iteratively sigma clip till no new clips
    old_n_masked = 0  # dummy value to make loop execute at least once
    new_n_masked = combiner.data_arr.mask.sum()
    while new_n_masked > old_n_masked:
        combiner.sigma_clipping()
        old_n_masked = new_n_masked
        new_n_masked = combiner.data_arr.mask.sum()

    combined_average = combiner.average_combine()
    dark_current = combined_average.multiply(s.gain / time)  # e/s
    for key in [
        "INSTRUME",
        "TELESCOP",
        "OBJECT",
        # "OBSTYPE",
        "DATE-OBS",
        "READMODE",
        "EXPTIME",
        "GAIN",
        "MJD-OBS",
    ]:
        combined_average.header[key] = hdul[0].header[key]
        dark_current.header[key] = hdul[0].header[key]
    print(f"Dark Current min: {dark_current.data.flatten().min()} e-/s/pix")
    print(f"Dark Current mean: {dark_current.data.flatten().mean()} e-/s/pix")
    print(f"Dark Current max: {dark_current.data.flatten().max()} e-/s/pix")

    combined_average.write(
        calibration_folder / f"super_dark_{time}s.fits", overwrite=True
    )

    if time > 50:  # select time = 60s, but with floats
        hot_pixels = dark_current.copy()
        hot_pixels.data = (dark_current.data[0] > 500).astype(int)
        hot_pixels.write(calibration_folder / "hot_pixels.fits", overwrite=True)
