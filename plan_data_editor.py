from kbcstorage.client import Client
import streamlit as st
import pandas as pd
import csv
import os
import base64
from st_on_hover_tabs import on_hover_tabs
from streamlit_card import card
from streamlit_server_state import server_state, server_state_lock

TOKEN = st.secrets["kbc_storage_token"]
URL = st.secrets["kbc_url"]

LOGO_IMAGE_PATH = os.path.abspath("./app/keboola.png")
STYLE_CSS_PATH = os.path.abspath("./app/style.css")

# Initialize Client
client = Client(URL, TOKEN)

@st.cache_data(ttl=7200)
def get_dataframe(table_name):
    table_detail = client.tables.detail(table_name)

    client.tables.export_to_file(table_id = table_name, path_name='')
    list = client.tables.list()
    with open('./' + table_detail['name'], mode='rt', encoding='utf-8') as in_file:
        lazy_lines = (line.replace('\0', '') for line in in_file)
        reader = csv.reader(lazy_lines, lineterminator='\n')
    if os.path.exists('data.csv'):
        os.remove('data.csv')
    else:
        print("The file does not exist")
    os.rename(table_detail['name'], 'data.csv')
    df = pd.read_csv('data.csv')
    return df

# Set Streamlit page config and custom CSS
def setup_streamlit():
    #st.set_page_config(layout="wide")
    with open(STYLE_CSS_PATH) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load and encode image for HTML
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Display logo
def display_logo():
    encoded_logo = get_base64_encoded_image(LOGO_IMAGE_PATH)
    logo_html = f"""<div style="display: flex; justify-content: flex-end;"><img src="data:image/png;base64,{encoded_logo}" style="width: 100px; margin-left: -10px;"></div>"""
    st.markdown(logo_html, unsafe_allow_html=True)

# Display footer
def display_footer():
    encoded_logo = get_base64_encoded_image(LOGO_IMAGE_PATH)
    html_footer = f"""<div style="display: flex; justify-content: flex-end;margin-top: 12%"><div><p><strong>Version:</strong> 1.1</p></div><div style="margin-left: auto;"><img src="data:image/png;base64,{encoded_logo}" style="width: 100px;"></div></div>"""
    st.markdown(html_footer, unsafe_allow_html=True)

# Initialization
if 'selected-table' not in st.session_state:
    st.session_state['selected-table'] = ""

with server_state_lock["tables_id"]:
    if "tables_id" not in server_state:
        server_state["tables_id"] = pd.DataFrame(columns=['table_id'])

# Fetch and prepare table IDs and short description
@st.cache_data(ttl=7200)
def fetch_all_ids():
    all_tables = client.tables.list()
    ids_list = [{'table_id': table["id"], 'displayName': table["displayName"], 'primaryKey': table["primaryKey"][0] if table["primaryKey"] else "",
                  'lastImportDate': table['lastImportDate'], 'rowsCount': table['rowsCount'], 'created': table['created']} for table in all_tables]
    return pd.DataFrame(ids_list)

# Create cards for tables in rows
def create_cards_in_rows(tables_df):
    num_rows = len(tables_df) // 4 + (1 if len(tables_df) % 4 else 0)
    for _ in range(num_rows):
        cols = st.columns(4)  # Creates a row of 4 columns
        for index, row in tables_df.iterrows():
            with cols[index % 4]:
                display_table_card(row)

# Display a single table card
def display_table_card(row):
    card(
        title=row["displayName"],
        text=[row["primaryKey"], row["table_id"], row["lastImportDate"], row["created"], str(row["rowsCount"])],
        styles={
            "card": {
                "width": "320px",
                "height": "200px",
                "borderRadius": "8px",
                "boxShadow": "none",
                "padding": "50px",
                "display": "flex",
            },
            "filter": {
                "background-color": "#EDF0F5"
            },
            "title": {
                "color": "black",
                "font-size": "24px",
                "display": "inlineBlock",
            },
            "text": {
                "color": "black",
                "font-size": "12px",
                "display": "inlineBlock",
            },
        },
        key=row['table_id'],
        on_click=lambda table_id=row['table_id']: st.session_state.update({"selected-table": table_id}) and st.experimental_rerun()
    )

def main():
    setup_streamlit()
    tables_df = fetch_all_ids()
    with st.sidebar:
        tabs = on_hover_tabs(tabName=['Tables', 'Data'], 
                            iconName=['folder', 'table_chart_view'],
                            styles = {'navtab': {'background-color':'#228dff;',
                                                'color': 'white',
                                                'font-size': '18px',
                                                'transition': '.3s',
                                                'white-space': 'nowrap',
                                                'text-transform': 'capitalize'},
                                    'tabOptionsStyle': {':hover :hover': {'color': 'black',
                                                                    'cursor': 'pointer'}},
                                    'iconStyle':{'position':'fixed',
                                                    'left':'7.5px',
                                                    'text-align': 'left'},
                                    'tabStyle' : {'list-style-type': 'none',
                                                    'margin-bottom': '30px',
                                                    'padding-left': '30px'}},
                            key="0", default_choice=1)

    if tabs == "Tables" or len(st.session_state["selected-table"]) == 0: 
        display_logo()
        st.title("Keboola Table Sheets")
        create_cards_in_rows(tables_df)
    

    elif tabs == 'Data' or len(st.session_state["selected-table"]) == 0:
        display_logo()
        st.title("Data Editor")
        st.subheader("Available Tables")
        option = st.selectbox(
        "Select table you want to show",
        server_state["tables_id"],
        index=None,
        placeholder="Select table",
        )

        st.subheader("Info")
        if option:
            st.write('You selected:', option)
            df = get_dataframe(option)
            filtered_df = server_state["tables_id"][server_state["tables_id"]['table_id'] == option]

            if not filtered_df.empty:
                # Pro každou kolonku ve vyfiltrovaném DataFrame zobrazíme informace
                for column in filtered_df.columns:
                    # Pro jednoduchost zde předpokládáme, že každá kolonka má jedinečnou hodnotu v rámci filtru
                    st.write(f"{column}: {filtered_df.iloc[0][column]}")
        else:        
            selected_table_id = st.session_state["selected-table"] 
            filtered_df = server_state["tables_id"][server_state["tables_id"]['table_id'] == selected_table_id]

            if not filtered_df.empty:
                # Pro každou kolonku ve vyfiltrovaném DataFrame zobrazíme informace
                for column in filtered_df.columns:
                    # Pro jednoduchost zde předpokládáme, že každá kolonka má jedinečnou hodnotu v rámci filtru
                    st.write(f"{column}: {filtered_df.iloc[0][column]}")
            st.write(st.session_state["selected-table"])
            df = get_dataframe(st.session_state["selected-table"])

        st.data_editor(df, disabled=True)
    display_footer()

      
if __name__ == '__main__':
    main()


