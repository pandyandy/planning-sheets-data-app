from kbcstorage.client import Client
import streamlit as st
import pandas as pd
import csv
import os
from streamlit_option_menu import option_menu
import base64

logo_image = os.path.abspath("./app/static/keboola.png")

logo_html = f"""<div style="display: flex; justify-content: flex-end;"><img src="data:image/png;base64,{base64.b64encode(open(logo_image, "rb").read()).decode()}" style="width: 100px; margin-left: -10px;"></div>"""
html_footer = f"""
 <div style="display: flex; justify-content: flex-end;margin-top: 12%">
        <div>
            <p><strong>Version:</strong> 1.1</p>
        </div>
        <div style="margin-left: auto;">
            <img src="data:image/png;base64,{base64.b64encode(open(logo_image, "rb").read()).decode()}" style="width: 100px;">
        </div>
    </div>
"""

token = st.secrets["kbc_storage_token"]
url = st.secrets["kbc_url"]

st.set_page_config(
    
    layout="wide",
    
)

client_upload = Client(url, token)


@st.cache_data(ttl=7200)
def get_dataframe(table_name):
    client = Client(url, token)

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
  

def main():
    
    # Set up Streamlit container with title and logo
    with st.container():
        st.markdown(f"{logo_html}", unsafe_allow_html=True)
        st.title("Interactive Keboola Sheets")
    
    client = Client(url, token)
    tables = client.tables.list()
    table_list = pd.DataFrame(tables)
    st.markdown('Tables Accessible By Provided Storage Token')
    st.dataframe(table_list['id'])

    # Get the unique values from a specific column. Replace 'column_name' with your actual column name.
    unique_values = table_list['id'].unique()
    # Add 'All' option to the unique values list
    options = ['empty'] + list(unique_values)
    # Create a select box with the unique values
    
    selected_value = st.selectbox('Select a table for editing', options=options)
    
    # Filter the dataset based on the selected value
    if selected_value == 'empty':
        st.markdown('No table selected')
    else:
        data = get_dataframe(selected_value)
    # Display the data in an editable table using st.data_editor
        edited_data = st.data_editor(data, num_rows="dynamic", width=1400, height=500)


    if st.button("Send to Keboola"):
        if os.path.exists('updated_data.csv'):
            os.remove('updated_data.csv.gz')
        else:
            print("The file does not exist")
        st.markdown(selected_value)
        st.markdown('Updated!')
        edited_data.to_csv('updated_data.csv.gz', index=False,compression='gzip')
        
        client_upload.tables.load(table_id = selected_value , file_path='updated_data.csv.gz', is_incremental=False)
    
    # Display HTML footer
    st.markdown(html_footer, unsafe_allow_html=True)
    
    # Hide Made with streamlit from footer
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if __name__ == '__main__':
    main()