"""
Huffman Compressor - web app (Streamlit, pure Python, no JavaScript written)
Run:  streamlit run web_app.py      (keep huffman.py in the same folder)
Install once:  pip install streamlit pandas
"""
import pandas as pd
import streamlit as st

import huffman

st.set_page_config(page_title="Huffman Compressor", page_icon="🗜", layout="wide")

# ---------- styling (CSS only) ----------
st.markdown("""
<style>
.stApp {background: linear-gradient(160deg,#12183a 0%,#3b2570 55%,#6b2f8f 100%);}
.block-container {padding-top: 2rem; max-width: 1100px;}
h1,h2,h3,p,label,span,div[data-testid="stMarkdownContainer"] {color:#f4f1ff;}
.hero {text-align:center; margin-bottom:1.2rem;}
.hero h1 {font-size:2.6rem; margin-bottom:0;}
.hero p {color:#cfc8ff; font-size:1.05rem;}
div[data-testid="stMetric"] {background:#ffffff; border-radius:16px; padding:16px 20px;
  box-shadow:0 6px 24px rgba(0,0,0,.25);}
div[data-testid="stMetric"] * {color:#1f2340 !important;}
div[data-testid="stMetricValue"] {font-weight:800;}
.stTabs [data-baseweb="tab-list"] {gap:8px;}
.stTabs [data-baseweb="tab"] {background:rgba(255,255,255,.10); border-radius:12px; padding:8px 18px;}
.stTabs [aria-selected="true"] {background:#7c4dff;}
div[data-testid="stFileUploader"] section {background:rgba(255,255,255,.10);
  border:2px dashed #b9a6ff; border-radius:16px;}
.stDownloadButton button, .stButton button {background:#7c4dff; color:white; border:0;
  border-radius:12px; font-weight:700; padding:.6rem 1.4rem;}
.stDownloadButton button:hover, .stButton button:hover {background:#5e35d1; color:white;}
.ok {background:#1faa59; color:white; padding:10px 16px; border-radius:12px; font-weight:600;}
.bad {background:#d93025; color:white; padding:10px 16px; border-radius:12px; font-weight:600;}
div[data-testid="stCode"] pre, div[data-testid="stCode"] code, div[data-testid="stCode"] span {color:#1f2340 !important; white-space:pre-wrap; word-break:break-all;}
.note {background:rgba(255,255,255,.12); padding:10px 16px; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero"><h1>🗜 Huffman File Compressor</h1>
<p>Lossless compression using Huffman Coding &nbsp;•&nbsp; DSA Mini Project</p></div>""",
            unsafe_allow_html=True)


# ---------- helpers ----------
def sym_label(b):
    names = {32: "space", 10: "\\n", 13: "\\r", 9: "\\t"}
    if b in names:
        return names[b]
    return chr(b) if 33 <= b < 127 else f"0x{b:02X}"


def code_table(data):
    freq = huffman.count_frequencies(data)
    codes = huffman.generate_codes(huffman.build_tree(freq))
    rows = [{"Symbol": sym_label(s), "Byte": s, "Frequency": f, "Huffman code": codes[s],
             "Code length": len(codes[s]), "Total bits": f * len(codes[s])}
            for s, f in freq.items()]
    return pd.DataFrame(rows).sort_values(["Frequency", "Byte"], ascending=[False, True]) \
        .reset_index(drop=True), freq


def tree_dot(freq):
    """Graphviz DOT source of the Huffman tree (rendered in the browser)."""
    root = huffman.build_tree(freq)
    lines = ['digraph G {', 'bgcolor="transparent"; rankdir=TB;',
             'node [style=filled, fontname="Helvetica", fontcolor=white];',
             'edge [color="#cfc8ff", fontcolor="#ffd9a0", fontname="Helvetica"];']
    stack, n = [(root, 0)], 0
    ids = {id(root): 0}
    while stack:
        node, i = stack.pop()
        if node.is_leaf():
            lines.append(f'n{i} [label="{sym_label(node.symbol)}\\n{node.freq}", '
                         f'shape=box, fillcolor="#1faa59"];')
        else:
            lines.append(f'n{i} [label="{node.freq}", shape=circle, fillcolor="#7c4dff"];')
            for child, bit in ((node.left, "0"), (node.right, "1")):
                n += 1
                ids[id(child)] = n
                lines.append(f'n{i} -> n{n} [label="{bit}"];')
                stack.append((child, n))
    lines.append("}")
    return "\n".join(lines)


def draw_tree(freq):
    """Works on both old and new Streamlit versions."""
    dot = tree_dot(freq)
    try:
        st.graphviz_chart(dot, width="stretch")
    except TypeError:
        st.graphviz_chart(dot, use_container_width=True)


def size_chart(original, compressed):
    df = pd.DataFrame({"Bytes": [original, compressed]}, index=["Original", "Compressed"])
    try:
        st.bar_chart(df, color="#b9a6ff", sort=False)
    except TypeError:
        st.bar_chart(df)


def show_results(original, compressed, data, heading_note=""):
    ratio = compressed / original if original else 0
    saved = (1 - ratio) * 100 if original else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Original size", f"{original:,} B")
    c2.metric("Compressed size", f"{compressed:,} B")
    c3.metric("Compression ratio", f"{ratio:.2f}")
    c4.metric("Space saved", f"{saved:.1f}%")
    if saved < 0:
        st.markdown('<div class="note">⚠ This file grew: the header (frequency table) costs more '
                    'than Huffman saves. Normal for very small or already-compressed files.</div>',
                    unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Size comparison")
        size_chart(original, compressed)
    with right:
        st.subheader("Huffman codes")
        df, freq = code_table(data)
        st.dataframe(df, height=300, hide_index=True)
    if len(freq) > 1:
        st.subheader("Huffman tree")
        if len(freq) <= 40:
            st.caption("Left edge = 0, right edge = 1. Green boxes are symbols with their "
                       "frequency; purple circles are merged nodes.")
            draw_tree(freq)
        else:
            st.info(f"{len(freq)} distinct symbols - too many to draw clearly "
                    "(showing the tree for up to 40). Try a smaller text file.")


tab1, tab2, tab3 = st.tabs(["🗜 Compress", "📄 Decompress", "🔬 Try with text"])

# ---------- Compress ----------
with tab1:
    up = st.file_uploader("Drag & drop any file here", key="comp")
    if up is not None:
        data = up.getvalue()
        if not data:
            st.warning("That file is empty - nothing to compress.")
        else:
            blob = huffman.compress_bytes(data)
            ok = huffman.decompress_bytes(blob) == data
            st.markdown('<div class="ok">✔ Compressed - lossless check passed</div>' if ok
                        else '<div class="bad">✘ Verification failed</div>',
                        unsafe_allow_html=True)
            st.write("")
            st.download_button("⬇ Download .huf file", blob, file_name=up.name + ".huf")
            st.write("")
            show_results(len(data), len(blob), data)

# ---------- Decompress ----------
with tab2:
    up2 = st.file_uploader("Drop a .huf file to restore it", key="decomp")
    if up2 is not None:
        try:
            restored = huffman.decompress_bytes(up2.getvalue())
        except ValueError as e:
            st.markdown(f'<div class="bad">✘ {e}</div>', unsafe_allow_html=True)
        else:
            name = up2.name[:-4] if up2.name.endswith(".huf") else up2.name + ".restored"
            st.markdown('<div class="ok">✔ Decompressed - original restored</div>',
                        unsafe_allow_html=True)
            st.write("")
            c1, c2 = st.columns(2)
            c1.metric("Compressed size", f"{len(up2.getvalue()):,} B")
            c2.metric("Restored size", f"{len(restored):,} B")
            st.write("")
            st.download_button("⬇ Download restored file", restored, file_name=name)

# ---------- Try with text ----------
with tab3:
    st.caption("Type any text and watch Huffman coding work on it live.")
    text = st.text_area("Your text", "this is an example of huffman coding", height=110)
    if text:
        data = text.encode("utf-8")
        blob = huffman.compress_bytes(data)
        df, freq = code_table(data)
        codes = huffman.generate_codes(huffman.build_tree(freq))
        bits = "".join(codes[b] for b in data) if len(freq) > 1 else "0" * len(data)
        m1, m2, m3 = st.columns(3)
        m1.metric("Fixed 8-bit encoding", f"{len(data) * 8} bits")
        m2.metric("Huffman encoding", f"{len(bits)} bits")
        m3.metric("Bits saved", f"{(1 - len(bits) / (len(data) * 8)) * 100:.1f}%")
        st.subheader("Encoded bit string")
        st.code(bits if len(bits) < 1500 else bits[:1500] + " ...", language=None)
        a, b = st.columns([1, 1])
        with a:
            st.subheader("Frequency & codes")
            st.dataframe(df, hide_index=True, height=320)
        with b:
            if 1 < len(freq) <= 40:
                st.subheader("Tree")
                draw_tree(freq)
        st.markdown("**Decoded back:** `" + huffman.decompress_bytes(blob).decode("utf-8") + "`")
