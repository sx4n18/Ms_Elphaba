import warnings

from Enc.Row_based_encoder import Row_encoder_5P
import numpy as np
import math


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

class RoundRobinSkipEmpty(arbiter):
    '''
    This is a round-robin arbiter that skips empty FIFOs when selecting channels to pop from.
    '''

    def select_channel(self):
        '''
        Choose the next non-empty channel in a round-robin fashion.
        Returns:
            The selected channel to pop data from.

        '''
        for _ in range(self.num_of_channels):
            self.last_served = (self.last_served + 1) % self.num_of_channels
            sel_channel = self.channels[self.last_served]
            if not sel_channel.fifo.is_empty():
                return sel_channel

        # If all channels are empty, return None
        return None

    def step(self, time_step:int):
        """
        This function will pop the data from the FIFO buffer of the selected channel at the reading speed.
        It will also track the buffer space available in each channel.
        If all FIFO buffers are empty, it will skip the pop operation.
        """
        sel_channel = self.select_channel()

        if sel_channel is not None:
            sel_channel.fifo.pop()
            self.channel_select.append(sel_channel.id)
        else:
            print(f"Time: @{time_step} *** All FIFOs are empty, skipping pop operation")


class CARRArbiter(arbiter):
    """
    Congestion-Aware Round-Robin (CARR) arbiter for your channel/fifo classes.

    Policy:
      1) Stick to current FIFO if it is non-empty
      2) Pre-empt to any other FIFO that is almost_full()
      3) If current served MAX_READS times consecutively, advance RR
      4) If all FIFOs empty, do nothing and keep current selection
    """

    def __init__(self, channels: list, max_reads: int = 16):
        super().__init__(channels)
        self.max_reads = int(max_reads)

        # Current selection index (sticky pointer) and consecutive read counter
        self.curr_idx = 0 if self.num_of_channels > 0 else -1
        self.burst_count = 0

        # temporarily track the popped word from FIFO, if there are no popped words, it shall be None.
        self.last_popped_word = None

    # ---------- helper predicates ----------
    def _empty(self, idx: int) -> bool:
        return self.channels[idx].fifo.is_empty()

    def _almost_full(self, idx: int) -> bool:
        # In your fifo class, almost_full is a METHOD.
        return self.channels[idx].fifo.almost_full()

    def _all_empty(self) -> bool:
        return all(ch.fifo.is_empty() for ch in self.channels)

    def _advance_to_next_non_empty(self):
        """Advance curr_idx in RR order until a non-empty FIFO is found (or give up if all empty)."""
        if self._all_empty():
            return  # keep curr_idx unchanged

        for _ in range(self.num_of_channels):
            self.curr_idx = (self.curr_idx + 1) % self.num_of_channels
            if not self._empty(self.curr_idx):
                return

    def _find_almost_full_other(self):
        """
        Find an almost-full FIFO other than current selection.
        Deterministic choice: scan in RR order starting from curr_idx+1.
        Returns index or None.
        """
        n = self.num_of_channels
        for k in range(1, n + 1):
            j = (self.curr_idx + k) % n
            if j != self.curr_idx and self._almost_full(j) and (not self._empty(j)):
                return j
        return None

    # ---------- core selection ----------
    def select_channel(self):
        """
        Returns the selected channel object according to CARR policy.
        Note: This updates internal state (curr_idx, burst_count resets) as needed.
        """
        if self.num_of_channels == 0:
            raise Exception("No channels connected to arbiter")

        # 0) If all FIFOs empty: hold selection, don't change pointer
        if self._all_empty():
            return self.channels[self.curr_idx]

        # 1) Pre-emption: any other FIFO almost full?
        af_idx = self._find_almost_full_other()
        if af_idx is not None:
            self.curr_idx = af_idx
            self.burst_count = 0
            return self.channels[self.curr_idx]

        # 2) If current FIFO empty: move to next non-empty
        if self._empty(self.curr_idx):
            self._advance_to_next_non_empty()
            self.burst_count = 0
            return self.channels[self.curr_idx]

        # 3) Burst limit reached: move on (fairness)
        if self.burst_count >= self.max_reads:
            self._advance_to_next_non_empty()
            self.burst_count = 0
            return self.channels[self.curr_idx]

        # 4) Otherwise stick to current
        return self.channels[self.curr_idx]

    def step(self, time_step: int):
        """
        One arbiter read opportunity.
        Pops from the selected FIFO if possible; otherwise idles.
        Records selected channel id in channel_select on successful pop.
        """
        if self.num_of_channels == 0:
            return

        # If all empty: do nothing and keep current selection
        if self._all_empty():
            # Optional: could log idle here
            self.last_popped_word = None
            return

        sel_channel = self.select_channel()

        if not sel_channel.fifo.is_empty():
            self.last_popped_word = sel_channel.fifo.pop()
            self.channel_select.append(sel_channel.id)
            self.burst_count += 1
        else:
            # Can happen if FIFO becomes empty after selection due to other pops in sim
            print(f"Time: @{time_step} *** FIFO {sel_channel.id} is empty, skipping pop operation")
            self.last_popped_word = None
            self.burst_count = 0



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
        elif arbiter_name == "round_robin_skip":
            self.arbiter = RoundRobinSkipEmpty(self.channels)
        elif arbiter_name == "CARR":
            self.arbiter = CARRArbiter(self.channels, max_reads=16)
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


class AsyncDataline:
    '''
    This is the true asynchronous data line class that would support the different writing and reading clock domains.
    By default, it will assume the writing clock is 20 MHz and the reading clock is 37.5 MHz.

    This is achieved by having a common tick counter that enables the writing and reading operations based on the respective clock frequencies.
    e.g.
    writing clock = 20 MHz, reading clock = 37.5 MHz, the least common multiple for their periods is 0.4 us.
    i.e. for every 8 cycles of writing operations, there will be 15 cycles of reading operations.
    So we could count the common tick counter and enable the writing operation every 15 ticks and the reading operation every 8 ticks.


    '''

    def __init__(self, num_of_channels=8, fifo_depth=256, fifo_width=16, DL_id=0, wr_freq=20, rd_freq=37.5, arbiter_name="round_robin_skip", write_up=False, **kwargs):
        '''
        This is the constructor for the AsyncDataline class.
        Args:
            num_of_channels: Simply the number of channels in the data line. By default, it is 8
            fifo_depth: FIFO depth for each channel
            fifo_width: The word length for each FIFO entry
            DL_id: Simply the ID for the data line, useful when there are multiple data lines in the simulation
            wr_freq: The writing frequency in MHz, the smallest resolution is 0.1 MHz
            rd_freq: The reading frequency in MHz the smallest resolution is 0.1 MHz
            arbiter_name: the type of arbiter to use, by default it is "round_robin_skip", available options are "round_robin" and "urgency"
        '''
        self.channels = [channel(chan_id=i, fifo_depth=fifo_depth, fifo_width=fifo_width) for i in range(num_of_channels)]
        self.num_of_channels = num_of_channels
        if arbiter_name == "round_robin":
            self.arbiter = arbiter(self.channels)
        elif arbiter_name == "urgency":
            self.arbiter = ArbiterUrgency(self.channels)
        elif arbiter_name == "round_robin_skip":
            self.arbiter = RoundRobinSkipEmpty(self.channels)
        elif arbiter_name == "CARR":
            self.arbiter = CARRArbiter(self.channels, max_reads=kwargs.get("max_reads", 16))
        else:
            raise Exception("Arbiter not supported yet")

        ## ID for the data line
        self.DL_id = DL_id

        ## Calculate the least common multiple for the writing and reading clock frequencies
        self.LCM_freq = int(wr_freq*rd_freq*100) // math.gcd(int(wr_freq*10), int(rd_freq*10))   # in MHz

        self.wr_enable_tick = self.LCM_freq // int(wr_freq*10)
        self.rd_enable_tick = self.LCM_freq // int(rd_freq*10)

        ## report the calculated tick enables only once when initialising
        print(f"Least Common Multiple Frequency: {self.LCM_freq//10} MHz, Writing Enable Tick: every {self.wr_enable_tick} ticks, Reading Enable Tick: every {self.rd_enable_tick} ticks.")

        ## Initialise the common tick counter
        self.common_tick_counter = 0

        ## To track the buffer space available in each channel dynamically
        self.buffer_space_track = [[] for _ in range(self.num_of_channels)]

        ## Whether to write up the popped words from the arbiter during the simulation, which is useful for later analysis of the data line performance.
        self.write_up = write_up


    def run_produce_live(self, data:np.ndarray, time_step:int):
        """
        This function will run the data production and compression live for the given time step.
        Args:
            data: the 5-pixel row data to be encoded which should be a numpy array of shape (num_of_channels*5,).
            time_step: Essentially the number of rows of the pixels being processed in the simulation. (This will not be a typical time step used in the previous data line class)


        """
        if data.shape != (self.num_of_channels*5,):
            raise Exception(f"Data shape is not correct, should be ({self.num_of_channels*5}, ), got {data.shape}")

        ## By default this assumes it is the writing enable tick satisfied so we loop through the channels and push the data into the FIFO buffer
        for chan in self.channels:
            chan.produce_and_push(data[chan.id*5:(chan.id+1)*5], time_step)


    def run_consume_live(self, time_step:int):
        """
        This function will run the data consumption live for the given time step.
        Args:
            time_step: Since produce and consume are separated, the time_step here will be the number of data consumption cycles in the simulation.


        """
        ## Run the arbiter to pop the data from the FIFO buffer
        self.arbiter.step(time_step)

    def update_buffer_space_track(self):
        """
        This function will update the buffer space track for each channel regardless of the produce or consume operation.
        """
        for i, chan in enumerate(self.channels):
            self.buffer_space_track[i].append(chan.fifo.space_available())

    def run_single_image(self, img:np.ndarray):
        """
        This is the method that will run the full asynchronous data line simulation for a single image.
        Args:
            img: the image that needs to be processed, should be a 2D numpy array where each row is a set of pixel values.

        Returns:

        """

        wr_step = 0
        rd_step = 0

        if self.write_up:
            print("Writing up the popped words from the arbiter during the simulation...")
            POP_word_file = open(f"DataLine_{self.DL_id}_popped_words.txt", "w")
            POP_word_file.write("Time Step, Channel ID, Popped Word(Hex), Popped Word(Dec)\n")

        ## check image shape
        if img.shape[1] != self.num_of_channels*5:
            raise Exception(f"Image shape is not correct, should be (N, {self.num_of_channels*5}), got {img.shape}")

        ## increment the common tick counter and run the produce and consume operations based on the enable ticks
        total_ticks = img.shape[0] * self.wr_enable_tick  # Total ticks that runs out the image writing

        for tick in range(total_ticks):
            if tick % self.wr_enable_tick == 0 and wr_step < img.shape[0]:
                ## Writing enable tick satisfied, run the produce operation
                self.run_produce_live(img[wr_step], wr_step)
                wr_step += 1

            if tick % self.rd_enable_tick == 0:
                ## Reading enable tick satisfied, run the consume operation
                self.run_consume_live(rd_step)
                rd_step += 1
                if self.write_up:
                    self.write_up_popped_words(POP_word_file, rd_step)

            ## Update the buffer space track for each channel
            self.update_buffer_space_track()

        if self.write_up:
            POP_word_file.close()


    def get_used_up_space_track(self):
        """
        This function will return the used up space in each channel in an ndarray.
        Returns:

        """
        buffer_space_track = np.array(self.buffer_space_track)
        used_up_space = self.channels[0].fifo.data_depth - buffer_space_track
        return used_up_space


    def write_up_popped_words(self, pop_file, read_step):
        """
        This function will write up the popped words from the arbiter during the simulation. This is useful for later analysis of the data line performance.

        The written information includes the reading time step, the channel ID that the popped word comes from and the popped word itself.

        """
        if self.arbiter.last_popped_word is not None:
            pop_file.write(f"{read_step-1}, {self.arbiter.channel_select[-1]}, {hex(self.arbiter.last_popped_word)}, {self.arbiter.last_popped_word}\n")








