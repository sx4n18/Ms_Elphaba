import numpy as np
import matplotlib.pyplot as plt

## This is the script to include the entropy class, which is used to calculate the entropy of the image
## Entropy is a measure of the amount of information in the image



## The simple entropy class
## Entropy is calculated using the formula:
## H(X) = -sum(p(x) * log2(p(x)))
## where p(x) is the probability of the pixel value x
## The entropy is calculated for each pixel value in the image
## The entropy is then normalised by the number of pixels in the image
## The entropy is then returned as a numpy array
## The entropy is then plotted as a heatmap

class simple_entropy:
    '''
    This is the simple entropy class, which is used to calculate the entropy of the image
    The entropy is calculated using the formula:
    H(X) = -sum(p(x) * log2(p(x)))
    where p(x) is the probability of the pixel value x

    The class parameters are:
    image: the image to calculate the entropy for, an nd numpy array
    pixel_depth: the pixel depth of the image, default is 8

    The class tributes are:
    entropy: the entropy of the image, a float
    '''

    def __init__(self, image: np.ndarray, pixel_depth: int = 8):
        self.image = image
        self.entropy = None
        self.pixel_depth = pixel_depth

    def calculate_entropy(self):
        '''
        Calculate the entropy of the image
        '''
        # get the histogram of the image
        hist, _ = np.histogram(self.image, bins=2**self.pixel_depth, range=(0, 2**self.pixel_depth-1))
        # calculate the probability of each pixel value
        prob = hist / np.sum(hist)
        # calculate the entropy
        self.entropy = -np.sum(prob * np.log2(prob + 1e-10))
        return self.entropy

    def plot_histogram(self):
        '''
        Plot the histogram of the image
        '''
        hist, _ = np.histogram(self.image, bins=2**self.pixel_depth, range=(0, 2**self.pixel_depth-1))
        plt.bar(range(2**self.pixel_depth), hist)
        plt.title("Histogram of the image")
        plt.xlabel("Pixel value")
        plt.ylabel("Frequency")
        plt.show()


class delentropy:
    '''
    This is the delentropy class, which is used to calculate the delta entropy of the image

    The delta entropy is calculated using the similar formula, but the probability is calculated using delta of the image.



    The class parameters are:
    image: the image to calculate the entropy for, an nd numpy array
    pixel_depth: the pixel depth of the image, default is 8

    The class tributes are:
    entropy: the entropy of the image, a float
    '''

    def __init__(self, image: np.ndarray, pixel_depth: int = 8):
        self.image = image
        self.entropy = None
        self.pixel_depth = pixel_depth