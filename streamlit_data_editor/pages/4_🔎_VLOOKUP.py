import streamlit as st
import pandas as pd
import logging

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('vlookup.log')
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

st.set_page_config(page_title="Multi VLOOKUP", layout="wide")
st.title("🔁 Multiple VLOOKUPs with Master File")

# Init session
if "goto_next" not in st.session_state:
    st.session_state.goto_next = False

if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    master_file = st.file_uploader("📤 Upload Master File", type=["csv", "xlsx", "xlsb"])
    st.dataframe(st.session_state["merged_df"])

    if master_file:
        try:
            logger.info("Master file uploaded")

            # Load master file
            if master_file.name.endswith(".xlsb"):
                master_df = pd.read_excel(master_file, engine="pyxlsb")
            elif master_file.name.endswith(".csv"):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)

            # Normalize columns
            df.columns = df.columns.str.strip().str.lower()
            master_df.columns = master_df.columns.str.strip().str.lower()

            st.write("📄 Columns in current file:", df.columns.tolist())
            st.write("📄 Columns in master file:", master_df.columns.tolist())

            # Ask for match columns
            common_col = st.selectbox("🧩 Match column in current file", df.columns)
            master_col = st.selectbox("🧩 Match column in master file", master_df.columns)

            # Container for multiple VLOOKUPs
            st.markdown("### ➕ Add Multiple Columns to Fetch")
            vlookup_list = []
            col_to_fetch_list = master_df.columns.tolist()

            with st.form("multi_vlookup_form"):
                n = st.number_input("🔢 How many columns to fetch?", min_value=1, max_value=len(master_df.columns)-1, step=1)
                
                for i in range(n):
                    st.markdown(f"#### VLOOKUP {i+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        col_fetch = st.selectbox(f"📥 Column to fetch [{i+1}]", col_to_fetch_list, key=f"fetch_{i}")
                    with col2:
                        col_target_mode = st.radio(f"🛠 Where to store [{col_fetch}]", ["New column", "Update existing column"], key=f"mode_{i}")
                        if col_target_mode == "New column":
                            target_col = st.text_input("🆕 New column name", value=col_fetch, key=f"new_col_{i}")
                        else:
                            target_col = st.selectbox("✏️ Existing column", df.columns, key=f"exist_col_{i}")
                    vlookup_list.append((col_fetch, target_col))

                submit = st.form_submit_button("✅ Apply All VLOOKUPs")

            if submit:
                logger.info("Applying multiple VLOOKUPs")

                # Build merge dataframe
                temp_df = master_df[[master_col] + [col for col, _ in vlookup_list]].drop_duplicates()

                # Merge
                merged = df.merge(temp_df, how="left", left_on=common_col, right_on=master_col)

                # Rename columns
                for fetch_col, new_col in vlookup_list:
                    if fetch_col != new_col:
                        merged.rename(columns={fetch_col: new_col}, inplace=True)

                # Drop right join key if it's not the same as left
                if master_col != common_col and master_col in merged.columns:
                    merged.drop(columns=[master_col], inplace=True)

                st.session_state["merged_df"] = merged
                logger.info(f"Successfully applied {len(vlookup_list)} VLOOKUP(s)")
                st.success(f"✅ {len(vlookup_list)} VLOOKUP(s) applied successfully!")
                st.write("📐 New Shape:", merged.shape)
                st.dataframe(merged)
                st.dataframe(st.session_state["merged"])

        except Exception as e:
            logger.exception("Error in multiple VLOOKUP:")
            st.error(f"⚠️ Could not perform VLOOKUP: {e}")
else:
    st.warning("⚠️ Please upload and merge files first.")

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("💾 Save Changes"):
        st.success("Changes saved!")

with col2:
    if st.button("➡️ Continue"):
        st.info("Continuing to next step...")
        st.switch_page("pages/5_📤_Export.py")
        st.session_state.goto_next = True

with col3:
    if st.button("⬅️ Go Back to File Upload"):
        from streamlit_extras.switch_page_button import switch_page
        switch_page("4_🔎_VLOOKUP.py")

if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/5_📤_Export'" />""", unsafe_allow_html=True)
