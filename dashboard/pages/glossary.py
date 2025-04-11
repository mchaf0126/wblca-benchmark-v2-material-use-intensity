import os
import pandas as pd
from dash import html, register_page, dash_table

# ✅ Define Absolute Paths for Data Files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get current script directory
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
glossary_path = os.path.join(ASSETS_DIR, "data_glossary.xlsx")
if os.path.exists(glossary_path):
    df_glossary = pd.read_excel(glossary_path)
else:
    df_glossary = pd.DataFrame()  # Avoid errors if missing

register_page(__name__, path='/glossary')

# Define specific widths for each column based on typical content length
column_styles = [
    {'if': {'column_id': df_glossary.columns[0]}, 'minWidth': '20px', 'width': '25px', 'maxWidth': '50px'},  # Adjusted for minimal content
    {'if': {'column_id': df_glossary.columns[1]}, 'minWidth': '50px', 'width': '125px', 'maxWidth': '125px'},  # Wider for more content
    {'if': {'column_id': df_glossary.columns[2]}, 'minWidth': '300px', 'width': '350px', 'maxWidth': '400px'},  # Description, usually lengthy
    {'if': {'column_id': df_glossary.columns[3]}, 'minWidth': '20px', 'width': '25px', 'maxWidth': '50px'}   # Units, typically short
]

layout = html.Div([
    dash_table.DataTable(
        id='table',
        columns=[{"name": col, "id": col} for col in df_glossary.columns],
        data=df_glossary.to_dict('records'),
        style_cell={
            'textAlign': 'left',
            'padding': '5px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_table={
            'overflowX': 'auto',
            'width': '100%',
            'minWidth': '100%',
        },
        style_header={
            'backgroundColor': 'light-grey',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ],
        style_cell_conditional=column_styles,
        fill_width=True
    )
], style={'padding': '20px 20px 20px 20px', 'margin-top': '20px', 'box-shadow': '0 2px 2px 0 rgba(0,0,0,0.05)'})
