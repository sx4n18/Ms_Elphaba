## This is the newly defined compression encoder, which is a run-length encoder where
## each row will be encoded into 2 bytes. All the variations of 2-byte run-length
## encoders will be defined in this file.
## The encoders defined in this file are:
## 1. RLE_2B: simple 2 byte run-length encoder
## 2. RLE_RD_2B: by comparison, this encoder will encode the row difference data
## 3. RLE_AZ_W_RM_2B: this encoder will consider special cases of all zero rows and throw row marker data
## Comments:
## 1. All the encoders expect an input of a 2D numpy array where each row is encoded separately.
## 2. Each row of the input data is expected to be 256 elements long.
## 3. Value of each element should have a range of 0-7.
import warnings

import numpy as np
import struct
import io
from typing import List, Tuple
import os


class RLE_2B:
    """
    Simple 2 byte run-length encoder.

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
                elif all_zero_row_run_length > 0:
                    # Write the all zero row run length data to the byte stream
                    byte_stream.write(struct.pack("B", 0b0100_0000 | (all_zero_row_run_length >> 8)))
                    byte_stream.write(struct.pack("B", all_zero_row_run_length & 0xFF))
                    # Reset the all zero row run length
                    all_zero_row_run_length = 0
                # If the row is not all zeros, encode the row data
                else:
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
    def encode_2_file_straight(data:np.ndarray, file_name: str):
        # This method is not going to be implemented
        warnings.warn("This method is not going to be implemented"
                      "Plese use the encode_2_file(data, file_name) method instead."
                      "data: the 2d numpy array to be encoded"
                      "file_name: the file name to be saved")
        pass



