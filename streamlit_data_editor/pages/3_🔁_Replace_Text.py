import streamlit as st
import pandas as pd

st.title("🔁 Replace Text in Columns (Excel-style Filter)")

if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    col = st.selectbox("Select column", df.columns)

    unique_vals = df[col].dropna().unique().tolist()
    selected_vals = st.multiselect("Select values to replace", unique_vals[:50])  # limit to 50 values
    new_val = st.text_input("Enter new value to replace selected")

    if st.button("Replace"):
        df[col] = df[col].replace(selected_vals, new_val)
        st.session_state["merged_df"] = df
        st.success(f"Replaced {selected_vals} with '{new_val}'")

    st.dataframe(df)
else:
    st.warning("Please upload and merge files first.")