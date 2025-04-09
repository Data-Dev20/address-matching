import streamlit as st
import pandas as pd
from datetime import datetime

st.title("➕ Add Column")

if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    new_col = st.text_input("Enter new column name")
    col_type = st.radio("Column Type", ["Blank", "Today's Date", "Custom Value"])

    if col_type == "Custom Value":
        custom_val = st.text_input("Enter text or number")

    if st.button("Add Column"):
        if col_type == "Blank":
            df[new_col] = ""
        elif col_type == "Today's Date":
            df[new_col] = datetime.today().strftime('%Y-%m-%d')
        else:
            df[new_col] = custom_val
        st.session_state["merged_df"] = df
        st.success(f"Column '{new_col}' added.")
        st.dataframe(df)
else:
    st.warning("Please upload and merge files first.")