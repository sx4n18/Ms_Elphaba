

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



if __name__ == "__main__":
    # Example usage
    lz77 = LZ77(search_buffer_size=20, lookahead_buffer_size=15)

    data = "ABABABABA"
    print("Original Data:", data)

    compressed = lz77.compress(data)
    print("Compressed:", compressed)

    decompressed = lz77.decompress(compressed)
    print("Decompressed:", decompressed)
