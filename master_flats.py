"""super_flats.py

https://doc.astro-wise.org/man_howto_flat.html#combining-flats-into-a-master-flat
normalize raw flats, then average with sigma clipping
"""

from pathlib import Path

from astropy import units as u
from astropy.io import fits
from astropy.nddata import CCDData
from astropy.stats import mad_std
import ccdproc as ccdp
import matplotlib.pyplot as plt
import numpy as np

import settings as s


def inv_median(a):
    return 1 / np.median(a)


calibration_folder = Path(s.calibration_folder)
imgs = ccdp.ImageFileCollection(calibration_folder)
filters = set(imgs.filter(obstype="flat").summary["filter"]) # seems to change order?
filters = ["J_G0802", "H_G0803"]

print(imgs.filter(obstype="flat").summary["file", "obstype", "exptime", "filter"])
# sci_image = ccdp.ImageFileCollection(s.science_folder)
# print(sci_image.summary["obstype", "exptime", "filter"])
# print(filters)

dark_hdul_60 = fits.open(calibration_folder / s.dark_60)
dark_60 = CCDData(dark_hdul_60[0].data[0], unit=u.adu)
dark_hdul_3 = fits.open(calibration_folder / s.dark_3)
dark_3 = CCDData(dark_hdul_3[0].data[0], unit=u.adu)
darks = [dark_60, dark_3]
dark_hduls = [dark_hdul_60, dark_hdul_3]

for filter, dark, dark_hdul in zip(filters, darks, dark_hduls):
    to_combine = []
    # somehow, half the J band flats are darks?
    for filename in imgs.filter(obstype="flat", filter=filter).files[:5]:
        flat_hdul = fits.open(filename)
        a_flat = CCDData(flat_hdul[1].data[0], unit=u.adu)

        a_flat_reduced = ccdp.subtract_dark(
            a_flat,
            dark,
            data_exposure=flat_hdul[0].header["EXPTIME"] * u.s,
            dark_exposure=dark_hdul[0].header["EXPTIME"] * u.s,
            scale=False,
        )

        a_flat_reduced = ccdp.trim_image(
            a_flat_reduced[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel]
        )
        to_combine.append(a_flat_reduced)

    combined_flat = ccdp.combine(
        to_combine,
        method="average",
        scale=inv_median,
        sigma_clip=True,
        sigma_clip_low_thresh=5,
        sigma_clip_high_thresh=5,
        sigma_clip_func=np.ma.median,
        signma_clip_dev_func=mad_std,
    )
    s.show_image(a_flat_reduced.data)
    plt.title(filter)
    combined_flat.write(
        calibration_folder / f"super_flat_{filter}.fits", overwrite=True
    )
