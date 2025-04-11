import os
import pandas as pd
from dash import html, register_page, dcc

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

layout = html.Div([
    # Parent container for layout
    html.Div([
        # Left side (Dropdowns & Inputs) - 1/4 width
        html.Div([

            # Filtering Area
            html.Div([
                html.Div("Add Filters (Optional):", style={"marginBottom": "5px"}),
                dcc.Dropdown(
                    id="filter-categorical-features-material",
                    options=[
                        {"label": col, "value": col}
                        for col in merged_df.select_dtypes(include=["object", "category"]).columns
                    ],
                    placeholder="Select a feature...",
                    multi=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ], style={'marginBottom': '10px'}),

            html.Div(id="filter-values-container-material", children=[]),

            html.Hr(),

            # Dropdowns for categorical, numerical, and stacking variables
            html.Div([
                html.Label("Select Categories:"),
                dcc.Dropdown(
                    id='secondary_cat_feature_dropdown',
                    options=categorical_options,
                    value=(stored_selections or {}).get("secondary_cat_feature", None),
                    placeholder="Select a feature...",
                    persistence=True,
                    persistence_type="session",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '10px'}),

            html.Div([
                html.Label("Select Metrics:"),
                dcc.Dropdown(
                    id='numerical_feature_dropdown',
                    # options=numerical_options,
                    options=material_numerical_options,
                    value=(stored_selections or {}).get("material_numerical_options", None),
                    placeholder="Select a feature...",
                    persistence=True,
                    persistence_type="session",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '10px'}),

            html.Div([
                html.Label("Select Stacks (Optional):"),
                dcc.Dropdown(
                    id='primary_cat_feature_dropdown',
                    options=[{'label': 'None', 'value': ''}] + categorical_options,
                    value=(stored_selections or {}).get("primary_cat_feature", None),
                    placeholder="Select a feature...",
                    persistence=True,
                    persistence_type="session",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '10px'}),

            html.Hr(),

            # Aggregation Method
            html.Div([
                html.Label("Aggregation Method:"),
                dcc.RadioItems(
                    id="aggregation-method-material",
                    options=[
                        {"label": " Mean", "value": "mean"},
                        {"label": " Median", "value": "median"},
                    ],
                    value="mean",
                    inline=False,
                    persistence=True,
                    persistence_type="session",
                ),
            ], style={'marginBottom': '10px'}),

            html.Div([
                dbc.Checkbox(
                    id="log_y_axis",
                    label="Logarithmic Y-Axis",
                    persistence=True,
                    persistence_type="session",
                    value=False,
                ),
            ], style={'margin-bottom': '10px'}),

            html.Div([
                dbc.Checkbox(  # ✅ New checkbox for 100% stacking
                    id="stacked_100_percent",
                    label="100% Stacked Bar Chart",
                    persistence=True,
                    persistence_type="session",
                    value=False,
                ),
            ], style={'margin-bottom': '10px'}),

            html.Hr(),

            html.Div([
                html.Label("Graph Dimensions:", style={'margin-bottom': '5px'}),

                html.Div([
                    html.Div([
                        html.Label("W:", style={'margin-right': '5px'}),
                        dcc.Input(
                            id='graph_width',
                            type='number',
                            placeholder="e.g., 800",
                            step=50,
                            persistence=True,
                            persistence_type="session",
                            style={'width': '80px'}
                        ),
                    ], style={'display': 'flex', 'align-items': 'center', 'margin-right': '10px'}),

                    html.Div([
                        html.Label("H:", style={'margin-right': '5px'}),
                        dcc.Input(
                            id='graph_height',
                            type='number',
                            placeholder="e.g., 600",
                            step=50,
                            persistence=True,
                            persistence_type="session",
                            style={'width': '80px'}
                        ),
                    ], style={'display': 'flex', 'align-items': 'center'}),
                ], style={'display': 'flex'}),
            ], style={'margin-bottom': '10px'}),

        ], style={'width': '25%', 'padding': '10px', 'display': 'inline-block', 'verticalAlign': 'top'}),  # Left section (1/4 width)

        # Right side (Graph) - 3/4 width
        html.Div([
            dcc.Graph(
                id='visualization',
                figure=go.Figure(**stored_graph) if stored_graph and "data" in stored_graph else go.Figure()
            )
        ], style={'width': '70%', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'verticalAlign': 'top', 'padding-left': '10px'}),  # Right section (3/4 width)

    ], style={'display': 'flex', 'justify-content': 'space-between'}),  # Flex container for alignment
])