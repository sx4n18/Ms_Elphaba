## This is the newly defined compression encoder, which is a run-length encoder where
## each row will be encoded into 2 bytes. All the variations of 2-byte run-length
## encoders will be defined in this file.
## The encoders defined in this file are:
## 1. RLE_2B: simple 2 byte run-length encoder
## 2. RLE_RD_2B: by comparison, this encoder will encode the row difference data
## 3. RLE_AZ_W_RM_2B: this encoder will consider special cases of all zero rows and throw row marker data
## 4. RLE_VP_num_2B: this encoder will support variable number of pixels in a row
## Comments:
## 1. All the encoders expect an input of a 2D numpy array where each row is encoded separately.
## 2. Each row of the input data is expected to be 256 elements long, this only applies RLE_2B and RLE_RD_2B.
## 3. Value of each element should have a range of 0-7.
###########################################################################################################

import warnings
import numpy as np
import struct
import io
from typing import List, Tuple
import os


class RLE_2B:
    """
    Simple 2 byte run-length encoder.

    IMPORTANT: This encoder will by default consider the input data is 256 elements wide.

    The encoder will encode the given data using a simple 2 byte run-length encoding scheme.
    The returned byte follows the following format:
    [rrrr rrrr]    [XXXX Xvvv]
    where:
    The first 8 bits represent the run length of the value.
    The following 8 bits represent the value, but the range is only within 0-7, only 3 bits are used.
    Therefore, the XXXX X stands for all zeros.
    """
    @staticmethod
    def encode_in_memory(data: np.ndarray) -> bytes:
        """
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # Iterate over each row in the data
            for row in data:
                # Initialize the run length and the current value
                run_length = 0
                current_value = row[0]
                # Iterate over each value in the row
                for value in row:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        byte_stream.write(struct.pack("B", run_length))
                        byte_stream.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                byte_stream.write(struct.pack("B", run_length))
                byte_stream.write(struct.pack("B", current_value))
            # Return the encoded data as bytes
            return byte_stream.getvalue()

    @staticmethod
    def encode_2_file(data: np.ndarray, file_name: str):
        """
        Encode the given data using a simple 2 byte run-length encoding scheme
        and write the encoded data to a file.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Encode the data in memory
        encoded_data = RLE_2B.encode_in_memory(data)
        # Write the encoded data to the file
        with open(file_name, "wb") as file:
            file.write(encoded_data)
        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")

    @staticmethod
    def get_compression_ratio(data: np.ndarray, bits_per_pixel=3):
        """
        Calculate the compression ratio of the given data.
        :param data:
        :return: compression percentage
        """
        # Calculate the number of bytes required to store the original data
        original_size = data.size*bits_per_pixel/8
        # Encode the data using the run-length encoder
        encoded_data = RLE_2B.encode_in_memory(data)
        # Calculate the number of bytes required to store the encoded data
        encoded_size = len(encoded_data)
        # Calculate the compression ratio
        compression_ratio = (original_size - encoded_size) / original_size * 100
        return compression_ratio

    @staticmethod
    def encode_2_file_straight(data:np.ndarray, file_name: str):
        """
        Encode the given data using a simple 2 byte run-length encoding scheme
        and write the encoded data to a file.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Create a byte stream to write the encoded data
        with open(file_name, "wb") as file:
            # Iterate over each row in the data
            for row in data:
                # Initialize the run length and the current value
                run_length = 0
                current_value = row[0]
                # Iterate over each value in the row
                for value in row:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        file.write(struct.pack("B", run_length))
                        file.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                file.write(struct.pack("B", run_length))
                file.write(struct.pack("B", current_value))

        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")



class RLE_RD_2B(RLE_2B):
    '''
    This is a variation of the 2-byte run-length encoder. This encoder will encode the row difference data instead of the original data.
    The encoder will first calculate the difference between the consecutive elements in the row and then encode the difference data using a simple 2 byte run-length encoding scheme.

    Given two rows of arrays as in data[0:1][:], the difference will be calculated as:
    data[1][:] = mod(data[0][:]+diff[1][:], 8)
    where mod is the modulo by 8 operation.
    So the diff should be calculated as:
    diff[1] = data[1][:] + (8 - data[0][:])

    As for the first row, the diff will be the same as the row.
    diff[0] = data[0][:]
    '''

    @staticmethod
    def encode_in_memory(data: np.ndarray) -> bytes:
        """
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # Iterate over each row in the data
            for i in range(len(data)-1):
                if i == 0:
                    diff = data[0]
                else:
                    # Calculate the difference between the consecutive rows
                    diff = (data[i+1] + (8 - data[i])) % 8
                # Initialize the run length and the current value
                run_length = 0
                current_value = diff[0]
                # Iterate over each value in the row
                for value in diff:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        byte_stream.write(struct.pack("B", run_length))
                        byte_stream.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                byte_stream.write(struct.pack("B", run_length))
                byte_stream.write(struct.pack("B", current_value))
            # Return the encoded data as bytes
            return byte_stream.getvalue()

    @staticmethod
    def encode_2_file(data: np.ndarray, file_name: str):
        """
        Encode the given data using a simple 2 byte run-length encoding scheme
        and write the encoded data to a file.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Encode the data in memory
        encoded_data = RLE_RD_2B.encode_in_memory(data)
        # Write the encoded data to the file
        with open(file_name, "wb") as file:
            file.write(encoded_data)
        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")

    @staticmethod
    def get_compression_ratio(data: np.ndarray, bits_per_pixel=3):
        """
        Calculate the compression ratio of the given data.
        :param data:
        :return: compression percentage
        """
        # Calculate the number of bytes required to store the original data
        original_size = data.size*bits_per_pixel/8
        # Encode the data using the run-length encoder
        encoded_data = RLE_RD_2B.encode_in_memory(data)
        # Calculate the number of bytes required to store the encoded data
        encoded_size = len(encoded_data)
        # Calculate the compression ratio
        compression_ratio = (original_size - encoded_size) / original_size * 100
        return compression_ratio

    @staticmethod
    def encode_2_file_straight(data:np.ndarray, file_name: str):
        '''
        Encode the given data using a 2 byte run-length row-difference encoding scheme
        :param data: the initial data to be encoded
        :param file_name: expected file name to be saved
        :return: void
        '''

        # Create a byte stream to write the encoded data
        with open(file_name, "wb") as file:
            # Iterate over each row in the data
            for i in range(len(data)-1):
                if i == 0:
                    diff = data
                else:
                    # Calculate the difference between the consecutive rows
                    diff = (data[i+1] + (8 - data[i])) % 8
                # Initialize the run length and the current value
                run_length = 0
                current_value = diff[0]
                # Iterate over each value in the row
                for value in diff:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        file.write(struct.pack("B", run_length))
                        file.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                file.write(struct.pack("B", run_length))
                file.write(struct.pack("B", current_value))

        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")



class RLE_AZ_W_RM_2B(RLE_2B):
    '''
    This is another variation of 2-byte run-length encoder. This encoder will consider special cases of all zero rows and throw row marker data.

    There are 3 types of 2-byte data:
    1. Normal run length data:
    [00vv vrrr] [rrrr rrrr]
    where: the first byte start with 2 zeros, followed by 3 bits of value and 11 bits of run length, the 11 bits run length's LS 8bit
    is stored in the second byte, and the MS 3 bits are stored in the first byte.
    2. All zero row data:
    [01rr rrrr] [rrrr rrrr]
    where: the first byte start with 01, followed by 14 bits of run length of the row, the 14 bits run length's LS 8bit is stored in the
    second byte, and the MS 6 bits are stored in the first byte.
    3. Row marker data:
    [1iii iiii] [iiii iiii]
    where: the first byte start with 1, followed by 15 bits of row marker data, the 15 bits row marker data's LS 8bit is stored in the
    second byte, and the MS 7 bits are stored in the first byte.
    This row marker will be sent out every 2^14 rows, before sending over the row marker, the encoder will send out the all zero row
    data and also the normal run length data.
    '''

    @staticmethod
    def encode_in_memory(data: np.ndarray) -> bytes:
        """
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # Initialize the all zero row run length
            all_zero_row_run_length = 0
            # Initialize the row marker data
            row_marker_data = 0
            # Initialize the row count
            row_count = 0
            # Iterate over each row in the data
            for row in data:
                # If the row is all zeros, increment the all zero row run length
                if np.all(row == 0):
                    all_zero_row_run_length += 1
                    # if the all zero row run length is greater than 2^14, write the all zero row run length data to the byte stream
                    if all_zero_row_run_length >= 2**14 - 1:
                        byte_stream.write(struct.pack("B", 0b0100_0000 | (all_zero_row_run_length >> 8)))
                        byte_stream.write(struct.pack("B", all_zero_row_run_length & 0xFF))
                        # Reset the all zero row run length
                        all_zero_row_run_length = 0
                # If the row is not all zeros, check if the all zero row run length is greater than 0
                else:
                    # if the all zero row run length is greater than 0, write the AZ run length before encoding the row data
                    if all_zero_row_run_length > 0:
                        # Write the all zero row run length data to the byte stream
                        byte_stream.write(struct.pack("B", 0b0100_0000 | (all_zero_row_run_length >> 8)))
                        byte_stream.write(struct.pack("B", all_zero_row_run_length & 0xFF))
                        # Reset the all zero row run length
                        all_zero_row_run_length = 0
                    # If the row is not all zeros, encode the row data
                    # Initialize the run length and the current value
                    run_length = 0
                    current_value = row[0]
                    # Iterate over each value in the row
                    for value in row:
                        # If the value is the same as the current value, increment the run length
                        if value == current_value:
                            run_length += 1
                        # If the value is different, write the run length and the value to the byte stream
                        else:
                            byte_stream.write(struct.pack("B", 0b0000_0000 | ((current_value << 3) | (run_length >> 8))))
                            byte_stream.write(struct.pack("B", run_length & 0xFF))
                            # Update the current value and reset the run length
                            current_value = value
                            run_length = 1
                    # Write the final run length and value to the byte stream
                    byte_stream.write(struct.pack("B", 0b0000_0000 | ((current_value << 3) | (run_length >> 8))))
                    byte_stream.write(struct.pack("B", run_length & 0xFF))
                # Increment the row count
                row_count += 1
                # If the row count is a multiple of 2^14, write the row marker data divided by 2^14 to the byte stream
                if row_count % 2**14 == 0:
                    row_marker_data = row_count >>14
                    byte_stream.write(struct.pack("B", 0b1000_0000 | (row_marker_data >> 8)))
                    byte_stream.write(struct.pack("B", row_marker_data & 0xFF))
            # write out the remaining all zero row run length data
            if all_zero_row_run_length > 0:
                byte_stream.write(struct.pack("B", 0b0100_0000 | (all_zero_row_run_length >> 8)))
                byte_stream.write(struct.pack("B", all_zero_row_run_length & 0xFF))
            # Return the encoded data as bytes
            return byte_stream.getvalue()

    @staticmethod
    def encode_2_file(data: np.ndarray, file_name: str):
        """
        Encode the given data using a simple 2 byte run-length encoding scheme
        and write the encoded data to a file.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Encode the data in memory
        encoded_data = RLE_AZ_W_RM_2B.encode_in_memory(data)
        # Write the encoded data to the file
        with open(file_name, "wb") as file:
            file.write(encoded_data)
        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")

    @staticmethod
    def get_compression_ratio(data: np.ndarray, bits_per_pixel=3):
        """
        Calculate the compression ratio of the given data.
        :param data:
        :return: compression percentage
        """
        # Calculate the number of bytes required to store the original data
        original_size = data.size*bits_per_pixel/8
        # Encode the data using the run-length encoder
        encoded_data = RLE_AZ_W_RM_2B.encode_in_memory(data)
        # Calculate the number of bytes required to store the encoded data
        encoded_size = len(encoded_data)
        # Calculate the compression ratio
        compression_ratio = (original_size - encoded_size) / original_size * 100
        return compression_ratio

    @staticmethod
    def encode_2_file_straight(data:np.ndarray, file_name: str):
        # This method is not going to be implemented
        warnings.warn("This method is not going to be implemented\n"
                      "Plese use the encode_2_file(data, file_name) method instead.\n"
                      "data: the 2d numpy array to be encoded\n"
                      "file_name: the file name to be saved\n")
        pass



class RLE_VP_num_2B(RLE_2B):
    '''
    This is a variation of the original RLE_2B encoder, this encoder will support variable number of pixels in a row.
    The encoder expects the parameter num_pixels to instantiate this encoder.
    '''
    def __init__(self, num_pixels: int):
        self.num_pixels = num_pixels

    def encode_in_memory(self, data: np.ndarray) -> bytes:
        """
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each row is encoded
        separately.
        """
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # Iterate over each row in the data
            for row in data:
                # Initialize the run length and the current value
                run_length = 0
                current_value = row[0]
                # Iterate over each value in the row
                for value in row:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                        # If the run length reaches the maximum number of pixels, write the run length and the value to the byte stream
                        if run_length == 255:
                            byte_stream.write(struct.pack("B", run_length))
                            byte_stream.write(struct.pack("B", current_value))
                            run_length = 0
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        byte_stream.write(struct.pack("B", run_length))
                        byte_stream.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                byte_stream.write(struct.pack("B", run_length))
                byte_stream.write(struct.pack("B", current_value))
            # Return the encoded data as bytes
            return byte_stream.getvalue()

    def encode_2_file(self, data: np.ndarray, file_name: str):
        '''
        Encode the given data using a simple 2 byte run-length encoding scheme
        :param data: numpy 2D array to be encoded
        :param file_name: saved file name string
        :return: void
        '''
        # Encode the data in memory
        encoded_data = self.encode_in_memory(data)
        # Write the encoded data to the file
        if not os.path.exists(file_name):
            os.makedirs(file_name)
        with open(file_name, "wb") as file:
            file.write(encoded_data)
        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")

    def get_compression_ratio(self, data: np.ndarray, bits_per_pixel=3):
        """
        Calculate the compression ratio of the given data.
        :param data:
        :return: compression percentage
        """
        # Calculate the number of bytes required to store the original data
        original_size = data.size*bits_per_pixel/8
        # Encode the data using the run-length encoder
        encoded_data = self.encode_in_memory(data)
        # Calculate the number of bytes required to store the encoded data
        encoded_size = len(encoded_data)
        # Calculate the compression ratio
        compression_ratio = (original_size - encoded_size) / original_size * 100
        return compression_ratio

    def encode_2_file_straight(self, data:np.ndarray, file_name: str):
        '''
        :param data:
        :param file_name:
        :return:
        '''
        # Create a byte stream to write the encoded data
        with open(file_name, "wb") as file:
            # Iterate over each row in the data
            for row in data:
                # Initialize the run length and the current value
                run_length = 0
                current_value = row[0]
                # Iterate over each value in the row
                for value in row:
                    # If the value is the same as the current value, increment the run length
                    if value == current_value:
                        run_length += 1
                        # If the run length reaches the maximum number of pixels, write the run length and the value to the byte stream
                        if run_length == 255:
                            file.write(struct.pack("B", run_length))
                            file.write(struct.pack("B", current_value))
                            run_length = 0
                    # If the value is different, write the run length and the value to the byte stream
                    else:
                        file.write(struct.pack("B", run_length))
                        file.write(struct.pack("B", current_value))
                        # Update the current value and reset the run length
                        current_value = value
                        run_length = 1
                # Write the final run length and value to the byte stream
                file.write(struct.pack("B", run_length))
                file.write(struct.pack("B", current_value))
        # report the binary file size
        print(f"Binary file size: {os.path.getsize(file_name)} bytes\n")


class mini_col_RLE_2B_encoder:
    '''
    This is the 2-byte run length encoder that operates on each column instead of the rows.
    The max number of columns is 256, the encoder will encode the column data separately.
    Each data packet should be 3 bytes long.
    '''

    def __init__(self, col_index, current_value, run_length = 1):
        # limit the column index from 0 to 255
        if col_index < 0 or col_index > 255:
            raise ValueError("The column index should be within the range of 0-255")
        self.col_index = col_index
        self.current_value = current_value
        self.run_length = run_length

    def encode_on_live_data(self, data) -> bytes:
        '''
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each column is encoded separately.
        '''
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # if the value is the same as the current value, increment the run length
            if data == self.current_value:
                self.run_length += 1
            # If the value is different, write the index, run length and the value to the byte stream
            else:
                byte_stream.write(struct.pack("B", self.col_index))
                byte_stream.write(struct.pack("B", 0b0000_0000 | ((self.current_value << 4) | (self.run_length >> 8))))
                byte_stream.write(struct.pack("B", self.run_length & 0xFF))
                # Update the current value and reset the run length
                self.current_value = data
                self.run_length = 1
            # Return the encoded data as bytes
            return byte_stream.getvalue()

    def encode_on_a_whole_column(self, data: np.ndarray) -> bytes:
        '''
        Encode the given column of data using a simple 2 byte run-length encoding scheme.
        :param data:
        :return:
        '''
        row_mark_data = 0
        # Create a byte stream to write the encoded data
        with io.BytesIO() as byte_stream:
            # check if the first element is the same as the initialised value, if not, report the warning and reset the current value
            if data[0] != self.current_value:
                warnings.warn("The first element is different from the initialised current value, resetting the current value...\n")
                self.current_value = data[0]
            # Iterate over each value in the column
            for number, value in enumerate(data):
                if number == 0:
                    continue
                # if the number marks the 2**12 column, write the row marker data to the byte stream
                if (number+1) % 2**12 == 0:
                    byte_stream.write(struct.pack("B", self.col_index))
                    byte_stream.write(struct.pack("B", 0b1000_0000 | (row_mark_data >> 8)))
                    byte_stream.write(struct.pack("B", row_mark_data & 0xFF))
                    row_mark_data += 1
                # if the value is the same as the current value, increment the run length
                if value == self.current_value:
                    self.run_length += 1
                # If the value is different, write the index, run length and the value to the byte stream
                else:
                    byte_stream.write(struct.pack("B", self.col_index))
                    byte_stream.write(struct.pack("B", 0b0000_0000 | ((self.current_value << 4) | (self.run_length >> 8)))
                                      )
                    byte_stream.write(struct.pack("B", self.run_length & 0xFF))
                    # Update the current value and reset the run length
                    self.current_value = value
                    self.run_length = 1
            # Write the final run length and value to the byte stream
            byte_stream.write(struct.pack("B", self.col_index))
            byte_stream.write(struct.pack("B", 0b0000_0000 | ((self.current_value << 4) | (self.run_length >> 8))))
            byte_stream.write(struct.pack("B", self.run_length & 0xFF))
            # Return the encoded data as bytes
            return byte_stream.getvalue()







class RLE_Col_2B:
    '''
    This is a 2-byte run length encoder that operates on each column instead of the rows.
    This shall operate similarly to the RLE_2B encoder, there are 2 cases to consider:
    1. Normal run length data:
    [cccc cccc] column index
    [0vvv rrrr] [rrrr rrrr]
    where: the first byte start with 0, followed by 3 bits of value and 12 bits of run length, the 12 bits run length's LS 8bit
    is stored in the second byte, and the MS 4 bits are stored in the first byte.
    2. Row marker data:
    [cccc cccc] column index
    [1iii iiii] [iiii iiii]
    where: the first byte start with 1, followed by 15 bits of row marker data, the 15 bits row marker data's LS 8bit is stored in the
    second byte, and the MS 7 bits are stored in the first byte.
    This row marker will be sent out every 2^12 columns, before sending over the row marker, the encoder will send out the normal run
    '''

    def __init__(self, num_columns: int, num_sub_channels: int = 1):
        self.num_pixels = num_columns
        self.encoders = []
        self.num_sub_channels = num_sub_channels


    def init_encoders(self, data):
        '''
        Initialise the encoders for each column
        :param data: the whole data array, or just the first row of the data
        '''
        if data.ndim == 1:
            data = np.expand_dims(data, axis=0)
        if self.num_pixels > 256:
            warnings.warn("The number of columns is greater than 256, the image will be broken into sub-channels\n")
            self.num_sub_channels = self.num_pixels // 256
            for i in range(self.num_sub_channels):
                sub_chan_encoders = []
                for j in range(256):
                    try:
                        sub_chan_encoders.append(mini_col_RLE_2B_encoder(j, data[0][i*256+j]))
                    except IndexError:
                        print(f"Sub-channel {i} has less than 256 columns\n")
                        break
                self.encoders.append(sub_chan_encoders)
            print(f"There are in total {self.num_sub_channels} sub-channels.\n")
        else:
            for i in range(self.num_pixels):
                self.encoders.append(mini_col_RLE_2B_encoder(i, data[0][i]))

    def encode(self, data: np.ndarray, file_path: str):
        '''
        Encode the given data using a simple 2 byte run-length encoding scheme.
        The data is assumed to be a 2D numpy array where each column is encoded separately.
        '''
        # make sure the file path is valid
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_size = 0
        # if there is more than one sub-channel, encode the data separately
        if self.num_sub_channels > 1 :
            for sub_chan_index in range(self.num_sub_channels):
                bin_file = open(file_path + f"/sub_chan_{sub_chan_index}.bin", "wb")
                for i in range(256):
                    try:
                        encoded_data = self.encoders[sub_chan_index][i].encode_on_a_whole_column(data[:, sub_chan_index*256+i])
                    except IndexError:
                        print("Last sub-channel has less than 256 pixels\n")
                        break
                    file_size += len(encoded_data)
                    bin_file.write(encoded_data)
                bin_file.close()
        else:
            bin_file = open(file_path + "/the_only_chan.bin", "wb")
            for i in range(self.num_pixels):
                encoded_data = self.encoders[i].encode_on_a_whole_column(data[:, i])
                file_size += len(encoded_data)
                bin_file.write(encoded_data)
            bin_file.close()

        print(f"Binary file size: {file_size} bytes\n")




