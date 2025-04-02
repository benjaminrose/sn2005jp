from pathlib import Path

from astropy import units as u
from astropy.io import fits
from astropy.nddata import CCDData
from astropy.stats import mad_std
import ccdproc as ccdp
import matplotlib.pyplot as plt
import numpy as np

import settings as s

calibration_folder = Path(s.calibration_folder)

cal_imgs = ccdp.ImageFileCollection(s.calibration_folder)
sci_imgs = ccdp.ImageFileCollection(s.science_folder)
filters = list(set(sci_imgs.summary["filter"]))  # changes order?
filters = ["J_G0802", "H_G0803"]
# print(sci_imgs.summary["filter", "exptime", "file"])

filter = filters[0]
print(filter)
for filename in sci_imgs.filter(filter=filter).files:
    with fits.open(filename) as hdul_sci:
        sci = CCDData(hdul_sci[1].data[0], unit=u.adu)
    sci = ccdp.trim_image(sci[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
    s.show_image(sci.data, percl=99)
    plt.title("sci")
    print("sci max:", sci.data.max())

    with fits.open(calibration_folder / s.dark_60) as hdul_dark:
        dark = CCDData(hdul_dark[0].data[0], unit=u.adu)
    dark = ccdp.trim_image(dark[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
    s.show_image(dark.data, percl=99)
    plt.title("dark")
    print("dark max:", dark.data.max())

    with fits.open(calibration_folder / f"super_flat_{filter}.fits") as hdul_flat:
        flat = CCDData(hdul_flat[0].data, unit=u.adu)
    # s.show_image(flat.data)
    # plt.title("flat")

    with fits.open(calibration_folder / "hot_pixels.fits") as hdul_hot:
        hot = CCDData(hdul_hot[0].data, unit=u.dimensionless_unscaled)
    hot = ccdp.trim_image(hot[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
    hot.data = hot.data.astype("bool")

    sci_dark_subtracted = ccdp.subtract_dark(
        sci,
        dark,
        data_exposure=hdul_sci[0].header["EXPTIME"] * u.s,
        dark_exposure=hdul_dark[0].header["EXPTIME"] * u.s,
        scale=False,
    )
    # sci_dark_subtracted = sci.copy()
    # sci_dark_subtracted.data = sci.data - dark.data
    
    s.show_image(sci_dark_subtracted.data, percl=99)
    plt.title("dark subtracted")
    sci_final = ccdp.flat_correct(sci_dark_subtracted, flat)
    print("final max:", sci_final.data.max())
    s.show_image(sci_final.data, percl=99)
    plt.title("reduced")

    # sci_other = (sci.data - dark.data) / flat.data
    # s.show_image(sci_other)
    # plt.title("manual")
    sci_final.write(f"SN2005jp_{filter}.fits", overwrite=True)

#     plt.show()
#     from sys import exit
# 
#     exit()
