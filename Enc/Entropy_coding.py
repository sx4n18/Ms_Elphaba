import numpy as np


## This is a class header file for entropy related coding algorithms.

class LZ77:
    def __init__(self, search_buffer_size=20, lookahead_buffer_size=15):
        self.search_buffer_size = search_buffer_size
        self.lookahead_buffer_size = lookahead_buffer_size

    def compress(self, data):
        i = 0
        compressed = []

        while i < len(data):
            match_distance = 0
            match_length = 0

            # Search for the longest match in the search buffer
            search_start = max(0, i - self.search_buffer_size)
            search_buffer = data[search_start:i]

            # Lookahead buffer
            lookahead_buffer = data[i:i + self.lookahead_buffer_size]

            for j in range(len(search_buffer)):
                k = 0
                # Check for matches between search buffer and lookahead buffer
                while k < len(lookahead_buffer) and j + k < len(search_buffer) and search_buffer[j + k] == lookahead_buffer[k]:
                    k += 1

                if k > match_length:
                    match_length = k
                    match_distance = len(search_buffer) - j

            # Record the match (distance, length, next symbol) or literal
            if match_length > 0:
                next_symbol = data[i + match_length] if i + match_length < len(data) else ''
                compressed.append((match_distance, match_length, next_symbol))
                i += match_length + 1
            else:
                compressed.append((0, 0, data[i]))
                i += 1

        return compressed

    def decompress(self, compressed):
        decompressed = []

        for distance, length, next_symbol in compressed:
            if distance == 0 and length == 0:
                decompressed.append(next_symbol)
            else:
                start = len(decompressed) - distance
                for _ in range(length):
                    decompressed.append(decompressed[start])
                    start += 1
                if next_symbol:
                    decompressed.append(next_symbol)

        return ''.join(decompressed)


class rAsymmetric_Numeral_System:
    '''
    A simple range asymmetric numeral system for encoding and decoding.
    This encoder will encode the input message into a big integer and number of messages it encodes.

    To instantiate the class, you need to provide the following parameters:
    - labelling: a string/list of symbols randomly interleaved, where the appearance counts of each symbol
    corresponds to its occurring probability.
    - block_size: the size of the block
    '''
    def __init__(self, labelling: str | list):
        self.labelling = labelling
        self.block_size = len(labelling)

        # `symbol` appears in each block `count_per_block[symbol]` times
        # `count_before_index[i]` is the number of numbers labeled `labeling[i]` that are less than `i`
        # `symbol_table[symbol][i]` is the index in `labeling` of the `i`th number labeled `symbol`
        self.count_per_block = {}
        self.count_before_index = []
        self.symbol_table = {}
        for i, c in enumerate(labelling):
            if c not in self.symbol_table:
                self.count_per_block[c] = 0
                self.symbol_table[c] = []
            self.count_before_index.append(self.count_per_block[c])
            self.count_per_block[c] += 1
            self.symbol_table[c].append(i)


        # if the initial value of `X` is too small, then `C(X)` might equal `X`. but we want `C(X)` to be different from `X` for everything to be reversible
        # this is analogous to "appending a non-zero digit to the left of `X`" except in ANS it's "non-first-symbol symbol" instead
        # if you're sure that no message will ever start with the first symbol, you can set `initial_state = 0`
        self.initial_state = next((i for i, c in enumerate(labelling) if c != labelling[0]), len(labelling))

    def Cr(self, state: int, symbol: str):
        """Returns the `state + 1`th number labeled `symbol`"""

        # full_blocks * count_per_block[symbol] + symbols_left = state + 1
        full_blocks = (state + 1) // self.count_per_block[symbol]
        symbols_left = (state + 1) % self.count_per_block[symbol]  # equivalently, (state + 1) - full_blocks * self.count_per_block[symbol]
        if symbols_left == 0:
            full_blocks -= 1
            symbols_left = self.count_per_block[symbol]

        # Count `symbols_left` symbols within the block
        index_within_block = self.symbol_table[symbol][symbols_left - 1]

        # if `block_size` is a power of 2, this multiplication is a bitshift
        return full_blocks * self.block_size + index_within_block


    def Dx(self, state: int):
        """Counts the number of numbers labeled `symbol` that are less than `state`"""

        index_within_block = state % self.block_size  # if `block_size` is a power of 2, this is `state & (block_size - 1)`
        symbol = self.labelling[index_within_block]

        num_previous_blocks = state // self.block_size  # if `block_size` is a power of 2, this division is a bitshift
        count_before_block = self.count_per_block[symbol] * num_previous_blocks

        return symbol, count_before_block + self.count_before_index[index_within_block]


    def encode(self, message: str | list):
        state = self.initial_state
        for symbol in message[::-1]:
            state = self.Cr(state, symbol)
        return state

    def decode(self, state: int):
        message = ""
        while state > self.initial_state:
            symbol, state = self.Dx(state)
            message += symbol
        return message, state

class rANS_simple:

    def __init__(self, frequency: list | np.ndarray):
        if isinstance(frequency, np.ndarray):
            self.freq = [int(i) for i in frequency]
        else:
            self.freq = frequency
        self.M = int(np.sum(frequency))
        self.acumulate = [int(x) for x in np.concatenate(([0], np.cumsum(frequency)[0:self.M-1])).tolist()]
        self.symbols = np.arange(len(frequency)).tolist()
        self.init_state = int(self.M)

    def Cr(self, state: int, symbol: int):
        """ Return the `state + 1`th number labeled `symbol`'s index """
        new_state = (state // self.freq[symbol]) * self.M + self.acumulate[symbol] + state % self.freq[symbol]
        return new_state

    def Dx(self, state: int):
        """ Return the symbol and the number of symbols less than `state` """
        symbol = np.searchsorted(self.acumulate, state % self.M)
        count = state // self.M * self.freq[symbol] + state % self.freq[symbol]
        return symbol, count

    def encode(self, message: list | str):
        state = self.init_state
        for symbol in message[::-1]:
            state = self.Cr(state, symbol)
        return state

    def decode(self, state: int):
        message = []
        while state > self.init_state:
            symbol, state = self.Dx(state)
            message.append(symbol)
        return message[::-1], state


class StreamANS:
    '''
    The streaming ANS encoder that will encode the input into a predicted state and then comparing the predicted state with the current state.
    '''
    def __init__(self, labeling: str | list):
        self.labeling = labeling
        self.block_size = len(labeling)

        self.count_per_block = {}
        self.count_before_index = []
        self.symbol_table = {}
        for i, c in enumerate(labeling):
            if c not in self.symbol_table:
                self.count_per_block[c] = 0
                self.symbol_table[c] = []
            self.count_before_index.append(self.count_per_block[c])
            self.count_per_block[c] += 1
            self.symbol_table[c].append(i)

    def Cr(self, state: int, symbol: str):
        """Returns the `state + 1`th number labeled `symbol`"""

        full_blocks = (state + 1) // self.count_per_block[symbol]
        symbols_left = (state + 1) % self.count_per_block[symbol]
        if symbols_left == 0:
            full_blocks -= 1
            symbols_left = self.count_per_block[symbol]

        # Count `symbols_left` symbols within the block
        index_within_block = self.symbol_table[symbol][symbols_left - 1]

        return full_blocks * self.block_size + index_within_block

    def Dx(self, state: int):
        """Counts the number of numbers labeled `symbol` that are less than `state`"""

        # because of renormalization, `state` is guaranteed to be in [block_size, 2 * block_size - 1]
        index_within_block = state - self.block_size
        symbol = self.labeling[index_within_block]

        return symbol, self.count_per_block[symbol] + self.count_before_index[index_within_block]

    def encode(self, message: str | list, initial_state: int = 0):
        bitstream = 1
        state = [i for i in range(self.block_size) if self.Cr(i, message[-1]) >= self.block_size][
            initial_state]  # the `initial_state`th number X such that `block_size <= C(X) < 2 * block_size`

        for symbol in message[::-1]:

            # shrink `X` until `C(X) < 2N`
            predicted = self.Cr(state, symbol)
            normalized_state = state
            while predicted >= 2 * self.block_size:
                bitstream <<= 1
                bitstream |= normalized_state & 1
                normalized_state >>= 1
                predicted = self.Cr(normalized_state, symbol)

            state = predicted

        return state, bitstream

    def decode(self, state: int, bitstream):
        message = ""

        while True:
            symbol, state = self.Dx(state)
            message += symbol

            # expand `X` until `X >= N` or we run out of bits
            while state < self.block_size and bitstream > 1:
                state <<= 1
                state |= bitstream & 1
                bitstream >>= 1
            if state < self.block_size: break

        return message, state

class Simple_streamANS(rANS_simple):
    '''
    This is a simple streaming version of tht rANS that checks if the state in the range BEFORE encoding.
    if the state is in the range, it will encode the state and symbol.
    if the state is not in the range, it will renormalise the state by right shifting the state and save the bits that needs to be shifted,
    then encode the renormed_state and symbol.
    '''
    def __init__(self, frequency: list | np.ndarray):
        super().__init__(frequency)
        self.state = self.init_state
        self.individual_interval = {
            i: range(self.freq[i], 2 * self.freq[i]) for i in range(len(self.freq))
        }

    def Cr(self, state: int, symbol: int):
        # check if the state is in the range of the symbol
        if state in self.individual_interval[symbol]:
            stream_encoded_state = super().Cr(state, symbol)
            bit_stream = None
        else:
            # renormalise the state by right shifting the state and save the bits that needs to be shifted
            bits_needed_shifting = 0
            while (state >> bits_needed_shifting) not in self.individual_interval[symbol]:
                bits_needed_shifting += 1
            print(f"bits needed shifting for {state}: ", bits_needed_shifting)
            stream_encoded_state = super().Cr(state >> bits_needed_shifting, symbol)
            bit_stream = (state & ((1 << bits_needed_shifting) - 1))| (1 << bits_needed_shifting)

        return stream_encoded_state, bit_stream


if __name__ == "__main__":
    # Example usage
    lz77 = LZ77(search_buffer_size=20, lookahead_buffer_size=15)

    data = "ABABABABA"
    print("Original Data:", data)

    compressed = lz77.compress(data)
    print("Compressed:", compressed)

    decompressed = lz77.decompress(compressed)
    print("Decompressed:", decompressed)
