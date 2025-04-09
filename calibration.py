from pathlib import Path

from astropy import units as u
from astropy.io import fits
from astropy.nddata import CCDData
from astropy.stats import mad_std
from astropy.wcs import WCS
import ccdproc as ccdp
import matplotlib.pyplot as plt
import numpy as np

import settings as s

calibration_folder = Path(s.calibration_folder)

cal_imgs = ccdp.ImageFileCollection(s.calibration_folder)
sci_imgs = ccdp.ImageFileCollection(s.science_folder)
filters = list(set(sci_imgs.summary["filter"]))  # changes order?
filters = ["J_G0802", "H_G0803"]
print(sci_imgs.summary["filter", "exptime", "file"])

for filter in filters:
    print(filter)
    reprojected = []
    base_wcs = None
    
    for filename in sci_imgs.filter(filter=filter).files:
        with fits.open(filename) as hdul_sci:
            # only keep the celestial components (drop any unneeded 3rd axes)
            wcs = WCS(hdul_sci[1].header).celestial
            sci = CCDData(hdul_sci[1].data[0], unit=u.adu, wcs=wcs)
        if base_wcs is None:
            base_wcs = wcs
        sci = ccdp.trim_image(sci[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
            
        with fits.open(calibration_folder / s.dark_3) as hdul_dark:
            dark = CCDData(hdul_dark[0].data[0], unit=u.adu)
        dark = ccdp.trim_image(dark[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
    
        with fits.open(calibration_folder / f"super_flat_{filter}.fits") as hdul_flat:
            flat = CCDData(hdul_flat[0].data, unit=u.adu)
    
        with fits.open(calibration_folder / "hot_pixels.fits") as hdul_hot:
            hot = CCDData(hdul_hot[0].data, unit=u.dimensionless_unscaled)
        hot = ccdp.trim_image(hot[s.min_pixel : s.max_pixel, s.min_pixel : s.max_pixel])
        hot.data = hot.data.astype("bool")
    
        sci_dark_subtracted = ccdp.subtract_dark(
            sci,
            dark,
            data_exposure=3 * u.s,
            dark_exposure=3 * u.s,
            scale=False,
        )
        
        sci_flat_corrected = ccdp.flat_correct(sci_dark_subtracted, flat)
        
        sci_reprojected = ccdp.wcs_project(sci_flat_corrected, base_wcs)
        reprojected.append(sci_reprojected)
    
    combiner = ccdp.Combiner(reprojected)
    combiner.sigma_clipping()
    
    sci_final = combiner.average_combine()
    sci_final.wcs = base_wcs
    sci_final.write(f"SN2005jp_{filter}.fits", overwrite=True)
