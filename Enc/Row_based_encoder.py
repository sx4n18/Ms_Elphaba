import struct
import os
import numpy as np
import io

## This is a class script for the row based encoders, which operate in a simple fashion.
## This encoder will be very simple, it will only dump the raw data into a packet when there is no match in the buffer.
## When there is a match, the encoder will not export anything.
## But also it will export the timestamp, this will be exported in 2 cases:
## 1. When there is a mismatch in the buffer
## 2. When the alarm rings, this will happen when the global timer loops around


class Row_encoder_5P:
    '''
    This is a simple implementation of the row based encoder.
    The encoder will encode the data in a very simple way, it will only dump the row data when the input
    data does not match what is in the buffer.
    If the input data matches what is in the buffer, the encoder will not export anything until the pattern
    is broken.
    When the pattern is broken, the encoder will first export the timestamp, then it will export the row data.
    The encoder will also export the timestamp when the alarm rings, this will happen when the global timer
    loops around.

    The output data format is a 16-bit number in bytes. There are 3 types of data:
    1. The timestamp data, this is a 16-bit number in bytes that starts with a leading 1
        1_Time_stamp ---> 1 is the leading bit, rest 15 bits are the timestamp data
    2. The raw data, this is a 16-bit number in bytes that starts with a leading 0
        0_data_data_data_data_data ---> each data is 3 bit, 5 data and a leading 0 will make it 16 bits
    3. The alarm data, this is a special packet that will be sent when the global timer loops around, this will
    be sent every 2^15 ticks.
        1000_0000_0000_0000 ---> this is a special packet that will be sent when the global timer loops around
    '''

    def __init__(self):
        self._repeating_pattern = 0
        self._tok_record = 0


    def encode_in_mem(self, data: np.ndarray) -> bytes:
        '''
        This function will encode the data assuming that the data is sent along with the increment of the timestamp.
        i.e. the time stamp is incremented by 1 for each data sent.

        Args:
            data: This should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.

        Returns:
            encoded_data: This will be a bytes object that contains the encoded data.
        '''

        # Check if the data is in the correct format
        if data.shape[1] != 5:
            raise ValueError("The data should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.")

        #Start encoding the data
        encoded_data = bytearray()
        loops = data.shape[0]
        with io.BytesIO() as byte_stream:
            for loop in range(loops):
                if loop == 0:
                    # This is the first loop, the data will be exported as it is and saved as the repeating pattern
                    self._repeating_pattern = data[loop]
                    data_to_write = self.one_by_5_nd_array_to_number(data[loop])
                    byte_stream.write(struct.pack('H', data_to_write))
                elif (loop+1)% 2^15 == 0:
                    # This is the alarm data, this will be sent when the global timer loops around
                    byte_stream.write(struct.pack('H', 0x8000))
                else:
                    # This is the normal data, the data will be exported as it is
                    # Check if the data matches the repeating pattern
                    if np.array_equal(data[loop], self._repeating_pattern):
                        # The data matches the repeating pattern, do not export anything
                        pass
                    else:
                        if self._tok_record != loop - 1:
                            # The data does not match saved pattern and it has been more than 1 loop since the last update
                            self._tok_record = loop
                            # Export the timestamp
                            byte_stream.write(struct.pack('H', (self._tok_record) | 0x8000))

                        # The data does not match the repeating pattern, dump the raw data
                        self._tok_record = loop

                        # Export the data
                        data_to_write = self.one_by_5_nd_array_to_number(data[loop])
                        byte_stream.write(struct.pack('H', data_to_write))
                        # update the repeating pattern
                        self._repeating_pattern = data[loop]

            # Get the encoded data from the byte stream
            encoded_data = byte_stream.getvalue()
        return encoded_data



    def one_by_5_nd_array_to_number(self, data: np.ndarray) -> int:
        '''
        This function will convert a 1x5 numpy array to a 16-bit number.
        The first bit is the leading bit, the rest 15 bits are the data.
        The data is in the format of 3 bits per data, so there are 5 data in total.
        The leading bit is 0 for the data and 1 for the timestamp.

        Args:
            data: This should be a 1D numpy array of shape (5,)

        Returns:
            number: This will be a 16-bit number.
        '''
        if data.shape[0] != 5:
            raise ValueError("The data should be a 1D numpy array of shape (5,)")

        # Convert the data to a number
        number = 0
        for i in range(5):
            number |= (data[i] << (3 * i))

        return number

    def track_encoding_rate(self, data: np.ndarray, np_or_lst: bool = False):
        '''
        This is a new function that will track the encoding output data rate.
        Args:
            data:
                This should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.
            np_or_lst:
                This is a boolean value that will determine if the output is in numpy array or list format.
                The default value is False, which means the output will be in list format.

        Returns:
            a list of the accumulating data size.
        '''

        # Check if the data is in the correct format
        if data.shape[1] != 5:
            raise ValueError("The data should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.")

        if np_or_lst:
            # If the output is in numpy array format
            data_size = np.zeros(data.shape[0])
        else:
            # If the output is in list format
            data_size = []

        # Start encoding the data
        loops = data.shape[0]
        with io.BytesIO() as byte_stream:
            for loop in range(loops):
                if loop == 0:
                    # This is the first loop, the data will be exported as it is and saved as the repeating pattern
                    self._repeating_pattern = data[loop]
                    data_to_write = self.one_by_5_nd_array_to_number(data[loop])
                    byte_stream.write(struct.pack('H', data_to_write))
                elif (loop+1)% 2^15 == 0:
                    # This is the alarm data, this will be sent when the global timer loops around
                    byte_stream.write(struct.pack('H', 0x8000))
                else:
                    # This is the normal data, the data will be exported as it is
                    # Check if the data matches the repeating pattern
                    if np.array_equal(data[loop], self._repeating_pattern):
                        # The data matches the repeating pattern, do not export anything
                        pass
                    else:
                        if self._tok_record != loop - 1:
                            # The data does not match saved pattern and it has been more than 1 loop since the last update
                            self._tok_record = loop
                            # Export the timestamp
                            byte_stream.write(struct.pack('H', (self._tok_record) | 0x8000))

                        # The data does not match the repeating pattern, dump the raw data
                        self._tok_record = loop

                        # Export the data
                        data_to_write = self.one_by_5_nd_array_to_number(data[loop])
                        byte_stream.write(struct.pack('H', data_to_write))
                        # update the repeating pattern
                        self._repeating_pattern = data[loop]

                # Get the encoded data from the byte stream
                encoded_data = byte_stream.getvalue()
                # Calculate the size of the encoded data
                encoded_size = len(encoded_data)
                # Append the size to the data_size list
                if np_or_lst:
                    data_size[loop] = encoded_size
                else:
                    data_size.append(encoded_size)
        return data_size




    def encode(self, data:np.ndarray, file_name="encoded_data.bin"):
        '''
        This function will encode the data and write it to a byte file.
        Args:
            data:
                This should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.

            file_name:
                This is the name of the file where the encoded data will be written to.
                The default value is "encoded_data.bin".

        Returns:
            None

        '''

        # Check if the data is in the correct format
        if data.shape[1] != 5:
            raise ValueError("The data should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.")
        # Start encoding the data
        encoded_data = self.encode_in_mem(data)
        # Write the encoded data to a file

        with open(file_name, 'wb') as f:
            f.write(encoded_data)
        print(f"Encoded data written to {file_name}")


    def compression_ratio(self, data):
        '''
        This function will calculate the compression ratio of the encoded data.
        The compression ratio is defined as the size of the original data divided by the size of the encoded data.
        Args:
            data: This should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.

        Returns:
            compression_ratio: This will be a float value that represents the compression ratio.
        '''
        # Check if the data is in the correct format
        if data.shape[1] != 5:
            raise ValueError("The data should be a 2D numpy array of shape (M, 5), where M is the number of rows and 5 is the number of columns.")

        # The original size needs to be calculated as the multiplication of number of the elements by 3 bit
        original_size = data.size * 3 / 8

        # Calculate the size of the encoded data
        encoded_data = self.encode_in_mem(data)
        encoded_size = len(encoded_data)

        # Calculate the compression ratio
        compression_ratio = (1 - (encoded_size / original_size)) * 100

        return compression_ratio

    def reset(self):
        '''
        This function will reset the encoder to its initial state.
        This will reset the repeating pattern and the tok record to 0.
        Returns:
            None
        '''
        self._repeating_pattern = 0
        self._tok_record = 0

class Row_encoder_10P:
    '''
    Just like the Row_encoder_5P, but this will encode the data slightly differently.

    Since this encoder will take 10 pixels, the output of this encoder will be 32 bits instead of 16.

    Similarly, there are 3 types of data:
    1. Raw data, this is a 32-bit number in bytes that starts with a leading 00
        00_data_data_data_data_data_data_data_data_data_data ---> each data is 3 bit, 10 data and a leading 00 will make it 32 bits
    2. The timestamp data, this is a 32-bit number in bytes that starts with a leading 01
        01_Time_stamp ---> 1 is the leading bit, rest 30 bits are the timestamp data
    3. The alarm data, this is a special packet that will be sent when the global timer loops around, this will
    be sent every 2^30 ticks.
        1000_0000_0000_0000_0000_0000_0000_0000 ---> this is a special packet that will be sent when the global timer loops around
    '''

    def __init__(self):
        self._repeating_pattern = 0
        self._tok_record = 0

    def encode_in_mem(self, data: np.ndarray) -> bytes:
        '''
        This function will encode the data assuming that the data is sent along with the increment of the timestamp.
        i.e. the time stamp is incremented by 1 for each data sent.

        Args:
            data: This should be a 2D numpy array of shape (M, 10), where M is the number of rows and 10 is the number of columns.

        Returns:
            encoded_data: This will be a bytes object that contains the encoded data.
        '''

        # Check if the data is in the correct format
        if data.shape[1] != 10:
            raise ValueError("The data should be a 2D numpy array of shape (M, 10), where M is the number of rows and 10 is the number of columns.")

        #Start encoding the data
        encoded_data = bytearray()
        loops = data.shape[0]
        with io.BytesIO() as byte_stream:
            for loop in range(loops):
                if loop == 0:
                    # This is the first loop, the data will be exported as it is and saved as the repeating pattern
                    self._repeating_pattern = data[loop]
                    data_to_write = self.one_by_10_nd_array_to_number(data[loop])
                    byte_stream.write(struct.pack('I', data_to_write))
                elif (loop+1)% 2^30 == 0:
                    # This is the alarm data, this will be sent when the global timer loops around
                    byte_stream.write(struct.pack('I', 0x80000000))
                else:
                    # This is the normal data, the data will be exported as it is
                    # Check if the data matches the repeating pattern
                    if np.array_equal(data[loop], self._repeating_pattern):
                        # The data matches the repeating pattern, do not export anything
                        pass
                    else:
                        if self._tok_record != loop - 1:
                            # The data does not match saved pattern and it has been more than 1 loop since the last update
                            self._tok_record = loop
                            # Export the timestamp
                            byte_stream.write(struct.pack('I', (self._tok_record) | 0x80000000))
                        # The data does not match the repeating pattern, export the timestamp and the data
                        self._tok_record = loop
                        # Export the data
                        data_to_write = self.one_by_10_nd_array_to_number(data[loop])
                        byte_stream.write(struct.pack('I', data_to_write))
                        self._repeating_pattern = data[loop]

            # Get the encoded data from the byte stream
            encoded_data = byte_stream.getvalue()
        return encoded_data
    def one_by_10_nd_array_to_number(self, data: np.ndarray) -> int:
        '''
        This function will convert a 1x10 numpy array to a 32-bit number.
        The first 2 bits are the leading bits, the rest 30 bits are the data.
        Args:
            data:

        Returns:

        '''
        # Check if the data is in the correct format
        if data.shape[0] != 10:
            raise ValueError("The data should be a 1D numpy array of shape (10,)")
        # Convert the data to a number
        number = 0
        for i in range(10):
            number |= (data[i] << (3 * i))
        return number

    def encode(self, data:np.ndarray, file_name="encoded_data.bin"):
        '''
        This function will encode the data and write it to a byte file.
        Args:
            data:
                This should be a 2D numpy array of shape (M, 10), where M is the number of rows and 10 is the number of columns.

            file_name:
                This is the name of the file where the encoded data will be written to.
                The default value is "encoded_data.bin".

        Returns:
            None

        '''

        # Check if the data is in the correct format
        if data.shape[1] != 10:
            raise ValueError("The data should be a 2D numpy array of shape (M, 10), where M is the number of rows and 10 is the number of columns.")
        # Start encoding the data
        encoded_data = self.encode_in_mem(data)
        # Write the encoded data to a file

        with open(file_name, 'wb') as f:
            f.write(encoded_data)
        print(f"Encoded data written to {file_name}")

    def compression_ratio(self, data):
        '''
        This function will calculate the compression ratio of the encoded data.
        The compression ratio is defined as the size of the original data divided by the size of the encoded data.
        Args:
            data:

        Returns:

        '''
        # Check if the data is in the correct format
        if data.shape[1] != 10:
            raise ValueError("The data should be a 2D numpy array of shape (M, 10), where M is the number of rows and 10 is the number of columns.")
        # The original size needs to be calculated as the multiplication of number of the elements by 3 bit
        original_size = data.size * 3 / 8
        # Calculate the size of the encoded data
        encoded_data = self.encode_in_mem(data)
        encoded_size = len(encoded_data)
        # Calculate the compression ratio
        compression_ratio = (1 - (encoded_size / original_size)) * 100
        return compression_ratio

    def reset(self):
        '''
        This function will reset the encoder to its initial state.
        This will reset the repeating pattern and the tok record to 0.
        Returns:
            None
        '''
        self._repeating_pattern = 0
        self._tok_record = 0


class Row_encoder_4P:
    '''
    This is a class for the 4-pixel row based encoder. It will encode the data in a similar way to the 5-pixel encoder,
    but it will take 4 pixels instead of 5.
    input:
        4 pixels -- 12-bits data
        tiktok -- it assumes that the row number will be the input tiktok
    output can be categorised into mainly 2 types:
    1. The raw data, this is a 16-bit number in bytes that starts with a leading 0
        when opcode is 000, it will be in the format:
        0_{Opcode}_data_data_data_data ---> each data is 3 bit, 4 data and a leading 0 and an opcode will make it 16 bits
        when opcode is 001, the raw data will be in the 1-bit mode, this will be in the format:
        0_001_{12'bxxxx} ---> each data is 1 bit, 4 data and a leading 0 and an opcode will make it 16 bits

    2. The timestamp data, this is a 16-bit number in bytes that starts with a leading 1
        1_Time_stamp ---> 1 is the leading bit, rest 15 bits are the timestamp data

    So far the opcode used are:
    000: raw data
    001: 1-bit mode start
    010: 1-bit mode end
    '''

    def __init__(self):
        self._repeating_pattern = 0
        self._tok_record = 0

    def reset(self):
        '''
        This function will reset the encoder to its initial state.
        This will reset the repeating pattern and the tok record to 0.
        Returns:
            None
        '''
        self._repeating_pattern = 0
        self._tok_record = 0

    def one_by_4_nd_array_to_number(self, data: np.ndarray, opcode=0) -> int:
        '''
        This function will convert a 1x4 numpy array to a 16-bit number.
        The first bit is the leading bit, the rest 15 bits are the data.
        The data is in the format of 3 bits per data, so there are 4 data in total.
        The leading bit is 0 for the data and 1 for the timestamp.

        Args:
            data: This should be a 1D numpy array of shape (4,)

        Returns:
            number: This will be a 16-bit number.
        '''
        if data.shape[0] != 4:
            raise ValueError("The data should be a 1D numpy array of shape (4,)")

        # Convert the data to a number
        if opcode == 0:
            # Normal 3-bit mode
            number = 0
            for i in range(4):
                number |= (data[i] << (3 * i))
            return number
        elif opcode == 1:
            # 1-bit mode, quantise the data to 1 bit
            # [0,1] ==> 0 , [2, 3, 4, 5, 6, 7] ==> 1
            data = np.where(data>1, 1, 0)
            number = 0
            for i in range(4):
                number |= (data[i] << i)
            return number

    def split_data(self, data: np.ndarray, pixel_num: int = 4, interleave: bool = False) -> list:
        '''
        This function will split the data into parts of pixel_num width for the encoder.
        Args:
            data: 2d numpy array of shape (M, N), where M is the number of rows and N is the number of columns.
            pixel_num:
            interleave: interleave the data or not, if True, the odd and even columns will be grouped together.
                        The default value is False, which means the data will not be interleaved.

        Returns:
            split_data: a list of numpy arrays, each of shape (M, pixel_num), where M is the number of rows and pixel_num is the number of columns.

        '''

        # Check if the data is in the correct format
        if data.ndim != 2:
            raise ValueError("The data should be a 2D numpy array.")

        if data.shape[1] % pixel_num != 0:
            data = data[:, :data.shape[1] - (data.shape[1] % pixel_num)]
            raise Warning(f"The width of the data is not divisible by {pixel_num}. The last part will be discarded.")

        # check if interleave is True, if so, split the data into even and odd columns
        if interleave:
            # Split the data into even and odd columns
            even_arr = data[:, 0::2]
            odd_arr = data[:, 1::2]
            # Concatenate the even and odd arrays
            data = np.concatenate((even_arr, odd_arr), axis=1)

        # Split the data into parts of pixel_num width
        parts = data.shape[1] // pixel_num
        split_data = np.array_split(data, parts, axis=1)

        return split_data



    def encode_in_mem(self, data: np.ndarray, opcode=0) -> bytes:
        '''
        This function will encode the data assuming that the data is sent along with the increment of the timestamp.
        i.e. the time stamp is incremented by 1 for each data sent.

        Args:
            data: This should be a 2D numpy array with the shape (M, 4), where M is the number of rows and 4 is the number of columns.
            opcode: This is the opcode that will be used to encode the data. The default value is 0.

        Returns:
            encoded_data: This will be a bytes object that contains the encoded data.
        '''

        # Check if the data is in the correct format
        if data.shape[1] != 4:
            raise ValueError("The data should be a 2D numpy array of shape (M, 4), where M is the number of rows and 4 is the number of columns.")


        if opcode == 0:
            # Start encoding the data
            loops = data.shape[0]
            with io.BytesIO() as byte_stream:
                for loop in range(loops):
                    if loop == 0:
                        # This is the first loop, the data will be exported as it is and saved as the repeating pattern
                        self._repeating_pattern = data[loop]
                        data_to_write = self.one_by_4_nd_array_to_number(data[loop])
                        byte_stream.write(struct.pack('H', data_to_write))
                    elif (loop + 1) % 2 ^ 15 == 0:
                        # This is the alarm data, this will be sent when the global timer loops around
                        byte_stream.write(struct.pack('H', 0x8000))
                    else:
                        # This is the normal data, the data will be exported as it is
                        # Check if the data matches the repeating pattern
                        if np.array_equal(data[loop], self._repeating_pattern):
                            # The data matches the repeating pattern, do not export anything
                            pass
                        else:
                            if self._tok_record != loop - 1:
                                # The data does not match saved pattern and it has been more than 1 loop since the last update
                                self._tok_record = loop
                                # Export the timestamp
                                byte_stream.write(struct.pack('H', (self._tok_record) | 0x8000))

                            # The data does not match the repeating pattern, dump the raw data
                            self._tok_record = loop

                            # Export the data
                            data_to_write = self.one_by_4_nd_array_to_number(data[loop])
                            byte_stream.write(struct.pack('H', data_to_write))
                            # update the repeating pattern
                            self._repeating_pattern = data[loop]

                # Get the encoded data from the byte stream
                encoded_data = byte_stream.getvalue()
            return encoded_data

        # operating at 1-bit mode, in this mode, the data will not be compared to the repeating pattern
        elif opcode == 1:
            # Start encoding the data
            loops = data.shape[0]
            with io.BytesIO() as byte_stream:
                data_to_write = 0x0000
                for loop in range(loops):
                    data_polar = self.one_by_4_nd_array_to_number(data[loop], opcode)
                    data_to_write = (data_to_write << 4) | data_polar
                    if loop %3 == 0:
                        # flush out the data_to_write every 3 loops
                        data_to_write = (data_to_write & 0x0FFF) | 0x1000  # Keep only the last 12 bits and then pack it with 0001
                        byte_stream.write(struct.pack('H', data_to_write))
                        data_to_write = 0x0000
                    elif loop ==  loops-1:
                        # if this is the last loop, flush out the data_to_write
                        data_to_write = (data_to_write & 0x0FFF) | 0x1000
                        byte_stream.write(struct.pack('H', data_to_write))

                # Get the encoded data from the byte stream
                encoded_data = byte_stream.getvalue()
            return encoded_data

    def encode(self, data: np.ndarray, file_name="encoded_data.bin", opcode=0, interleave=False):
        '''
        This function will encode the data and write it to a byte file.
        Args:
            data:
                This should be a 2D numpy array of shape (M, 4), where M is the number of rows and 4 is the number of columns.

            file_name:
                This is the name of the file where the encoded data will be written to.
                The default value is "encoded_data.bin".

            opcode: This is the opcode that will be used to encode the data. The default value is 0.

            interleave: This is a boolean value that will determine if the data is interleaved or not.
        Returns:
            None
        '''

        # Check if the data is in the correct format
        data_list = self.split_data(data, pixel_num=4, interleave=interleave)

        if len(data_list) == 0:
            raise ValueError("The data should be a 2D numpy array with at least 4 columns.")


        with open(file_name, 'ab') as f:
            for data_part in data_list:
                encoded_data = self.encode_in_mem(data_part, opcode=opcode)
                f.write(encoded_data)
                self.reset()

        print("Encoding completed...")
