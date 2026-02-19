## This is the class file that will contain all the different packet builder classes.
## The packet builder is responsible for taking in the output data from the FIFO groups
## and building the packets that will be sent to the packet builder fifo before being sent
## off to the serialiser and LVDS TX.




class packetiser:
    """
    Abstract base class for packet builders. It defines the interface that all packet builders should implement.
    """
    def __init__(self, num_of_channels, total_time_steps):
        self.num_of_channels = num_of_channels
        self.total_time_steps = total_time_steps

    def build_packet(self, fifo_output):
        """
        This method should be implemented by all subclasses to build the packet from the FIFO output.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def packet_ratio(self):
        """
        This method should be implemented by all subclasses to calculate the packet ratio.

        A.K.A. the size after the packet builder divided by the size before the packet builder. It will show how much overhead the packet builder is adding to the data.
        """
        raise NotImplementedError("Subclasses must implement this method")


    def print_header(self):
        """
        Helper function to return the header of the packet.
        Returns:

        """
        return "SOF: 0xFACE\nHeader: 0x0001\n"

    def print_eof(self):
        """
        Helper function to return the end of frame of the packet.
        Returns:
            A string representing the end of frame.
        """
        return "EOF: 0xDEAD\n"


class CARR_packer_fixed_length(packetiser):
    """
    This is a simple packet builder that will take in the FIFO output and build fixed length packets for each channel.

    The packet will contain the data from the FIFO output and the frame will be built as below:

    ## Start of Frame (SOF) - 16-bit fixed value 0xFACE
    ## Header - 16-bit value containing type of data, sequence number, etc. (for simplicity, we will just use a fixed value here)
    ## Channel ID and word length - MSB 8 bits for channel ID and LSB 8 bits for word length.
    ## Payload - The actual data from the FIFO output. The length will be max of 32 words for each channel, if the output has less than 32 words, it will not be padded.
    ## Repeat Channel ID + word length and Payload for each channel.
    ## End of Frame (EOF) - 16-bit fixed value 0xDEAD

    """
    def __init__(self, num_of_channels, total_time_steps, fifo_data_length):
        super().__init__(num_of_channels, total_time_steps)
        self.fifo_data_length = fifo_data_length
        self._encoded_packet_size = 0  # This variable will keep track of the size of the encoded packet for calculating the packet ratio later.

    def build_packet(self, fifo_output):
        # This is where the logic for building the packet from the FIFO output will go. For simplicity, we will just concatenate the channel ID, time step and FIFO output data to form the packet.
        # The actual implementation will depend on the specific requirements of the packet format.
        # This will take in the arbiter output text file and output the packetised data in a text file as well.
        '''The input fifo file will be formated as below:
            Time stemp, Channel ID, FIFO output data (hex), FIFO output data (decimal)
            0, 0, 0x1234, 4660
            1, 1, 0x5678, 22136
        '''

        ## Read the fifo output file and ignore the first line (header), since the file has already been open, we will just read the lines and process them.
        fifo_output_lines = fifo_output.readlines()[1:]  # Skip the header line
        curr_id_x = -1  # This variable will keep track of the current channel ID we are processing. It will be used to determine when to add the channel ID and word length to the packet.
        header_cnt = 0  # This variable keeps track of how many headers we have added to the packet. By the end of packetisation, the header count should be the same as the number of enders.
        ender_cnt = 0

        ## write out the packetised data to a new text file
        with open("CARR_with_word_length_packetised_output.txt", "w") as packetised_file:
            packetised_file.write(self.print_header())  # Write the header of the packet
            self._encoded_packet_size += 2 # 2 words for the SOF and header, in total it will be 4 bytes
            header_cnt += 1
            for line in fifo_output_lines:
                time_step, channel_id, fifo_hex, fifo_dec = line.strip().split(", ")
                ## if the channel ID changes, we will add the channel ID and word length to the packet, but if the new channel ID is smaller
                ## than the current channel ID, it means we need to seal the frame for current frame finish the frame and start a new frame
                if int(channel_id) != curr_id_x:
                    if curr_id_x != -1 and int(channel_id) < curr_id_x:
                        packetised_file.write(self.print_eof())  # Write the end of frame for the current frame
                        packetised_file.write(self.print_header())  # Write the header for the new frame
                        self._encoded_packet_size += 3 # 1 word for the EOF and 2 words for the new SOF and header, in total it will be 6 bytes
                        ender_cnt += 1
                        header_cnt += 1
                    curr_id_x = int(channel_id)
                    word_length = len(fifo_hex) - 2  # Subtract 2 for the "0x" prefix
                    packetised_file.write("Channel ID: {}, Word Length: {}\n".format(channel_id, word_length))
                    # Simply push the fifo content into the packet without any processing.
                    packetised_file.write(fifo_hex+"\n")
                    self._encoded_packet_size += 2 # 1 word for the channel ID and word length, and 1 word for the fifo content, in total it will be 4 bytes
                else:
                    # if the channel ID does not change, we will just add the fifo content to the packet without adding the channel ID and word length again.
                    packetised_file.write(fifo_hex+"\n")
                    self._encoded_packet_size += 1 # 1 word for the fifo content, in total it will be 2 bytes
            packetised_file.write(self.print_eof())  # Write the end of frame for the last frame
            self._encoded_packet_size += 1 # 1 word for the EOF, in total
            ender_cnt += 1

            ## Sanity check to make sure the number of headers and enders are the same, since each frame should have one header and one ender.
            if header_cnt != ender_cnt:
                print("Warning: The number of headers and enders are not the same. Header count: {}, Ender count: {}".format(header_cnt, ender_cnt))






    def packet_ratio(self):
        # This is where the logic for calculating the packet ratio will go. It will depend on how much additional information is added to the packet compared to the original FIFO output data.
        print("============ CARR PACKER FIXED LENGTH PACKET RATIO ============\n")
        print("Encoded packet size (in words): ", self._encoded_packet_size)
        print("Original FIFO output size (in words): ", self.fifo_data_length)
        ratio = self._encoded_packet_size / self.fifo_data_length

        print("Packet ratio: {}".format(ratio)+"\n")


class CARR_PACKER_VARIABLE_LENGTH(packetiser):
    """
    This is an alternative packet builder that will take in the FIFO output and build variable length packets for each channel.

    The packet will not contain the word length in the header, but will use byte stuffing to escape the special characters in the payload. The frame will be built as below:

    ## Start of Frame (SOF) - 16-bit fixed value 0xFACE
    ## Header - 16-bit value containing type of data, sequence number, etc. (for simplicity, we will just use a fixed value here)
    ## Channel start - 16-bit fixed value 0xC0DE
    ## Channel ID - 16-bit value representing the channel ID.
    ## Payload - The actual data from the FIFO output. The length will be determined by the word length field in the header.
    ## Repeat Channel start, Channel ID and Payload for each channel.
    ## End of Frame (EOF) - 16-bit fixed value 0xDEAD

    ######## Word Stuffing ########
    ## Reserved the following special characters for framing and escaping:
    ## 0xC0DE - Channel start
    ## 0xDEAD - End of frame
    ## 0xBEEF - Escape character

    if special words appear in the payload, we will use byte stuffing to escape them.
    The escape character will be 0xBEEF, and it will be followed by the original word XORed with 0xFFFF to indicate that it is an escaped word.

    """

    def __init__(self, num_of_channels, total_time_steps, fifo_data_length):
        super().__init__(num_of_channels, total_time_steps)
        self.fifo_data_length = fifo_data_length
        self._encoded_packet_size = 0  # This variable will keep track of the size




    def build_packet(self, fifo_output):
        """
        This method will be similarly structured to the build_packet method in the CARR_packer_fixed_length class, but with additional logic for handling the variable length packets and byte stuffing.
        Args:
            fifo_output: this will be the opened file object for the arbiter output text file, which contains the FIFO output data that we want to packetise.
            The method will read the lines from this file, process them according to the variable length packet format, and write the packetised data to a new text file.

        Returns:
            None, but it will write the packetised data to a new text file and update the _encoded_packet_size variable to keep track of the size of the encoded packet for calculating the packet ratio later.
        """

        ## Read the fifo output file and ignore the first line (header), since the file has already been open, we will just read the lines and process them.
        fifo_output_lines = fifo_output.readlines()[1:]  # Skip the header line
        curr_id_x = -1  # This variable will keep track of the current channel ID we are processing. It will be used to determine when to add the channel ID and word length to the packet.
        header_cnt = 0  # This variable keeps track of how many headers we have added to the packet. By the end of packetisation, the header count should be the same as the number of enders.
        ender_cnt = 0

        ## write out the packetised data to a new text file
        with open("CARR_variable_length_packetised_output.txt", "w") as packetised_file:
            packetised_file.write(self.print_header())  # Write the header of the packet
            self._encoded_packet_size += 2 # 2 words for the SOF and header, in total it will be 4 bytes
            header_cnt += 1
            for line in fifo_output_lines:
                time_step, channel_id, fifo_hex, fifo_dec = line.strip().split(", ")
                ## if the channel ID changes, we will add the channel start and channel ID to the packet, but if the new channel ID is smaller
                ## than the current channel ID, it means we need to seal the frame for current frame finish the frame and start a new frame
                if int(channel_id) != curr_id_x:
                    if curr_id_x != -1 and int(channel_id) < curr_id_x:
                        packetised_file.write(self.print_eof())  # Write the end of frame for the current frame
                        packetised_file.write(self.print_header())  # Write the header for the new frame
                        self._encoded_packet_size += 3 # 1 word for the EOF and 2 words for the new SOF and header, in total it will be 6 bytes
                        ender_cnt += 1
                        header_cnt += 1
                    curr_id_x = int(channel_id)
                    packetised_file.write("CHS: 0xC0DE\n")
                    packetised_file.write("CID: {}\n".format(channel_id))
                    self._encoded_packet_size += 2 # 1 word for the channel start and 1 word for the channel ID, in total it will be 4 bytes

                    # Check the fifo content before writing, if it contains special characters, it will need to be escaped.
                    written_word = self.word_processing(fifo_hex)
                    packetised_file.write(written_word)
                    if written_word != fifo_hex + "\n":
                        print(f"Word stuffing applied for word: {fifo_hex} at {time_step} for channel {channel_id}")
                        self._encoded_packet_size += 2 # word stuffing should add 2 words in total
                    else:
                        self._encoded_packet_size += 1 # 1 word for the fifo content, in total it will be 2 bytes
                else:
                    # if the channel ID does not change, we will just add the fifo content to the packet without adding the channel start and channel ID again.
                    written_word = self.word_processing(fifo_hex)
                    packetised_file.write(written_word)
                    if written_word != fifo_hex + "\n":
                        print(f"Word stuffing applied for word: {fifo_hex} at {time_step} for channel {channel_id}")
                        self._encoded_packet_size += 2 # word stuffing should add 2 words in total
                    else:
                        self._encoded_packet_size += 1 # 1 word for the fifo content, in total it will be 2 bytes
            packetised_file.write(self.print_eof())  # Write the end of frame for the last frame
            ender_cnt += 1
            self._encoded_packet_size += 1 # 1 word for the EOF, in total it will be 2 bytes

            ## Sanity check to make sure the number of headers and enders are the same, since each frame should have one header and one ender.
            if header_cnt != ender_cnt:
                print("Warning: The number of headers and enders are not the same. Header count: {}, Ender count: {}".format(header_cnt, ender_cnt))

    def packet_ratio(self):
        # This is where the logic for calculating the packet ratio will go. It will depend on how much additional information is added to the packet compared to the original FIFO output data.
        print("============ CARR PACKER VARIABLE LENGTH PACKET RATIO ============\n")
        print("Encoded packet size (in words): ", self._encoded_packet_size)
        print("Original FIFO output size (in words): ", self.fifo_data_length)
        ratio = self._encoded_packet_size / self.fifo_data_length

        print("Packet ratio: {}".format(ratio) +"\n")


    def word_processing(self, word):
        """
        This method will take in a word and check if it is one of the special characters that need to be escaped. If it is, it will return the escape character followed by the original word XORed with 0xFFFF. If it is not, it will return the original word.

        Args:
            word: a string representing the word to be checked for byte stuffing. It will be in hexadecimal format (e.g., "0x1234").

        Returns:
            A string representing the byte stuffed word if it is a special character, or the original word if it is not.
        """
        special_characters = ["0xC0DE", "0xDEAD", "0xBEEF"]
        if word in special_characters:
            escaped_word = "0xBEEF\n" + hex(int(word, 16) ^ 0xFFFF).upper() + "\n" # XOR the original word with 0xFFFF and concatenate with the escape character
            return escaped_word
        else:
            return word +"\n"
