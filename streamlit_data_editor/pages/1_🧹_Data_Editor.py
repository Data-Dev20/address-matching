import streamlit as st
import pandas as pd
from io import BytesIO


st.set_page_config(page_title="🚀 Data Editor", layout="wide")
st.title("🚀 Data Editor")

# Flag to simulate navigation
if "goto_next" not in st.session_state:
    st.session_state.goto_next = False

if "merged_df" in st.session_state:
    st.write("Here’s your merged data:")
    
else:
    st.warning("No merged data found. Please go back and upload files.")

if st.button("⬅️ Go Back to File Upload"):
    from streamlit_extras.switch_page_button import switch_page
    switch_page("1_File_Uploader.py")


if "merged_df" in st.session_state:
    df = st.session_state["merged_df"].copy()

    st.write(f"📐 Shape: {df.shape}")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    st.session_state["merged_df"] = edited_df
    st.success("Data updated.")
    st.write("📐 Updated Shape:", edited_df.shape)

    # Delete Columns
    st.subheader("🧨 Delete Columns")
    cols_to_delete = st.multiselect("Select columns to delete", edited_df.columns)
    if st.button("Delete Selected Columns"):
        edited_df.drop(columns=cols_to_delete, inplace=True)
        st.session_state["merged_df"] = edited_df
        st.success(f"Deleted columns: {cols_to_delete}")
        st.write("📐 New Shape:", edited_df.shape)
        st.dataframe(edited_df)

    # Delete Rows by Column and Value
    st.subheader("🧽 Delete Rows by Column and Value")
    col_to_filter = st.selectbox("Select column to filter", edited_df.columns)
    if col_to_filter:
        unique_vals = edited_df[col_to_filter].dropna().unique().tolist()
        vals_to_delete = st.multiselect("Select values to delete", unique_vals[:100])
        if st.button("Delete Rows with Selected Values"):
            edited_df = edited_df[~edited_df[col_to_filter].isin(vals_to_delete)]
            st.session_state["merged_df"] = edited_df
            st.success(f"Deleted rows with values {vals_to_delete} in column '{col_to_filter}'")
            st.write("📐 New Shape:", edited_df.shape)
            st.dataframe(edited_df)

    # Delete Rows by Index Range
    st.subheader("✂️ Delete Rows by Row Number")
    start_idx = st.number_input("Start Row Number (0-based index)", min_value=0, max_value=len(edited_df)-1, value=0)
    end_idx = st.number_input("End Row Number (exclusive)", min_value=start_idx+1, max_value=len(edited_df), value=start_idx+1)
    if st.button("Delete Rows in Range"):
        edited_df = edited_df.drop(edited_df.index[start_idx:end_idx])
        st.session_state["merged_df"] = edited_df
        st.success(f"Deleted rows from index {start_idx} to {end_idx-1}")
        st.write("📐 New Shape:", edited_df.shape)
        st.dataframe(edited_df)

    # Export options
    filename = st.text_input("Filename to save (leave blank to use previous)", value="merged_file")
    file_format = st.selectbox("Download format", ["CSV", "Excel"])

    if file_format == "CSV":
        csv = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"{filename}.csv", mime="text/csv")
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False)
        st.download_button("Download Excel", data=output.getvalue(), file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    
col1, col2,col3 = st.columns([1, 1,1])

with col1:
    if st.button("Save Changes"):
        
        st.success("Changes saved!")

with col2:
    if st.button("Continue"):
        st.session_state["merged_df"] = edited_df
        st.info("Continuing to next step...")
        st.switch_page("pages/2_🔁_Replace_Text.py")

        # Alternatively, simulate navigation (if not using multipage)
        st.session_state.goto_next = True
with col3:
    if st.button("⬅️ Go Back to File Upload", key="go_back_bottom"):
        from streamlit_extras.switch_page_button import switch_page
        switch_page("app.py")


# Simulate page change (if needed)
if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/2_🔁_Replace_Text'" />""", unsafe_allow_html=True)
