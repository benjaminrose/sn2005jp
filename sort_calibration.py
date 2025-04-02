"""sort_calibration.py"""

from pathlib import Path

from astropy.io import fits

import settings as s


calibration_folder = Path(s.calibration_folder)
cal_files = calibration_folder.glob("*.fits")
for cal_file in cal_files:
    with fits.open(cal_file) as hdul:
        # allow for FITS values to have trailing/leading white space
        if "FLAT" in hdul[0].header[s.obs_type]:
            if hdul[0].header[filter][0] == "J":
                with open(calibration_folder / s.J_flats_file, "a") as f:
                    print(cal_file.name, file=f)
            elif hdul[0].header[filter][0] == "H":
                with open(calibration_folder / s.H_flats_file, "a") as f:
                    print(cal_file.name, file=f)
            else:
                RuntimeWarning(f"Unknown filter for file {cal_file}.")

        elif "DARK" in hdul[0].header[s.obs_type]:
            with open(calibration_folder / s.darks_file, "a") as f:
                print(cal_file.name, file=f)

        else:
            RuntimeWarning(f"Unknown obs_type for file {cal_file}.")
