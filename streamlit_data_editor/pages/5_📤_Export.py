import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📤 Export Final File")

if "merged_df" in st.session_state:
    df = st.session_state["merged_df"]
    filename = st.text_input("Enter filename (without extension)", value="final_output")
    file_format = st.radio("Export Format", ["CSV", "Excel"])

    if file_format == "CSV":
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"{filename}.csv", mime="text/csv")
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", output.getvalue(), file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.warning("Please process data before exporting.")

if st.button("⬅️ Go Back to File Upload"):
        from streamlit_extras.switch_page_button import switch_page
        switch_page("1_Data_Editor.py")

# Simulate page change (if needed)
if st.session_state.get("goto_next", False):
    st.markdown("""<meta http-equiv="refresh" content="0; url='/page/1_🧹_Data_Editor'" />""", unsafe_allow_html=True)
