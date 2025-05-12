import streamlit as st
import pandas as pd

st.set_page_config(page_title="🔁 Replace Text in Columns (Excel-style Filter)", layout="wide")
st.title("🔁 Replace Value")

# Flag to simulate navigation
if "goto_next" not in st.session_state:
    st.session_state.goto_next = False

if "merged_df" in st.session_state:
    st.write("Here’s your merged data:")
    st.dataframe(st.session_state["merged_df"])
else:
    st.warning("No merged data found. Please go back and upload files.")


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



col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("Save Changes"):
        st.success("Changes saved!")

with col2:
    if st.button("Continue"):
        st.info("Continuing to next step...")
        st.switch_page("pages/3_➕_Add_Columns.py")

        # Alternatively, simulate navigation (if not using multipage)
        st.session_state.goto_next = True

with col3:
    if st.button("⬅️ Go Back to File Upload"):
        from streamlit_extras.switch_page_button import switch_page
        switch_page("2_🔁_Replace_Text.py")

# Simulate page change (if needed)
if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/3_➕_Add_Columns'" />""", unsafe_allow_html=True)
