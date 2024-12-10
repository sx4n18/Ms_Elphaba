## This file contains all the decoders for the 2B RLE encoders
## The decoders will decode the encoded data into the original image data numpy array or save it into a h5 file
## The following decoders are implemented:
## 1. RLE_2B_DEC: This class will decode the RLE_2B/RLE_VP_num_2B encoded data, which follows the format of the RLE_2B encoder.
## 2. RLE_RD_2B_DEC: This class will decode the RLE_RD_2B encoded data, which follows the format of the RLE_RD_2B encoder.
## 3. RLE_AZ_W_RM_2B_DEC: This class will decode the RLE_AZ_W_RM_2B encoded data, which follows the format of the RLE_AZ_W_RM_2B encoder.
## Comments:
## 1. All the input binary file should have even length.
## 2. The decoder RLE_2B_DEC and RLE_RD_2B_DEC will by default take there are 256 pixels in a row of the image.


import warnings

import numpy as np
import h5py



class RLE_2B_DEC:
    '''
    This class will decode the 2B RLE encoded data, which follows the format of the RLE_2B encoder,
    it should read out 2 bytes at a time, the first byte is the run length, and the second byte is the pixel value
    '''
    def __init__(self, pixel_number=256):
        ## This will indicate the number of pixels in a row of the image
        self.pixel_num = pixel_number

    def decode_2_ndarr(self, encoded_data):
        '''
        This function will decode the encoded data in memory
        :param encoded_data: the encoded binary data
        :return: original image data numpy array
        '''
        ## This function will decode the encoded data in memory
        ## The encoded data is a list of tuples
        ## The first element of the tuple is the run length, and the second element is the pixel value
        ## The pixel value should be a 3 bit number
        with open(encoded_data, "rb") as f:
            arry_bin = np.fromfile(f, dtype=np.uint8)
            ## The encoded data is a long list of bytes
            ## Read out 2 bytes a time
            if len(arry_bin) % 2 != 0:
                raise ValueError("The encoded data is not in the correct format!"
                                 "The length of the encoded data should be even!")
            ## The decoded data shall be saved in a 2d numpy array with unknown length, but known width
            decoded_data = np.zeros((1, self.pixel_num), dtype=np.uint8)
            decoded_row_index = 0
            row_element = []
            ## loop through the encoded data
            for i in range(0, len(arry_bin), 2):
                run_length = arry_bin[i]
                pixel_value = arry_bin[i+1]
                ## Append the pixel value to the decoded data
                appendix = np.full((1, run_length), pixel_value, dtype=np.uint8).tolist()
                row_element.extend(appendix)
                ## Check if the row is full
                if len(row_element) == self.pixel_num:
                    if decoded_row_index == 0:
                        decoded_data[decoded_row_index] = np.array(row_element)
                    else:
                        decoded_data = np.vstack((decoded_data, np.array(row_element)))
                    decoded_row_index += 1
                    row_element = []
                elif len(row_element) > self.pixel_num:
                    raise ValueError("The decoded row is too long!")
            return decoded_data

    def decode_2_file(self, encoded_data, decoded_data_path):
        '''
        This function will decode the encoded data into a h5 file
        :param encoded_data: string that names original binary encoded data file
        :param decoded_data_path: string that names the decoded data file
        :return: void
        '''
        ## This function will decode the encoded data into a h5 file
        decoded_numpy_array = self.decode_2_ndarr(encoded_data)
        with h5py.File(decoded_data_path, "w") as f:
            f.create_dataset("intensity_data", data=decoded_numpy_array)


class RLE_RD_2B_DEC:
    '''
    This class will decode the corresponding encoder's encoded data, which is RLE_RD_2B.
    The encoded binary file should be even and the first byte is the run length, and the second byte is the pixel value's
    difference from the previous row.
    '''
    def __init__(self, pixel_number=256):
        ## This will indicate the number of pixels in a row of the image
        self.pixel_num = pixel_number

    def decode_2_ndarr(self, encoded_data):
        '''
        This function will decode the encoded data into an ndarray.
        :param encoded_data: the encoded binary data
        :return: original image data numpy array
        '''
        ## This function will decode the encoded data in memory
        ## The encoded data is a list of tuples
        ## The first element of the tuple is the run length, and the second element is the pixel value
        ## The pixel value should be a 3 bit number
        with open(encoded_data, "rb") as f:
            arry_bin = np.fromfile(f, dtype=np.uint8)
            ## The encoded data is a long list of bytes
            ## Read out 2 bytes a time
            if len(arry_bin) % 2 != 0:
                raise ValueError("The encoded data is not in the correct format!"
                                 "The length of the encoded data should be even!")
            ## The decoded data shall be saved in a 2d numpy array with unknown length, but known width
            decoded_data = np.zeros((1, self.pixel_num), dtype=np.uint8)
            decoded_row_index = 0
            row_element = []
            ## loop through the encoded data
            for i in range(0, len(arry_bin), 2):
                run_length = arry_bin[i]
                pixel_value = arry_bin[i+1]
                ## Append the pixel value to the decoded data
                appendix = np.full((1, run_length), pixel_value, dtype=np.uint8).tolist()
                row_element.extend(appendix)
                ## Check if the row is full
                if len(row_element) == self.pixel_num:
                    if decoded_row_index == 0:
                        decoded_data[decoded_row_index] = np.array(row_element)
                    else:
                        decoded_data = np.vstack((decoded_data, np.array(row_element)))
                        ## The current value is the difference from the previous row, therefore add the previous row and modulate by 8
                        decoded_data[-1] = (decoded_data[-1] + decoded_data[decoded_row_index-1]) % 8
                    decoded_row_index += 1
                    row_element = []
                elif len(row_element) > self.pixel_num:
                    raise ValueError("The decoded row is too long!")
            return decoded_data

    def decode_2_file(self, encoded_data, decoded_data_path):
        '''
        This function will decode the encoded data into a h5 file
        :param encoded_data: string that names original binary encoded data file
        :param decoded_data_path: string that names the decoded data file
        :return: void
        '''
        ## This function will decode the encoded data into a h5 file
        decoded_numpy_array = self.decode_2_ndarr(encoded_data)
        with h5py.File(decoded_data_path, "w") as f:
            f.create_dataset("intensity_data", data=decoded_numpy_array)


class RLE_AZ_W_RM_2B_DEC:
    '''
    This class will decode the corresponding encoder's encoded data, which is RLE_AZ_W_RM_2B.
    The encoded binary file should be even and the first byte is the run length, and the second byte is the pixel value's
    difference from the previous row.
    There are 3 cases of the encoded data:
    1. All zeros in this row:
    The corresponding byte should be:
    [01rr rrrr] [rrrr rrrr]
    The 2 bytes starts with 01, and the rest of the bits are the run length
    2. Normal run length:
    [00vv vrrr] [rrrr rrrr]
    The 2 bytes start with 00, the next 3 bits are the pixel value, and the rest of the bits are the run length
    3. Row marker:
    [1iii iiii] [iiii iiii]
    The 2 bytes start with 1, and the rest of the bits are the row marker, which is the row index.
    This should re-synchronise the pointer to the 2^14 * iii_iiii th row of the image
    '''
    def __init__(self, pixel_number):
        ## This will indicate the number of pixels in a row of the image
        self.pixel_num = pixel_number

    def decode_2_ndarr(self, encoded_data):
        '''
        This function will decode the encoded data into an ndarray.
        :param encoded_data: the encoded binary data
        :return: original image data numpy array
        '''
        ## This function will decode the encoded data in memory
        ## The encoded data is a list of tuples
        ## The first element of the tuple is the run length, and the second element is the pixel value
        ## The pixel value should be a 3 bit number
        with open(encoded_data, "rb") as f:
            arry_bin = np.fromfile(f, dtype=np.uint8)
            ## The encoded data is a long list of bytes
            ## Read out 2 bytes a time
            if len(arry_bin) % 2 != 0:
                raise ValueError("The encoded data is not in the correct format!"
                                 "The length of the encoded data should be even!")
            ## The decoded data shall be saved in a 2d numpy array with unknown length, but known width
            decoded_data = np.zeros((1, self.pixel_num), dtype=np.uint8)
            decoded_row_index = 0
            row_element = []
            ## loop through the encoded data
            for i in range(0, len(arry_bin), 2):
                byte1 = arry_bin[i]
                byte2 = arry_bin[i+1]
                ## Check the first bit of the first byte
                if byte1 >> 7 == 1: # [1xxxx xxxx]
                    ## This is the row marker
                    row_marker = byte1 & 0b0111_1111
                    ## Re-synchronise the pointer to the 2^14 * iii_iiii th row of the image
                    re_sync_row_index = (row_marker << 8 | byte2) << 14 -1
                    ## The row marker should be the row index
                    if decoded_row_index != re_sync_row_index:
                        ## raise the warning if the row index is not synchronised
                        warnings.warn("The row index is not synchronised!"
                                      f"The row index is: {decoded_row_index}"
                                      f"The re-synchronised row index is: {re_sync_row_index}" )
                elif byte1 >> 6 == 1: # [01xx xxxx]
                    ## This is the case where all the pixels in multiple rows are zeros
                    run_length_1 = byte1 & 0b00111111
                    run_length_2 = byte2
                    all_zero_rows = run_length_1 << 8 | run_length_2
                    ## Append the pixel value to the decoded data
                    all_zero_appendix_arr = np.zeros((all_zero_rows, self.pixel_num), dtype=np.uint8)
                    if decoded_row_index == 0:
                        decoded_data = np.vstack((decoded_data, all_zero_appendix_arr))
                        decoded_data = np.delete(decoded_data, 0, axis=0)
                    else:
                        decoded_data = np.vstack((decoded_data, all_zero_appendix_arr))
                    decoded_row_index += all_zero_rows
                else: # [00xx xxxx]
                    ## This is the normal run length case
                    pixel_value = byte1 >> 3
                    run_length = (byte1 & 0b00000111) << 8 | byte2
                    ## Append the pixel value to the decoded data
                    appendix = np.full((1, run_length), pixel_value, dtype=np.uint8).tolist()
                    row_element.extend(appendix)
                    ## Check if the row is full
                    if len(row_element) == self.pixel_num:
                        if decoded_row_index == 0:
                            decoded_data = np.array(row_element)
                        else:
                            decoded_data = np.vstack((decoded_data, np.array(row_element)))
                        decoded_row_index += 1
                        row_element = []
                    elif len(row_element) > self.pixel_num:
                        raise ValueError("The decoded row is longer than expected!"
                                         f"The length of the row is: {len(row_element)}"
                                         f"The expected length is: {self.pixel_num}")
            return decoded_data

    def decode_2_file(self, encoded_data, decoded_data_path):
        '''
        This function will decode the encoded data into a h5 file
        :param encoded_data: string that names original binary encoded data file
        :param decoded_data_path: string that names the decoded data file
        :return: void
        '''
        ## This function will decode the encoded data into a h5 file
        decoded_numpy_array = self.decode_2_ndarr(encoded_data)
        with h5py.File(decoded_data_path, "w") as f:
            f.create_dataset("intensity_data", data=decoded_numpy_array)

