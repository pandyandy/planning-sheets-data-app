from kbcstorage.client import Client
import streamlit as st
import pandas as pd
import csv
import os
from streamlit_option_menu import option_menu




ci = CommonInterface()


token = st.secrets["kbc_bucket_token"]
bucket_id = st.secrets["custom_bucket_id"]


st.set_page_config(
    
    layout="wide",
    
)


client_upload = Client('https://connection.north-europe.azure.keboola.com', token)



def get_dataframe(table_name):
    client = Client('https://connection.north-europe.azure.keboola.com', token)

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
  
  




with st.sidebar:
    choose = option_menu("Data manipulation", ["Data-editor"],
                         icons=['people', 'activity', 'person lines fill', 'activity'],
                         menu_icon="app-indicator", default_index=0,
                         styles={
        "container": {"padding": "5!important", "background-color": "#000000"},
        "icon": {"color": "#ffc52f", "font-size": "25px"}, 
        "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "grey"},
        "nav-link-selected": {"background-color": "#0082fa"},
    }
    )


if choose == "Data-editor":
    def main():
        
        st.title("APP: Data-editor")
        client = Client('https://connection.north-europe.azure.keboola.com', token)
        tables = client.buckets.list_tables(bucket_id = bucket_id)
        table_list = pd.DataFrame(tables)
        st.dataframe(table_list['id'])
        
        


        # Get the unique values from a specific column. Replace 'column_name' with your actual column name.
        unique_values = table_list['id'].unique()
        # Add 'All' option to the unique values list
        options = ['empty'] + list(unique_values)
        # Create a select box with the unique values
        selected_value = st.selectbox('Select a value', options=options)
        st.markdown(selected_value)


        


        data = get_dataframe(selected_value)


        # Display the data in an editable table using st.data_editor
        edited_data = st.data_editor(data, num_rows="dynamic", width=1400, height=500)



        if st.button("Send to Keboola"):
            os.remove('updated_data.csv.gz')
            st.markdown(selected_value)
            edited_data.to_csv('updated_data.csv.gz', index=False,compression='gzip')
            
            client_upload.tables.load(table_id = selected_value , file_path='updated_data.csv.gz', is_incremental=False)
    if __name__ == '__main__':
        main()
