import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="➕ Add Column", layout="wide")
st.title("➕ Add Column")

# Flag to simulate navigation
if "goto_next" not in st.session_state:
    st.session_state.goto_next = False

# Check if merged_df exists in session state
if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    st.dataframe(df)

    st.markdown("### Column Creation Settings")

    # Input multiple column names (comma-separated)
    col_names_input = st.text_area("Enter column names (comma-separated)", placeholder="e.g. Status,Remarks,Updated By")
    col_names = [col.strip() for col in col_names_input.split(",") if col.strip()]

    # Select where to insert new columns
    insert_after_col = st.selectbox("Insert new columns after:", ["At Beginning"] + list(df.columns))

    # Column type selection
    col_type = st.radio("Column Type", ["Blank", "Today's Date", "Custom Value"])
    
    # For custom value or formula, provide an additional option
    custom_or_formula = st.radio("Custom Value Type", ["Text/Number", "Formula"], key="custom_or_formula")
    custom_val = None
    formula = None

    if custom_or_formula == "Text/Number":
        if col_type == "Custom Value":
            custom_val = st.text_input("Enter custom text or number")
    else:
        if col_type == "Custom Value":
            formula = st.text_input("Enter formula (e.g., `Roll Qty * 45 / 1000`)", placeholder="e.g. Roll Qty * 45 / 1000")

    # Add columns when button is clicked
    if st.button("➕ Add Columns"):
        for i, col_name in enumerate(col_names):
            # Define new column data based on the selected column type
            if col_type == "Blank":
                new_col_data = ""  # Blank column
            elif col_type == "Today's Date":
                new_col_data = datetime.today().strftime('%Y-%m-%d')  # Today's date
            elif custom_or_formula == "Text/Number":
                new_col_data = custom_val  # Custom value
            elif custom_or_formula == "Formula":
                try:
                    # Apply the formula to each row
                    new_col_data = df.eval(formula).astype(str)  # Evaluate formula and convert to string
                except Exception as e:
                    st.error(f"Error applying formula: {str(e)}")
                    new_col_data = [""] * len(df)  # Default empty values if formula fails

            # Insert new column at the appropriate location
            if insert_after_col == "At Beginning":
                df.insert(i, col_name, new_col_data)
            else:
                idx = df.columns.get_loc(insert_after_col) + 1 + i
                df.insert(idx, col_name, new_col_data)

        st.session_state["merged_df"] = df  # Store the updated dataframe
        st.success(f"✅ Added columns: {', '.join(col_names)}")
        st.dataframe(df)  # Display the updated dataframe

else:
    st.warning("Please upload and merge files first.")

# Footer Navigation
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("💾 Save Changes"):
        st.success("Changes saved!")

with col2:
    if st.button("➡️ Continue"):
        st.info("Continuing to next step...")
        # Use Streamlit's multipage functionality to navigate to the next page
        st.session_state.goto_next = True
        st.switch_page("pages/4_🔎_VLOOKUP.py")

with col3:
    if st.button("⬅️ Go Back to File Upload"):
        from streamlit_extras.switch_page_button import switch_page
        switch_page("3_➕_Add_Columns.py")

# Optional HTML redirect (if needed)
if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/4_🔎_VLOOKUP'" />""", unsafe_allow_html=True)
