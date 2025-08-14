from Enc.Row_based_encoder import Row_encoder_5P
import numpy as np



class fifo :
    def __init__(self, data_depth=256, data_width = 16, id=None):
        self.buffer = []
        self.data_depth = data_depth
        self.data_width = data_width
        self.id = id

    def push(self, data):
        if data> 2**self.data_width -1 or data < 0:
            raise Exception("Data out of range for FIFO width")
        if len(self.buffer) < self.data_depth:
            self.buffer.append(data)
        else:
            raise Exception("FIFO is full")

    def pop(self):
        if len(self.buffer) > 0:
            return self.buffer.pop(0)
        else:
            raise Exception("FIFO is empty")

    def is_empty(self):
        return len(self.buffer) == 0

    def is_full(self):
        return len(self.buffer) == self.data_depth

    def space_available(self):
        return self.data_depth - len(self.buffer)

    def almost_full(self):
        return len(self.buffer) >= self.data_depth - 4

    def space_used(self):
        return len(self.buffer)


class channel:
    '''
    This is a class to encapsulate both the FIFO and the encoder.
    This assumes that the writing speed is 20MHz and the reading speed is 20MHz by default.


    '''
    def __init__(self, encoder="Row_encoder_5P", fifo_depth=256, fifo_width=16, wr_speed_ratio = 1, chan_id=None, one_B_mode=False):
        self.id = chan_id
        self.fifo = fifo(fifo_depth, fifo_width, id=chan_id)
        if encoder == "Row_encoder_5P":
            self.encoder = Row_encoder_5P(id=chan_id)
        else:
            raise Exception("Encoder not supported yet")
        self.wr_speed_ratio = wr_speed_ratio  # This is the ratio of the writing speed to the reading speed
        self.one_b_mode = one_B_mode  # This is the mode to use one byte to encode the data, default is False

        # initialise the buffer available
        self._buffer_available = self.fifo.space_available()
        self._buffer_space_track = []


    def one_single_cycle(self, data:np.ndarray, time_step:int):
        '''
        This function will encode the data and push it into the FIFO buffer.
        In the meantime, if the FIFO is not empty, it will pop the data from the FIFO buffer.
        Args:
            time_step: the current time step in the simulation, used for encoding.
            data: the 5-pixel row data to be encoded which should be a numpy array of shape (5,).

        Returns:

        '''
        if self.fifo.is_full():
            raise Exception(f"Time: @{time_step} *** FIFO {self.id} is full and currently has {len(self.fifo.buffer)}, cannot push data")

        if data.shape != (5,):
            raise Exception("Data shape is not correct, should be (5,)")

        if self.one_b_mode and self.fifo.almost_full():
                encoded_data = self.encoder.encode_live(time_step, np.where(data > 1, 7, 0))
                print(f"Time: @{time_step} *** FIFO {self.id} is almost full, changing into one bit mode...")
        else:
            encoded_data = self.encoder.encode_live(time_step, data)

        if encoded_data is not None:
            if type(encoded_data) is tuple:
                for d in encoded_data:
                    self.fifo.push(d)
            else:
                self.fifo.push(encoded_data)

        if time_step % self.wr_speed_ratio == 0:
            ## Pop the data from the FIFO buffer at the reading speed
            if not self.fifo.is_empty():
                popped_data = self.fifo.pop()
                self._buffer_available = self.fifo.space_available()

        ## Track the buffer space available at each time step
        self._buffer_space_track.append(self._buffer_available)

    def produce_and_push(self, data:np.ndarray, time_step:int):
        """
        This function is used to produce and push the data into the FIFO buffer.
        This method leaves the pop operation to be handled by the arbiter class.
        This is because one arbiter will handle multiple channels and the pop operation.

        Args:
            data: the 5-pixel row data to be encoded which should be a numpy array of shape (5,).
            time_step: the current time step in the simulation, used for encoding.

        Returns:

        """
        if self.fifo.is_full():
            raise Exception(f"Time: @{time_step} *** FIFO {self.id} is full and currently has {len(self.fifo.buffer)}, cannot push data")

        if data.shape != (5,):
            raise Exception("Data shape is not correct, should be (5,)")

        if self.one_b_mode and self.fifo.almost_full():
                encoded_data = self.encoder.encode_live(time_step, np.where(data > 1, 7, 0))
                print(f"Time: @{time_step} *** FIFO {self.id} is almost full, changing into one bit mode...")
        else:
            encoded_data = self.encoder.encode_live(time_step, data)

        if encoded_data is not None:
            if type(encoded_data) is tuple:
                for d in encoded_data:
                    self.fifo.push(d)
            else:
                self.fifo.push(encoded_data)

        ## Track the buffer space available at each time step
        self._buffer_space_track.append(self.fifo.space_available())



class arbiter:
    '''
    This is the arbiter class that will handle the pop operation from multiple channels.
    Ideally, each arbiter should handle 10 channels, that is 10 Row_encoder_5P objects and 10 FIFO buffers.
    This class can later on be encapsulated into a larger class that will handle the whole subgroup simulation.

    This is the base arbiter class that implements a simple round-robin scheduling algorithm.

    '''

    def __init__(self, channels:list):
        self.channels = channels
        self.num_of_channels = len(self.channels)
        self.last_served = -1
        self.channel_select = []

    def step(self, time_step:int):
        """
        This function will pop the data from the FIFO buffer of each channel at the reading speed.
        It will also track the buffer space available in each channel.
        If the FIFO buffer is empty, it will skip the pop operation for that channel and pop the next channel.
        """
        sel_channel = self.select_channel()

        if not sel_channel.fifo.is_empty():
            sel_channel.fifo.pop()
            self.channel_select.append(sel_channel.id)
        else:
            print(f"Time: @{time_step} *** FIFO {sel_channel.id} is empty, skipping pop operation")



    def select_channel(self):
        """
        This function will select the next channel to serve based on the last served channel.
        It will return the next channel to serve.
        """
        self.last_served = (self.last_served + 1) % self.num_of_channels
        return self.channels[self.last_served]

class ArbiterUrgency(arbiter):
    '''
    This is the new urgency based arbiter class that will handle the pop operation from multiple channels.
    It will select the channel based on the urgency of the channel and pop data from the FIFO buffer.
    The urgency is calculated as: data_used * 4 + age
    The age is a counter that increments every time but clamped to 255 when the channel is not selected, which will be reset to 0 when the channel is granted a pop operation.
    Also whenever the channel is empty, the age and urgency will be reset to 0.
    '''

    def __init__(self, channels:list):
        super().__init__(channels)
        self.urgency = np.zeros((self.num_of_channels,), dtype=int)  # Urgency for each channel
        self.age = np.zeros((self.num_of_channels,), dtype=int)

    def select_channel(self):
        '''
        Choose the channel with the highest urgency to pop data from, if there are multiple channels with the same urgency, choose the one with the lowest id.
        Returns:
            The channel with the highest urgency to pop data from.

        '''
        # Calculate the urgency for each channel
        for i, chan in enumerate(self.channels):
            if chan.fifo.is_empty():
                self.urgency[i] = 0
                self.age[i] = 0
            elif self.age[i] < 255:
                # Increment the age if the channel is not selected
                self.age[i] += 1
            # Calculate the urgency based on the FIFO space used and the age
            self.urgency[i] = chan.fifo.space_used() * 4 + self.age[i]

        # Find the channel with the highest urgency
        max_urgency_indices = np.argmax(self.urgency)
        self.last_served = max_urgency_indices
        return self.channels[max_urgency_indices]

    def step(self, time_step:int):
        """
        This function will pop the data from the FIFO buffer of the selected channel at the reading speed.
        It will also track the buffer space available in each channel.
        If the FIFO buffer is empty, it will reset the urgency and age for that channel.
        """
        sel_channel = self.select_channel()

        if not sel_channel.fifo.is_empty():
            sel_channel.fifo.pop()
            self.channel_select.append(sel_channel.id)
            self.age[sel_channel.id] = 0
        else:
            print(f"Time: @{time_step} *** FIFO {sel_channel.id} is empty, resetting urgency and age")
            self.urgency[sel_channel.id] = 0
            self.age[sel_channel.id] = 0
            self.channel_select.append(sel_channel.id)

class DataLine:
    '''
    This is the DataLine class that encapsulates the whole data line simulation.`
    It will include 5 channels, each with a FIFO buffer and an encoder and an arbiter to handle the pop operation.


    '''

    def __init__(self, num_of_channels=5, fifo_depth=256, fifo_width=16, DL_id=0, arbiter_name="round_robin"):
        self.channels = [channel(chan_id=i, fifo_depth=fifo_depth, fifo_width=fifo_width) for i in range(num_of_channels)]
        self.num_of_channels = num_of_channels
        if arbiter_name == "round_robin":
            self.arbiter = arbiter(self.channels)
        elif arbiter_name == "urgency":
            self.arbiter = ArbiterUrgency(self.channels)
        else:
            raise Exception("Arbiter not supported yet")
        
        self.DL_id = DL_id

    def run_sim_live(self, data:np.ndarray, time_step:int):
        """
        This function will run the simulation live for the given number of time steps.
        It will encode the data and push it into the FIFO buffer of each channel.
        It will also pop the data from the FIFO buffer at the reading speed.

        Args:
            data: the 5-pixel row data to be encoded which should be a numpy array of shape (5,).
            time_step: the current time step the whole simulation runs for.
        """
        if data.shape != (self.num_of_channels*5,):
            raise Exception(f"Data shape is not correct, should be ({self.num_of_channels*5}, ), got {data.shape}")

        # loop through the channels and push the data into the FIFO buffer
        for chan in self.channels:
            chan.produce_and_push(data[chan.id*5:(chan.id+1)*5], time_step)

        # run the arbiter to pop the data from the FIFO buffer
        self.arbiter.step(time_step)

    def get_buffer_space_track(self):
        '''
        This function will return the buffer space available in each channel in an ndarray.
        Returns:

        '''
        buffer_space_track = np.array([chan._buffer_space_track for chan in self.channels])
        return buffer_space_track

    def get_used_up_space(self):
        """
        This function will return the used up space in each channel in an ndarray.
        Returns:

        """
        buffer_space_track = self.get_buffer_space_track()
        used_up_space = self.channels[0].fifo.data_depth - buffer_space_track
        return used_up_space






