import struct
import numpy as np






class Row_decoder_5P:
    """
    A class to decode data encoded by the Row_encoder_5P.
    This class provides methods to decode the data and return it in a 2D array format.


    """

    def __init__(self, decoded_data=None, num_of_parts=None):
        self._data = None
        self._decoded_data = decoded_data
        self._pixel_num = 5
        self._num_of_parts = num_of_parts

    def num_2_one_by_5_ndarray(self, byte_value) -> np.ndarray:
        """
        Convert a single 2 byte value to a 2D numpy array of shape (1, 5).

        Args:
            byte_value: A single byte value (int).

        Returns:
            A 2D numpy array of shape (1, 5) with the byte value repeated.
        """
        full_data = np.zeros((1, self._pixel_num), dtype=np.uint8)

        for i in range(5):
            single_int = byte_value & 0b111 # Get the last 3 bits
            full_data[0, i] = single_int
            byte_value >>= 3
        return full_data



    def decode_from_bytes(self, byte_stream) -> np.ndarray:
        """
        Decode the byte stream into a 2D numpy array.

        Args:
            byte_stream:

        Returns:
            A 2D numpy array of shape (time_stamp, 5) with the decoded data.

        """

        ## unpack the byte stream into a list
        byte_values = list(struct.iter_unpack('H', byte_stream))
        byte_values = [value[0] for value in byte_values]

        time_stamp = 0
        decoded_data = []

        ## loop through the byte values and decode them
        for byte_value in byte_values:
            if byte_value > 0x8000:
                # This is a time stamp byte and not a roll over byte
                new_pointer = byte_value & 0x7FFF
                # Update the list and time stamp
                pointer_offset = new_pointer - (time_stamp % 0x8000)
                decoded_data.extend([decoded_data[-1]]* pointer_offset)
                time_stamp = (time_stamp// 0x8000) * 0x8000 + new_pointer

            elif byte_value == 0x8000:
                # This is a roll over byte, we need to add the time stamp
                time_stamp = (time_stamp//0x8000 +1) * 0x8000


            else:
                # This is a data byte, we need to decode it
                byte_array = self.num_2_one_by_5_ndarray(byte_value)
                decoded_data.append(byte_array)
                # update the time stamp
                time_stamp += 1

        ## convert the decoded data to a numpy array
        decode_dat_arr = np.vstack(decoded_data)

        ## if the time stamp does not match the number of rows, raise a warning
        if decode_dat_arr.shape[0] != time_stamp:
            raise ValueError(f"The decoded data has {decode_dat_arr.shape[0]} rows, but the time stamp is {time_stamp}.")

        return  decode_dat_arr



