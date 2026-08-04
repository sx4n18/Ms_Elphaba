######################################################################################
## This will be the class that contains all the classes that can assist the hardware simulation.
## Particularly, it will generate the input pixel data for the compression module simulation.


import numpy as np
import os

class SEQGEN:
    """
    This class will by default generate the pixel data for verilog simulation.
    It will take in the 2d image file path and generate the pixel data for the simulation.

    It shall assume the pixels are grouped by 5, each pixel will have 3-bit quantised value.
    Each data line will handle 4 groups of 5 pixels, which means each data line will take in 4*5*3 = 60 bits of data at each step.
    """


    def __init__(self, n_channels=5, n_pixels_per_channel=5, n_bits_per_pixel=3):
        self.n_channels = n_channels
        self.n_pixels_per_channel = n_pixels_per_channel
        self.n_bits_per_pixel = n_bits_per_pixel
        self.bits_per_data_line = self.n_channels * self.n_pixels_per_channel * self.n_bits_per_pixel
        self.n_pixels_per_data_line = self.n_channels * self.n_pixels_per_channel
        print("Bits per data line:", self.bits_per_data_line)
        print("Pixels per data line:", self.n_pixels_per_data_line)

    def generate_pixel_data(self, export_file_path, img_file_path=None, img_array=None, img_start_col=0):
        """
       This method will generate a simple memory file that contains the pixel data for the simulation.

       It will read from img_file_path, which is a 2D image file.
       Based on the parameters set in the constructor and starting image column, it will slice out the needed width of image.

       Then it will convert the pixel values into hexadecimal format and save it into a memory file that can be used for verilog simulation.
        """

        ## sanity check for the image file
        if img_file_path is None and img_array is None:
            print("Error: No image file path or image array provided.")
            return
        elif img_file_path is not None:
            try:
                img_arr = np.load(img_file_path)
            except Exception as e:
                print("Error loading image file:", e)
                return
        else:
            img_arr = img_array



        ## check if export file path is valid, if not make the directory
        export_dir = os.path.dirname(export_file_path)
        if not os.path.exists(export_dir):
            print("Export directory does not exist:", export_dir)
            os.makedirs(export_dir)

        ## the output file name will be "pixel_data"+str(self.n_channels)+".mem"
        output_file_name = "pixel_data_{}ch_{}pix_per_ch_{}bits_per_pix.mem".format(self.n_channels, self.n_pixels_per_channel, self.n_bits_per_pixel)
        output_file_path = os.path.join(export_dir, output_file_name)

        ## slice out the needed width of image based on the starting column and bits per data line
        img_slice = img_arr[:, img_start_col:img_start_col+self.n_pixels_per_data_line]

        ## convert the pixel values into hexadecimal format and save it into a memory file
        with open(output_file_path, 'w') as f:
            for row in img_slice:
                # each pixel value is an integer, we need to convert it into binary string with n_bits_per_pixel bits,
                # and then concatenate them together for the whole data line
                row_value = 0
                for pixel in row:
                    row_value = (row_value << self.n_bits_per_pixel) | int(pixel)
                # convert the row value into hexadecimal format
                hex_value = hex(row_value)[2:].upper()  # remove the '0x' prefix and convert to uppercase
                f.write(hex_value + '\n')
        print("Pixel data generated and saved to:", output_file_path)
