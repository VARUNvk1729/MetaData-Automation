import os
import pandas as pd
import streamlit as st
import chardet

def process_paths(file_path, filter_files=False):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected_encoding = chardet.detect(raw_data)['encoding']
        encoding = detected_encoding if detected_encoding else 'utf-8'

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            paths = [line.strip() for line in f.readlines()]
    except UnicodeDecodeError:
        st.error(f"Failed to decode file with detected encoding: {encoding}.")
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

        file_exts = ['.pdf', '.docx', '.xlsx', '.txt', '.png', '.jpg', '.jpeg', '.zip', '.rar', '.csv']
        file_name = components[-1] if any(components[-1].lower().endswith(ext) for ext in file_exts) else None

        if filter_files and not file_name:
            continue

        folders = components[:-1] if file_name else components
        folder_path = os.path.join(drive, *components)
        max_depth = max(max_depth, len(folders))
        data.append((drive, folders, file_name, folder_path))

    columns = ["Drive"] + [f"Folder Level {i+1}" for i in range(max_depth)] + ["File Name", "Folder Path"]
    processed_data = []
    for drive, folders, file_name, folder_path in data:
        row = [drive] + folders + [None] * (max_depth - len(folders)) + [file_name, folder_path]
        processed_data.append(row)

    return pd.DataFrame(processed_data, columns=columns)

st.set_page_config(page_title="Path Categorizer", layout="centered")
st.markdown("## 📁 METADATA CATEGORISATION")
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
