File Compression Using Huffman Coding (DSA Mini Project, 21CSC201J)

Lossless byte-oriented Huffman compressor in pure Python (no dependencies).

Run
pip install streamlit pandas
streamlit run web_app.py   (web app in the browser: drag & drop, charts, code table, tree)
python app.py            (desktop app: Tkinter GUI, needs huffman.py beside it)
python huffman.py demo "this is an example of huffman coding"
python huffman.py compress   input.txt  output.huf
python huffman.py decompress output.huf restored.txt
python huffman.py stats      input.txt
python -m unittest -v test_huffman
How it works
Count byte frequencies (O(n))
Create leaf nodes, push into a min-heap (heapq)
Repeatedly pop the two smallest nodes, merge under a parent (greedy, O(k log k))
Traverse tree: left = 0, right = 1 -> prefix-free codes (O(k))
Encode and pack bits into real bytes (last byte zero-padded)
Write file: HUF1 magic | original length (8 B) | k (2 B) | k x (byte, freq 4 B) | payload

Decoder rebuilds the identical tree from the frequency table (deterministic tie-breaking by creation order) and walks it bit by bit until original length bytes are produced, so padding bits are ignored.

Edge cases handled

empty file, single repeated symbol, all 256 byte values, binary files, UTF-8 text, missing input, same input/output path, bad signature, truncated/corrupted data.
