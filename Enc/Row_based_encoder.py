import numpy as np


## This is a class script for the row based encoders, which operate in a simple fashion.
## This encoder will be very simple, it will only dump the raw data into a packet when there is no match in the buffer.
## When there is a match, the encoder will not export anything.
## But also it will export the timestamp, this will be exported in 2 cases:
## 1. When there is a mismatch in the buffer
## 2. When the alarm rings, this will happen when the global timer loops around