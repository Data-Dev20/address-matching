import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📁 Upload and Merge Files")

uploaded_files = st.file_uploader("Upload CSV or Excel files (min 2)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files and len(uploaded_files) >= 2:
    st.success(f"{len(uploaded_files)} files uploaded.")
    merge_files = st.radio("Do you want to merge these files?", ["Yes", "No"])

    if merge_files == "Yes":
        dfs = []
        for file in uploaded_files:
            if file.name.endswith(".csv"):
                dfs.append(pd.read_csv(file))
            else:
                dfs.append(pd.read_excel(file))
        merged_df = pd.concat(dfs, ignore_index=True)
        st.session_state["merged_df"] = merged_df
        st.write("✅ Merged Data Preview")
        st.dataframe(merged_df)
        
        filename = st.text_input("Enter filename for download (without extension)", value="merged_file")
        file_format = st.selectbox("Download format", ["CSV", "Excel"])
        
        if file_format == "CSV":
            csv = merged_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Merged CSV", data=csv, file_name=f"{filename}.csv", mime="text/csv")
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                merged_df.to_excel(writer, index=False)
            st.download_button("Download Merged Excel", data=output.getvalue(), file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.info("Files stored in session. You can use them in other modules.")
        st.session_state["file_list"] = uploaded_files
else:
    st.warning("Please upload at least 2 files.")