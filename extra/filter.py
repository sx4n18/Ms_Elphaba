import numpy as np
from scipy import signal


class single_out:
    '''
    This is a class that will filter out single pixel values from the quantised data.
    '''
    def __init__(self, pixel_num=5 ):
        self.pixel_num = pixel_num
        self._detect_mask = np.array([[1,1,1],[1, 0, 1],[1, 1, 1]])

    def convo_n_embed(self, data):
        '''
        This function will convolve the data with the detect mask and embed the result into an array of the same shape as the input data.
        The detect mask is a 3x3 array, so the result will be "one ring" slimmer than the input data, we shall fill the outer ring with ones.
        Args:
            data:

        Returns:

        '''
        ## convolve the data with the detect mask
        convolved_data = signal.convolve2d(data, self._detect_mask, mode='valid')

        ## create an array of the same shape as the input data, filled with ones
        embed_data = np.ones_like(data)

        ## embed the convolved data into the array, because the kernel is 3x3, the result will be "one ring" slimmer than the input data
        embed_data[1:-1, 1:-1] = convolved_data

        return embed_data


    def filter(self, quant_data, reassemble=False):
        '''
        This function will filter out single pixel values from the quantised data.
        Args:
            quant_data:

        Returns:

        '''

        ## check if the quant_data is a 2D array and the width is divisible by pixel_num
        if quant_data.ndim != 2:
            raise ValueError("The quant_data should be a 2D array.")
        if quant_data.shape[1] % self.pixel_num != 0:
            raise ValueError(f"The width of the quant_data should be divisible by {self.pixel_num}.")

        ## Split the array into parts of pixel_num width
        num_of_parts = quant_data.shape[1] // self.pixel_num
        split_data = np.array_split(quant_data, num_of_parts, axis=1)

        ## convolut the split data with the detect mask and create the mask to be used for filtering
        convolved_data = [self.convo_n_embed(part) for part in split_data]
        mask = np.array([np.where(conv_dat > 0, 1, 0) for conv_dat in convolved_data])

        ## filter the quant_data using the mask
        filtered_data = np.array([part * mask[i] for i, part in enumerate(split_data)])

        ## if needed, reshape the filtered data to the original shape
        if reassemble:
            filtered_data = np.hstack(filtered_data)
            if filtered_data.shape[1] != quant_data.shape[1]:
                raise ValueError("The filtered data does not have the same width as the original data.")

        return filtered_data


