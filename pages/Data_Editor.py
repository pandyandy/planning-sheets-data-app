
import streamlit as st
import schedule
import time
import pandas as pd

from Tables import clear_alert, get_dataframe, write_to_keboola, write_to_log, fetch_all_ids, display_footer, display_logo, init

init()
display_logo()
#st.title("data")
st.session_state["tables_id"] = tables_df = fetch_all_ids()
st.session_state["selected-table-data"] = tables_df.loc[0, 'table_id']
option = ""

st.title("Data Editor")
w7, w8, w9 = st.columns([5, 2, 1])
if w9.button("Reload Data", key="reload-data"):
            st.session_state["data"] = get_dataframe(st.session_state["selected-table-data"])
            alert = st.success("Data Reloaded!")
            schedule.enter(delay = 3, action = clear_alert(alert))
st.subheader("Available Tables")

# print("Session before option DATA:", st.session_state["selected-table-data"])
# print("Session before option TAB:", st.session_state["selected-table-tab"])
# print("go to data flag:", st.session_state["go-to-data"])

option = st.selectbox(
"Select table you want to show",
st.session_state["tables_id"],
index=None,
placeholder="Select table",
)
if st.session_state["go-to-data"] == True:
        # print("Jsem zde")
        option = st.session_state["selected-table-tab"]
        st.session_state["go-to-data"] = False

if option:
    st.subheader("Info")
    st.session_state["selected-table-data"] = option
    # print("selected table from option:", st.session_state["selected-table-data"])
    with st.spinner('Data is loading...'):
        st.session_state["data"] = get_dataframe(st.session_state["selected-table-data"])
    filtered_df = st.session_state["tables_id"][st.session_state["tables_id"]['table_id'] == st.session_state["selected-table-data"]]
    if not filtered_df.empty:
        # Pro každou kolonku ve vyfiltrovaném DataFrame zobrazíme informace
        for column in filtered_df.columns:
            # Assuming each column has a unique value within the filter for simplicity
            column_value = filtered_df.iloc[0][column]

            title_text = {
                "table_id": "Table ID",  # Removed the colon after "table_id"
                "primaryKey": "Primary key",
                "lastImportDate": "Updated at",
                "rowsCount": "Rows Count",
                "created": "Created at"
            }

            # Use the get method to handle cases where column is not found in the title_text dictionary
            column_title = title_text.get(column, column)  # Fallback to column if not found in title_text

            html_content = f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <p style="margin: 0; font-weight: bold; margin-right: 5px;">{column_title}:</p>
                <p style="margin: 0; color: #333;">{column_value}</p>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
        st.markdown("###")

    st.session_state["data"] = st.data_editor(st.session_state["data"], disabled=False, use_container_width=True)

    if st.button("Save Data", key="save-data-tables"):
                    with st.spinner('Saving Data...'):
                        kbc_data = get_dataframe(st.session_state["selected-table-data"])
                        concatenated_df = pd.concat([kbc_data, st.session_state["data"]])
                        sym_diff_df = concatenated_df.drop_duplicates(keep=False)
                        write_to_log(sym_diff_df)
                        write_to_keboola(st.session_state["data"], st.session_state["selected-table-data"],f'updated_data.csv.gz')
                        time.sleep(5)
                        st.session_state["data"] = get_dataframe(st.session_state["selected-table-data"])
                    alert = st.success("Data Updated!") 
                    schedule.enter(delay = 3, action = clear_alert(alert))
display_footer()