import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Data Processing App", layout="wide")
st.title("📊 Data Processing App")
st.markdown("Navigate through the sidebar to use different tools:")


st.title("📁 Upload and Merge Files")

# Flag to simulate navigation
if "goto_next" not in st.session_state:
    st.session_state.goto_next = False

# File upload
uploaded_files = st.file_uploader("Upload CSV or Excel files (min 2)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files and len(uploaded_files) >= 2:
    st.success(f"{len(uploaded_files)} files uploaded.")
    merge_files = st.radio("Do you want to merge these files?", ["Yes", "No"])

    if merge_files == "Yes":
        if st.button("Start Processing"):
            status = st.empty()
            status.info("⏳ Processing data... Please wait.")
            dfs = []
            for file in uploaded_files:
                if file.name.endswith(".xlsx"):
                    dfs.append(pd.read_excel(file))
                else:
                    dfs.append(pd.read_csv(file))
            merged_df = pd.concat(dfs, ignore_index=True)
            st.session_state["merged_df"] = merged_df
            status.empty()
            st.success(f"{len(uploaded_files)} Merged Data Preview!")
            st.write("📐 New Shape:", merged_df.shape)
            st.dataframe(merged_df)

            filename = st.text_input("Enter filename for download (without extension)", value="merged_file")
            file_format = st.selectbox("Download format", ["Excel", "CSV"])

            if file_format == "Excel":
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    merged_df.to_excel(writer, sheet_name='Sheet1', index=False)
                output.seek(0)
                st.download_button(
                    label="Download Merged Excel",
                    data=output.getvalue(),
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                csv = merged_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Merged CSV",
                    data=csv,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )

    else:
        st.info("Files stored in session. You can use them in other modules.")
        st.session_state["file_list"] = uploaded_files
else:
    st.warning("Please upload at least 2 files.")

# Buttons at bottom
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 Save Changes"):
        st.success("Changes saved!")

with col2:
    if st.button("➡️ Continue to Next Step"):
        # Uncomment this only if using Streamlit's multipage navigation
        st.switch_page("pages/1_🧹_Data_Editor.py")

        # Alternatively, simulate navigation (if not using multipage)
        st.session_state.goto_next = True

# Simulate page change (if needed)
if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/1_🧹_Data_Editor'" />""", unsafe_allow_html=True)
