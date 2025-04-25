## This is a simple implementation of a quantiser that will quantise the input pixel values.
## The expected pixel values are in the range of 0-1
## Where 0 means black and 1 means white
## But we might need to revserse the pixel values to match the compression algorithm
## The quantiser will quantise the pixel values to 2/3 bits depending on the requirement.
## As for the 2-bit quantiser, the thresholds used to quantise the pixel values are:
## [0.3-0.4, 0.5, 0.66]
## As for the 3-bit quantiser, the thresholds used to quantise the pixel values are:
## [0.2, 0.3, 0.4, 0.5, 0.66, 0.8, 0.9]
## The quantiser will return the quantised pixel values as a numpy array.

import numpy as np

class Quantiser_2B:
    '''
    Quantiser for 2-bit pixel values. This does not include the pixel value reversal.
    '''
    def __init__(self, thresholds: list = [0.35, 0.5, 0.66]):
        self.thresholds = thresholds

    def quantise(self, pixel_values: np.ndarray) -> np.ndarray:
        '''
        Quantise the pixel values to 2-bits.
        '''
        quantised_pixel_values = np.zeros_like(pixel_values, dtype=np.uint8)
        for i in range(len(self.thresholds)):
            quantised_pixel_values[pixel_values > self.thresholds[i]] = i+1
        return quantised_pixel_values

class Quantiser_2B_INV:
    '''
    Quantiser for 2-bit pixel values. This includes the pixel value reversal.
    '''
    def __init__(self, thresholds: list = [0.35, 0.5, 0.66]):
        self.thresholds = thresholds

    def quantise(self, pixel_values: np.ndarray) -> np.ndarray:
        '''
        Quantise the pixel values to 2-bits.
        '''
        quantised_pixel_values = np.zeros_like(pixel_values, dtype=np.uint8)
        reversed_pixel_values = 1 - pixel_values
        for i in range(len(self.thresholds)):
            quantised_pixel_values[reversed_pixel_values > self.thresholds[i]] = i+1
        return quantised_pixel_values

class Quantiser_3B:
    '''
    Quantiser for 3-bit pixel values. This does not include the pixel value reversal.
    '''

    def __init__(self, thresholds: list = [0.2, 0.3, 0.4, 0.5, 0.66, 0.8, 0.9]):
        self.thresholds = thresholds

    def quantise(self, pixel_values: np.ndarray) -> np.ndarray:
        '''
        Quantise the pixel values to 3-bits.
        '''
        quantised_pixel_values = np.zeros_like(pixel_values, dtype=np.uint8)
        for i in range(len(self.thresholds)):
            quantised_pixel_values[pixel_values > self.thresholds[i]] = i+1
        return quantised_pixel_values

class Quantiser_3B_INV:
    '''
    Quantiser for 3-bit pixel values. This includes the pixel value reversal.
    '''

    def __init__(self, thresholds: list = [0.2, 0.3, 0.4, 0.5, 0.66, 0.8, 0.9]):
        self.thresholds = thresholds

    def quantise(self, pixel_values: np.ndarray) -> np.ndarray:
        '''
        Quantise the pixel values to 3-bits.
        '''
        quantised_pixel_values = np.zeros_like(pixel_values, dtype=np.uint8)
        # limit the pixel values within the range of [0, 1]
        pixel_values = np.clip(pixel_values, 0, 1)
        reversed_pixel_values = 1 - pixel_values
        for i in range(len(self.thresholds)):
            quantised_pixel_values[reversed_pixel_values > self.thresholds[i]] = i+1
        return quantised_pixel_values


class Quantiser_3B_uniform_dist_INV:
    '''
    Quantiser for 3-bit pixel values, where given an upper limit, the thresholds are uniformly distributed.
    This includes the pixel value reversal.

    Parameters:
    upper_limit: float
        The upper limit of the pixel values, anything above this value is capped to this value due to the sensor
        limitations. The thresholds are uniformly distributed between 1-upper_limit and 1 with 8 levels.
        7 thresholds in between 1-upper_limit and 1.
    '''

    def __init__(self, upper_limit: float):
        # The thresholds are uniformly distributed between 1-upper_limit and 1 with 7 values in between.
        self.thresholds = np.linspace(1-upper_limit, 1, 8, False)[1:]

    def quantise(self, pixel_values: np.ndarray) -> np.ndarray:
        '''
        Quantise the pixel values to 3-bits.
        '''
        quantised_pixel_values = np.zeros_like(pixel_values, dtype=np.uint8)
        # limit the pixel values within the range of [0, 1]
        pixel_values = np.clip(pixel_values, 0, 1)
        reversed_pixel_values = 1 - pixel_values
        for i in range(len(self.thresholds)):
            quantised_pixel_values[reversed_pixel_values > self.thresholds[i]] = i+1
        return quantised_pixel_values


