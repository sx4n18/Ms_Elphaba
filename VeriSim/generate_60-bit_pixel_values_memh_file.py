################################################################################
## This script generates a .mem file containing 60-bit pixel values for testing.
## It will use the SEQGEN class to read a 2D image file, convert the pixel values
## into hexadecimal format, and save it into a memory file for verilog simulation.

from Sim.SeqGen import SEQGEN
import numpy as np


## Instantiate the SEQGEN class with 4 channels, 5 pixels per channel, and 3 bits per pixel
seq_gen = SEQGEN(n_channels=8, n_pixels_per_channel=5, n_bits_per_pixel=3)

## load the 2D image file path and specify the export file path
npz_image_file = "/home/j05003sx/oap-compression/Ms_Elphaba/generate_my_own_data/Quan_3b_data/pixel_20um/20K_runs_3b_quantised_011_500cc_30um_28_Jan_2026.npz"
loaded_npz_img = np.load(npz_image_file)
print("Loaded image keys:", loaded_npz_img.files)  # Print the keys in the loaded npz file to verify the image data
img_02 = loaded_npz_img['arm_02'].T  # Transpose the image to get the correct orientation
print("Image shape:", img_02.shape)  # Print the shape of the image to
img_006 = loaded_npz_img['arm_006'].T
img_008 = loaded_npz_img['arm_008'].T
img_012 = loaded_npz_img['arm_012'].T
img_016 = loaded_npz_img['arm_016'].T


export_path = "./Gen_mem/Theta_011/"

## generate the pixel data memory file using the SEQGEN class
seq_gen.generate_pixel_data(img_array=img_02, export_file_path=export_path, img_start_col=0)

