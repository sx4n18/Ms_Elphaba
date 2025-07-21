from Enc.Row_based_encoder import Row_encoder_5P
import numpy as np



class fifo :
    def __init__(self, data_depth=256, data_width = 16, id=None):
        self.buffer = []
        self.data_depth = 256
        self.data_width = 16
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


class channel:
    '''
    This is a class to encapsulate both the FIFO and the encoder.
    This assumes that the writing speed is 20MHz and the reading speed is 20MHz by default.


    '''
    def __init__(self, encoder="Row_encoder_5P", fifo_depth=256, fifo_width=16, wr_speed_ratio = 1, chan_id=None):
        self.id = chan_id
        self.fifo = fifo(fifo_depth, fifo_width, id=chan_id)
        if encoder == "Row_encoder_5P":
            self.encoder = Row_encoder_5P(id=chan_id)
        else:
            raise Exception("Encoder not supported yet")
        self.wr_speed_ratio = wr_speed_ratio  # This is the ratio of the writing speed to the reading speed

        # initialise the buffer available
        self._buffer_available = self.fifo.space_available()
        self._buffer_space_track = []

    def one_single_cycle(self, data:np.ndarray, time_step:int):
        '''
        This function will encode the data and push it into the FIFO buffer.
        In the meantime, if the FIFO is not empty, it will pop the data from the FIFO buffer.
        Args:
            data: the 5-pixel row data to be encoded which should be a numpy array of shape (5,).

        Returns:

        '''
        if self.fifo.is_full():
            raise Exception("FIFO is full, cannot push data")

        if data.shape != (5,):
            raise Exception("Data shape is not correct, should be (5,)")

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





