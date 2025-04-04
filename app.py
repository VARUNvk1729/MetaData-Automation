import os
import pandas as pd
import streamlit as st
import chardet
import re

def looks_like_file(name):
    if '.' not in name:
        return False
    ext = os.path.splitext(name)[1][1:]
    return ext.isalpha() or (len(ext) <= 5 and not ext.isdigit())

def process_paths(file_path, filter_files=False):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected_encoding = chardet.detect(raw_data)['encoding']
        encoding = detected_encoding if detected_encoding else 'utf-8'

    if encoding.lower() != 'utf-8':
        st.warning(f"⚠️If you get any error then make text file as utf-8 and re-upload. Detected encoding: {encoding}")

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            paths = [line.strip() for line in f.readlines()]
    except UnicodeDecodeError:
        st.error(f"❌ Failed to decode file with encoding: {encoding}.")
        return pd.DataFrame()

    data = []
    max_depth = 0

    for path in paths:
        if ":" in path:
            drive, tail = path.split(":", 1)
            drive += ":"
        else:
            drive, tail = 'No Drive', path

        components = [c for c in re.split(r"[\\/]+", tail) if c]
        if not components:
            continue

        last = components[-1]
        is_file = looks_like_file(last)
        file_name = last if is_file else None

        if filter_files and not file_name:
            continue

        folders = components[:-1] if is_file else components
        folder_path = os.path.join(drive, *folders, file_name) if file_name else os.path.join(drive, *folders)
        max_depth = max(max_depth, len(folders))
        data.append((drive, folders, file_name, folder_path))

    columns = ["Drive"] + [f"Folder Level {i+1}" for i in range(max_depth)] + ["File Name", "Folder Path"]
    processed_data = []
    for drive, folders, file_name, folder_path in data:
        row = [drive] + folders + [None] * (max_depth - len(folders)) + [file_name, folder_path]
        processed_data.append(row)

    return pd.DataFrame(processed_data, columns=columns)

# Streamlit UI
st.set_page_config(page_title="Metadata Automation", layout="centered")

st.markdown("""
    <style>
        .main {
            background-color: #f9f9fb;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 0 10px rgba(0,0,0,0.08);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #003366;
        }
        .stButton>button {
            background-color: #003366;
            color: white;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            border: none;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        }
        .stDownloadButton>button {
            background-color: #28a745;
            color: white;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            border: none;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        }
        .stDataFrame {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main'>", unsafe_allow_html=True)

st.markdown("## 📁 METADATA AUTOMATION")
st.markdown("Upload a `.txt` file containing file/folder paths. You can choose to filter only file paths.")

uploaded_file = st.file_uploader("🔼 Upload a text file", type=["txt"])

if uploaded_file:
    temp_file = "uploaded_paths.txt"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    filter_files = st.checkbox("🗂 Show only paths containing file names")
    df = process_paths(temp_file, filter_files=filter_files)

    st.markdown("### 📋 Processed Output")
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        output_file = "processed_paths.xlsx"
        df.to_excel(output_file, index=False, engine='openpyxl')

        st.download_button(
            label="📥 Download Excel",
            data=open(output_file, "rb"),
            file_name="processed_paths.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("</div>", unsafe_allow_html=True)
