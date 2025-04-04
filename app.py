import os
import pandas as pd
import streamlit as st
import chardet
import io

def looks_like_file(name):
    if '.' not in name:
        return False
    ext = os.path.splitext(name)[1][1:]
    return ext.isalpha() or (len(ext) <= 5 and not ext.isdigit())

def process_paths(file_buffer, filter_files=False):
    raw_data = file_buffer.read()
    detected_encoding = chardet.detect(raw_data)['encoding']
    encoding = detected_encoding if detected_encoding else 'utf-8'

    if encoding.lower() != 'utf-8':
        st.warning(f"⚠️ The uploaded file is not UTF-8 encoded. Detected encoding: {encoding}")

    try:
        file_buffer.seek(0)
        text_data = file_buffer.read().decode(encoding)
        paths = [line.strip() for line in text_data.splitlines()]
    except UnicodeDecodeError:
        st.error(f"❌ Failed to decode file with encoding: {encoding}.")
        return pd.DataFrame()

    data = []
    max_depth = 0

    for path in paths:
        drive, tail = os.path.splitdrive(path)
        if not drive:
            drive = 'No Drive'

        components = [c for c in tail.split(os.sep) if c]
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
    file_buffer = io.BytesIO(uploaded_file.getbuffer())

    filter_files = st.checkbox("🗂 Show only paths containing file names")
    df = process_paths(file_buffer, filter_files=filter_files)

    st.markdown("### 📋 Processed Output")
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="processed_paths.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("</div>", unsafe_allow_html=True)
