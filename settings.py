from astropy import visualization as aviz
from astropy.nddata.blocks import block_reduce
from matplotlib import pyplot as plt

calibration_folder = "./cal"
science_folder = "./data"

j_flat = "super_flat_J_G0802.fits"
h_flat = "super_flat_H_G0803.fits"
hot_pixels = "hot_pixels.fits"
dark_60 = "super_dark_60s.fits"
dark_3 = "super_dark_3s.fits"

############
# GEMINI F2
###########

# https://www.gemini.edu/instrumentation/flamingos-2/components

# header keys
obs_type = "OBSTYPE"
filter = "FILTER"
axis = ["NAXIS1", "NAXIS2"]

# F2
gain = 4.4  # +/- 0.35 e-/ADU
linearity = 22000  # ADU
dark_current_60s = gain * 22000 / 60  # 1613 e-/s
read_noise_combined = 5  # e- if >8 images
read_noise_single = 14.3  # e-
dark_current = 0.5  # e-/s/pix
dark_current_exposure_need = read_noise_single / dark_current  # 29 s

# Reduction
# at 1196, 946; 1364, 1115; 
min_pixel = 650
max_pixel = 1665
# min_pixel = 1200
# max_pixel = 1550
# min_pixel = 0
# max_pixel = 2028


##################
# Helper Functions
##################


def show_image(
    image,
    percl=99,
    percu=None,
    is_mask=False,
    figsize=(10, 10),
    cmap="viridis",
    log=False,
    clip=True,
    show_colorbar=True,
    show_ticks=True,
    fig=None,
    ax=None,
    input_ratio=None,
):
    """
    Show an image in matplotlib with some basic astronomically-appropriat stretching.

    Parameters
    ----------
    image
        The image to show
    percl : number
        The percentile for the lower edge of the stretch (or both edges if ``percu`` is None)
    percu : number or None
        The percentile for the upper edge of the stretch (or None to use ``percl`` for both)
    figsize : 2-tuple
        The size of the matplotlib figure in inches
    """
    if percu is None:
        percu = percl
        percl = 100 - percl

    if (fig is None and ax is not None) or (fig is not None and ax is None):
        raise ValueError(
            'Must provide both "fig" and "ax" ' "if you provide one of them"
        )
    elif fig is None and ax is None:
        if figsize is not None:
            # Rescale the fig size to match the image dimensions, roughly
            image_aspect_ratio = image.shape[0] / image.shape[1]
            figsize = (max(figsize) * image_aspect_ratio, max(figsize))

        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # To preserve details we should *really* downsample correctly and
    # not rely on matplotlib to do it correctly for us (it won't).

    # So, calculate the size of the figure in pixels, block_reduce to
    # roughly that,and display the block reduced image.

    # Thanks, https://stackoverflow.com/questions/29702424/how-to-get-matplotlib-figure-size
    fig_size_pix = fig.get_size_inches() * fig.dpi

    ratio = (image.shape // fig_size_pix).max()

    if ratio < 1:
        ratio = 1

    ratio = input_ratio or ratio

    reduced_data = block_reduce(image, ratio)

    if not is_mask:
        # Divide by the square of the ratio to keep the flux the same in the
        # reduced image. We do *not* want to do this for images which are
        # masks, since their values should be zero or one.
        reduced_data = reduced_data / ratio**2

    # Of course, now that we have downsampled, the axis limits are changed to
    # match the smaller image size. Setting the extent will do the trick to
    # change the axis display back to showing the actual extent of the image.
    extent = [0, image.shape[1], 0, image.shape[0]]

    if log:
        stretch = aviz.LogStretch()
    else:
        stretch = aviz.LinearStretch()

    norm = aviz.ImageNormalize(
        reduced_data,
        interval=aviz.AsymmetricPercentileInterval(percl, percu),
        stretch=stretch,
        clip=clip,
    )

    if is_mask:
        # The image is a mask in which pixels should be zero or one.
        # block_reduce may have changed some of the values, so reset here.
        reduced_data = reduced_data > 0
        # Set the image scale limits appropriately.
        scale_args = dict(vmin=0, vmax=1)
    else:
        scale_args = dict(norm=norm)

    im = ax.imshow(
        reduced_data,
        origin="lower",
        cmap=cmap,
        extent=extent,
        aspect="equal",
        **scale_args
    )

    if show_colorbar:
        # I haven't a clue why the fraction and pad arguments below work to make
        # the colorbar the same height as the image, but they do....unless the image
        # is wider than it is tall. Sticking with this for now anyway...
        # Thanks: https://stackoverflow.com/a/26720422/3486425
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        # In case someone in the future wants to improve this:
        # https://joseph-long.com/writing/colorbars/
        # https://stackoverflow.com/a/33505522/3486425
        # https://matplotlib.org/mpl_toolkits/axes_grid/users/overview.html#colorbar-whose-height-or-width-in-sync-with-the-master-axes

    if not show_ticks:
        ax.tick_params(
            labelbottom=False, labelleft=False, labelright=False, labeltop=False
        )
