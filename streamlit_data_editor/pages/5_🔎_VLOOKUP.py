import streamlit as st
import pandas as pd

st.title("🔎 VLOOKUP with Master File")

if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    master_file = st.file_uploader("Upload Master File", type=["csv", "xlsx"])

    if master_file:
        try:
            if master_file.name.endswith(".csv"):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)

            common_col = st.selectbox("Column to match on (from current file)", df.columns)
            master_col = st.selectbox("Column to fetch from master file", master_df.columns)

            if st.button("Apply VLOOKUP"):
                if common_col in df.columns and master_col in master_df.columns:
                    merged = df.merge(master_df[[common_col, master_col]], on=common_col, how="left")
                    st.session_state["merged_df"] = merged
                    st.success(f"Merged column '{master_col}' from master file.")
                    st.dataframe(merged)
                else:
                    st.error("❌ Column not found. Please check names.")
        except Exception as e:
            st.error(f"⚠️ Could not perform VLOOKUP: {e}")
else:
    st.warning("Please upload and merge files first.")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Save Changes"):
        st.success("Changes saved!")

with col2:
    if st.button("Continue"):
        st.info("Continuing to next step...")