from kbcstorage.client import Client
import streamlit as st
import pandas as pd
import csv
import os
import base64
from st_on_hover_tabs import on_hover_tabs
from streamlit_card import card
import time
import schedule
import datetime


# Constants
token = st.secrets["kbc_storage_token"]
url = st.secrets["kbc_url"]
LOGO_IMAGE_PATH = os.path.abspath("./app/static/keboola.png")

# Initialize Client
client = Client(url, token)

@st.cache_data(ttl=7200,show_spinner=False)
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
st.set_page_config(layout="wide")

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
    html_footer = f"""<div style="display: flex; justify-content: flex-end;margin-top: 12%"><div><p><strong>Version:</strong> 2.0</p></div><div style="margin-left: auto;"><img src="data:image/png;base64,{encoded_logo}" style="width: 100px;"></div></div>"""
    st.markdown(html_footer, unsafe_allow_html=True)

# Initialization
def init():
    if 'selected-table' not in st.session_state:
        st.session_state['selected-table'] = ""

    if 'data' not in st.session_state:
        st.session_state['data'] = None

    if 'go-to-data' not in st.session_state:
        st.session_state['go-to-data'] = False

    if 'tables_id' not in st.session_state:
        st.session_state['tables_id'] = pd.DataFrame(columns=['table_id'])

def write_to_keboola(data, table_name, table_path):
    """
    Writes the provided data to the specified table in Keboola Connection,
    updating existing records as needed.

    Args:
        data (pandas.DataFrame): The data to write to the table.
        table_name (str): The name of the table to write the data to.
        table_path (str): The local file path to write the data to before uploading.

    Returns:
        None
    """

    # Write the DataFrame to a CSV file with compression
    data.to_csv(table_path, index=False, compression='gzip')

    # Load the CSV file into Keboola, updating existing records
    client.tables.load(
        table_id=table_name,
        file_path=table_path,
        is_incremental=False
    )

def get_dataframe(table_name):
    """
    Retrieves a dataframe from a specified table.

    Args:
        table_name (str): The name of the table.

    Returns:
        pandas.DataFrame: The dataframe containing the table data.
    """
    table_detail = client.tables.detail(table_name)
    file_path = './' + table_detail['name']

    client.tables.export_to_file(table_id=table_name, path_name='')

    if os.path.exists(file_path):
        with open(file_path, mode='rt', encoding='utf-8') as in_file:
            lazy_lines = (line.replace('\0', '') for line in in_file)
            reader = csv.reader(lazy_lines, lineterminator='\n')
            if os.path.exists('data.csv'):
                os.remove('data.csv')
            else:
                print("The file does not exist")
    else:
        print(f"The file {file_path} does not exist")
        return pd.DataFrame()

    os.rename(table_detail['name'], 'data.csv')
    df = pd.read_csv('data.csv')
    return df

def write_to_log(data, table):
    log_df = pd.DataFrame({
            'table_id': table,
            'new': [data],
            'log_time': datetime.time,
            'user': "PlaceHolderUserID"
        })
    write_to_keboola(log_df, f'in.c-keboolasheets.log',f'updated_data_log.csv.gz')

# Fetch and prepare table IDs and short description
@st.cache_data(ttl=7200)
def fetch_all_ids():
    all_tables = client.tables.list()
    ids_list = [{'table_id': table["id"], 'displayName': table["displayName"], 'primaryKey': table["primaryKey"][0] if table["primaryKey"] else "",
                  'lastImportDate': table['lastImportDate'], 'rowsCount': table['rowsCount'], 'created': table['created']} for table in all_tables]
    return pd.DataFrame(ids_list)


# Create cards for tables in rows
def create_cards_in_rows(tables_df):
    cols = st.columns(3)  # Creates a row of 4 columns
    for index, row in tables_df.iterrows():
        with cols[index % 3]:
            display_table_card(row)

# Display a single table card
def display_table_card(row):
    card(
        title=row["displayName"].upper(),
        text=[f"Primary key: {row['primaryKey']}", f"Table ID: {row['table_id']}", f"Updated at: {row['lastImportDate']}", f"Created at: {row['created']}", f"Rows count: {str(row['rowsCount'])}"],
        styles={
            "card": {
                "width": "100%",
                "height": "100%",
                "borderRadius": "5px",
                "boxShadow": "none",
                "padding": "20px",
                "display": "flex",
                "paddingBottom": "30px",
                "justifyContent": "start",
    
            },
            "filter": {
                "background-color": "#b6dafa"
            },
            "title": {
                "color": "black",
                "font-size": "24px",
                "text-align":"left",
                "marginTop": "20px",  # Added space on top
                "marginLeft": "0",  # To keep the left margin neutral
                "marginRight": "0", 

            },
            "text": {
                "color": "black",
                "font-size": "12px",
                "marginLeft": "0",  # To keep the left margin neutral
                "marginRight": "0", 
            },
            "*":
            {
                "boxSizing": "borderBox",
                "width": "100%",
                "padding": "5px",
            },
        
            
        },
        image="https://upload.wikimedia.org/wikipedia/en/4/48/Blank.JPG" ,
        key=row['table_id'],
        on_click=lambda table_id=row['table_id']: st.session_state.update({"selected-table": table_id, "go-to-data": True})
    )
    
def main():
    init()
    display_logo()
    #st.title("data")
    st.session_state["tables_id"] = tables_df = fetch_all_ids()
    st.session_state["selected-table"] = tables_df.loc[0, 'table_id']
    st.session_state["data"] = get_dataframe(st.session_state["selected-table"])

    if len(tables_df) != 0:
        st.title("Tables from Keboola")
        st.write('Select and click on a specific table you want to edit.')
        w7, w8, w9 = st.columns([8, 2, 2])
        if w9.button("Reload Tables List", key="reload-tables"):
            st.session_state["tables_id"] = tables_df = fetch_all_ids()
            st.toast('Tables List Reloaded!', icon = "✅")
        w1 = st.columns([1])            
        create_cards_in_rows(st.session_state["tables_id"])
        if st.session_state["go-to-data"] == True:
            st.switch_page("pages/Data_Editor.py")
    else:
        st.error('Data is not loaded yet.')
        
    display_footer()
      
if __name__ == '__main__':
    main()


