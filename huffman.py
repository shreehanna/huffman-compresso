"""
File Compression Using Huffman Coding
DSA Mini Project (21CSC201J)

Lossless, byte-oriented Huffman compressor with a real binary file format.
Concepts: greedy algorithm, binary tree, min-heap (priority queue), dictionary.

Usage:
    python huffman.py compress   input.txt  output.huf
    python huffman.py decompress output.huf restored.txt
    python huffman.py demo       "this is an example of huffman coding"
    python huffman.py stats      input.txt
"""

import heapq
import os
import struct
import sys
from collections import Counter

MAGIC = b"HUF1"
# Header layout: MAGIC (4) | original length (8) | unique symbols k (2)
#                then k entries of: byte value (1) + frequency (4)
HEADER_FIXED = struct.Struct(">4sQH")
ENTRY = struct.Struct(">BI")


class Node:
    """Huffman tree node: leaf holds a symbol, internal node holds children."""

    def __init__(self, freq, symbol=None, left=None, right=None, order=0):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right
        self.order = order  # tie-breaker so encoder and decoder build the same tree

    def is_leaf(self):
        return self.left is None and self.right is None

    def __lt__(self, other):
        # Min-heap ordering: smaller frequency first, then creation order.
        return (self.freq, self.order) < (other.freq, other.order)


def count_frequencies(data):
    """Step 1: frequency table of every byte in the input."""
    return Counter(data)


def build_tree(freq):
    """Steps 2-4: build the Huffman tree using a min-heap (greedy)."""
    if not freq:
        return None
    heap = []
    order = 0
    for symbol in sorted(freq):  # sorted => deterministic
        heap.append(Node(freq[symbol], symbol=symbol, order=order))
        order += 1
    heapq.heapify(heap)
    while len(heap) > 1:
        a = heapq.heappop(heap)  # smallest
        b = heapq.heappop(heap)  # second smallest
        heapq.heappush(heap, Node(a.freq + b.freq, left=a, right=b, order=order))
        order += 1
    return heap[0]


def generate_codes(root):
    """Step 5: traverse tree, left edge = 0, right edge = 1 (iterative)."""
    codes = {}
    if root is None:
        return codes
    if root.is_leaf():  # only one distinct symbol: give it a 1-bit code
        codes[root.symbol] = "0"
        return codes
    stack = [(root, "")]
    while stack:
        node, code = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = code
        else:
            stack.append((node.right, code + "1"))
            stack.append((node.left, code + "0"))
    return codes


def pack_bits(data, codes):
    """Step 6: replace each byte with its code and pack bits into real bytes."""
    out = bytearray()
    buffer = 0
    nbits = 0
    for byte in data:
        code = codes[byte]
        buffer = (buffer << len(code)) | int(code, 2)
        nbits += len(code)
        while nbits >= 8:
            nbits -= 8
            out.append((buffer >> nbits) & 0xFF)
        buffer &= (1 << nbits) - 1  # keep only unwritten bits
    if nbits:  # final partial byte, padded with zeros on the right
        out.append((buffer << (8 - nbits)) & 0xFF)
    return bytes(out)


def compress_bytes(data):
    """Return the full compressed file (header + packed payload) as bytes."""
    freq = count_frequencies(data)
    header = bytearray(HEADER_FIXED.pack(MAGIC, len(data), len(freq)))
    for symbol in sorted(freq):
        header += ENTRY.pack(symbol, freq[symbol])
    if len(freq) <= 1:  # empty file or single repeated symbol: header is enough
        return bytes(header)
    codes = generate_codes(build_tree(freq))
    return bytes(header) + pack_bits(data, codes)


def decompress_bytes(blob):
    """Rebuild the tree from the header and decode bit by bit."""
    if len(blob) < HEADER_FIXED.size:
        raise ValueError("File too short to be a valid .huf file")
    magic, length, k = HEADER_FIXED.unpack_from(blob, 0)
    if magic != MAGIC:
        raise ValueError("Not a valid .huf file (bad signature)")
    pos = HEADER_FIXED.size
    if len(blob) < pos + k * ENTRY.size:
        raise ValueError("Corrupted file: header truncated")
    freq = {}
    for _ in range(k):
        symbol, f = ENTRY.unpack_from(blob, pos)
        freq[symbol] = f
        pos += ENTRY.size
    if length == 0:
        return b""
    if k == 1:
        return bytes([next(iter(freq))]) * length
    if sum(freq.values()) != length:
        raise ValueError("Corrupted file: frequency table mismatch")

    root = build_tree(freq)
    out = bytearray()
    node = root
    for byte in blob[pos:]:
        for shift in range(7, -1, -1):
            node = node.right if (byte >> shift) & 1 else node.left
            if node.is_leaf():
                out.append(node.symbol)
                if len(out) == length:
                    return bytes(out)
                node = root
    raise ValueError("Corrupted file: payload ended before all data was decoded")


def compress_file(src, dst):
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Input file not found: {src}")
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError("Input and output paths must be different")
    with open(src, "rb") as f:
        data = f.read()
    blob = compress_bytes(data)
    with open(dst, "wb") as f:
        f.write(blob)
    return len(data), len(blob)


def decompress_file(src, dst):
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Input file not found: {src}")
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError("Input and output paths must be different")
    with open(src, "rb") as f:
        blob = f.read()
    data = decompress_bytes(blob)
    with open(dst, "wb") as f:
        f.write(data)
    return len(blob), len(data)


def report(original, compressed):
    """Compression ratio and percentage reduction (formulas from the report)."""
    if original == 0:
        return "Original file is empty - nothing to compare."
    ratio = compressed / original
    return (f"Original size   : {original} bytes\n"
            f"Compressed size : {compressed} bytes (incl. header)\n"
            f"Compression ratio      = {ratio:.4f}\n"
            f"Compression percentage = {(1 - ratio) * 100:.2f}%")


def demo(text):
    data = text.encode("utf-8")
    freq = count_frequencies(data)
    root = build_tree(freq)
    codes = generate_codes(root)
    print("Original Text:", text)
    print("\nFrequency table:")
    for s, f in sorted(freq.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {chr(s)!r:6} : {f}")
    print("\nHuffman Codes:")
    for s, c in sorted(codes.items(), key=lambda x: (len(x[1]), x[1])):
        print(f"  {chr(s)!r:6} : {c}")
    bits = "".join(codes[b] for b in data)
    print("\nEncoded bits:", bits)
    print(f"Bits: {len(bits)} (vs {len(data) * 8} fixed 8-bit)")
    blob = compress_bytes(data)
    restored = decompress_bytes(blob)
    print("\nDecompressed Text:", restored.decode("utf-8"))
    print("Lossless check   :", "PASS" if restored == data else "FAIL")
    print("\n" + report(len(data), len(blob)))
    print("(Tiny inputs can grow because of the header - see Limitations.)")


def main(argv):
    if len(argv) >= 2 and argv[1] == "demo":
        demo(" ".join(argv[2:]) or "this is an example of huffman coding")
        return 0
    if len(argv) == 3 and argv[1] == "stats":
        with open(argv[2], "rb") as f:
            data = f.read()
        print(report(len(data), len(compress_bytes(data))))
        return 0
    if len(argv) == 4 and argv[1] in ("compress", "decompress"):
        try:
            if argv[1] == "compress":
                a, b = compress_file(argv[2], argv[3])
                print(report(a, b))
            else:
                a, b = decompress_file(argv[2], argv[3])
                print(f"Decompressed {a} bytes -> {b} bytes")
        except (OSError, ValueError) as e:
            print("Error:", e)
            return 1
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
