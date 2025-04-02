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


# Example Usage
lz77 = LZ77(search_buffer_size=10, lookahead_buffer_size=5)

data = "ABABCABAB"
print("Original Data:", data)

compressed = lz77.compress(data)
print("Compressed:", compressed)

decompressed = lz77.decompress(compressed)
print("Decompressed:", decompressed)