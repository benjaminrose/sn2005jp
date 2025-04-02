"""
https://gemini-iraf-flamingos-2-cookbook.readthedocs.io/en/latest/Processing.html
https://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/03-02-Real-dark-current-noise-and-other-artifacts.html
"""

from pathlib import Path

import settings as s

from ccdproc import ImageFileCollection

from astropy.io import fits
from astropy import units as u
from astropy.nddata import CCDData
from ccdproc import Combiner

import matplotlib.pyplot as plt

calibration_folder = Path(s.calibration_folder)
imgs = ImageFileCollection(calibration_folder)

# print(im_collection.filter(obstype="dark").summary["file", "obstype", "exptime"])

print(f"There are {len(imgs.filter(obstype='DARK', exptime=60).files)} 60s darks.")
print(f"There are {len(imgs.filter(obstype='DARK', exptime=3).files)} 3s darks.")


for time in [3, 60]:
    to_combine = []
    for filename in imgs.filter(obstype="DARK", exptime=time).files:
        fits.open(filename)
        hdul = fits.open(imgs.filter(obstype="DARK").files[0])
        to_combine.append(CCDData(hdul[1].data, unit=u.adu))
    combiner = Combiner(to_combine)
    combiner.sigma_clipping()
    combined_average = combiner.average_combine()

    combined_average.write(calibration_folder / f"super_dark_{time}s.fits")
    # s.show_image(combined_average[0])
    # plt.show()
