# RUN THIS TO UPDATE THE APP.PY FILE:
## gcloud compute scp "C:\Users\ashtiani\Desktop\WBLCA_Benchmarking\Material Intensity - Publication\Google Compute Engine\app.py" wblca-v2-mui-eci-20250305-205241:/home/ashtiani/mui-eci-dash-app/


import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import base64
import matplotlib.cm as cm

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=["https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap"],
    requests_pathname_prefix="/"  # Set this correctly when using an iframe

)
server = app.server  # Needed for Gunicorn

# ✅ Define Absolute Paths for Data Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


# ✅ Load Data Files Safely
wblca_results_path = os.path.join(DATA_DIR, "full_lca_results_02-21-2025_a1_to_a3.csv")
wblca_meta_data_path = os.path.join(DATA_DIR, "buildings_metadata_02-21-2025_a1_to_a3_new_construction.xlsx")

# ✅ Ensure Files Exist Before Loading
if os.path.exists(wblca_results_path):
    wblca_results_full = pd.read_csv(wblca_results_path, na_values=["NA", "NULL"])
else:
    raise FileNotFoundError(f"Missing file: {wblca_results_path}")

if os.path.exists(wblca_meta_data_path):
    wblca_meta_data = pd.read_excel(wblca_meta_data_path, na_values=["NA", "NULL"])
else:
    raise FileNotFoundError(f"Missing file: {wblca_meta_data_path}")

# Ensure 'project_index' is a string for merging
wblca_results_full['project_index'] = wblca_results_full['project_index'].astype(str)
wblca_meta_data['project_index'] = wblca_meta_data['project_index'].astype(str)

# **Force conversion of specific columns to numeric**
numeric_cols = ["inv_mass", "gwp", "service_life"]
for col in numeric_cols:
    wblca_results_full[col] = pd.to_numeric(wblca_results_full[col], errors='coerce')

# Perform a left join on 'project_index'
merged_df = pd.merge(wblca_results_full, wblca_meta_data, on="project_index", how="left")

# Compute derived columns safely
merged_df['mui (kg/m²)'] = np.where(
    merged_df['bldg_cfa'] != 0, merged_df['inv_mass'] / merged_df['bldg_cfa'], np.nan)

merged_df['eci (kgCO₂e/m²)'] = np.where(
    merged_df['bldg_cfa'] != 0, merged_df['gwp'] / merged_df['bldg_cfa'], np.nan)

merged_df['gwp_factor'] = np.where(
    merged_df['inv_mass'] != 0, merged_df['gwp'] / merged_df['inv_mass'], np.nan)


# Assuming 'merged_df' and 'wblca_meta_data' are loaded as DataFrame
categorical_options = [{'label': col, 'value': col} for col in merged_df.columns if merged_df[col].dtype == 'object']
numerical_options = [{'label': col, 'value': col} for col in merged_df.columns if merged_df[col].dtype in ['float64', 'int']]

# Restrict numerical options to only "mui (kg/m²)" and "eci (kgCO₂e/m²)"
material_numerical_options = [
    {"label": "Material Use Intensity", "value": "mui (kg/m²)"},
    {"label": "Embodied Carbon Intensity", "value": "eci (kgCO₂e/m²)"}
]

# Rename some feature names:
wblca_meta_data.rename(columns={
    'total_mass_a1_to_a3': 'total_mass_a1_to_a3 (kg)',
    'total_gwp_a1_to_a3': 'total_gwp_a1_to_a3 (kgCO₂e)',
    'mui_a1_to_a3': 'mui_a1_to_a3 (kg/m²)',
    'eci_a1_to_a3': 'eci_a1_to_a3 (kgCO₂e/m²)',
}, inplace=True)

# ✅ Encode Image
def encode_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded_string}"
    return None  # Avoid errors if file is missing

image_src = encode_image(os.path.join(ASSETS_DIR, "lcl-header.png"))

# ✅ Load Data Glossary
glossary_path = os.path.join(ASSETS_DIR, "data_glossary.xlsx")
if os.path.exists(glossary_path):
    df_glossary = pd.read_excel(glossary_path)
else:
    df_glossary = pd.DataFrame()  # Avoid errors if missing

# Layout with Page Title and Tabs
app.layout = html.Div([
    # ✅ Add header image
    html.Img(
        src=image_src,
        style={'width': '100%', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom': '10px'}
    ),

    # ✅ Add a Page Title
    html.H1(
        "Embodied Carbon and Material Use Intensity Visualizer",
        style={'textAlign': 'center', 'margin-top': '20px', 'margin-bottom': '10px', 'font-weight': 'bold', 'fontSize': '24px'}
    ),

    # ✅ Add dcc.Store to keep selections and graphs stored across tabs
    dcc.Store(id="material-level-selections"),
    dcc.Store(id="building-level-selections"),
    dcc.Store(id="material-graph-data"),
    dcc.Store(id="building-graph-data"),

    # ✅ Create Tab Layout
    dcc.Tabs(
        id="tabs",
        value="instructions",
        children=[
            dcc.Tab(
                label="Introduction",
                value="instructions",
                style={'fontWeight': 'bold', 'fontSize': '14px', 'height': '24px',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
                selected_style={'fontSize': '14px', 'height': '24px',
                                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                'backgroundColor': '#f4edff', 'borderTop': '1px solid black'}
            ),
            dcc.Tab(
                label="Data Glossary",
                value="glossary",
                style={'fontWeight': 'bold', 'fontSize': '14px', 'height': '24px',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
                selected_style={'fontSize': '14px', 'height': '24px',
                                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                'backgroundColor': '#f4edff', 'borderTop': '1px solid black'}
            ),
            dcc.Tab(
                label="Material Level Analysis",
                value="material_analysis",
                style={'fontWeight': 'bold', 'fontSize': '14px', 'height': '24px',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
                selected_style={'fontSize': '14px', 'height': '24px',
                                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                'backgroundColor': '#f4edff', 'borderTop': '1px solid black'}
            ),
            dcc.Tab(
                label="Building Level Analysis",
                value="building_analysis",
                style={'fontWeight': 'bold', 'fontSize': '14px', 'height': '24px',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
                selected_style={'fontSize': '14px', 'height': '24px',
                                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                'backgroundColor': '#f4edff', 'borderTop': '1px solid black'}
            ),
        ]),

    # ✅ Content of Tabs
    html.Div(id="tab-content")
], style={'font-family': 'Open Sans, sans-serif'})

# Callback to switch tab content
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    State("material-level-selections", "data"),
    State("material-graph-data", "data"),
)
def render_tab_content(tab, stored_selections, stored_graph):
    if tab == "instructions":
        return html.Div([
            html.P("This advanced dashboard is developed as part of the Carbon Leadership Forum's (CLF) WBLCA Benchmarking Study V2, designed primarily for the visualization of Material Use Intensity and Embodied Carbon Intensity. It serves as an interactive platform to explore the environmental impacts of building materials and construction practices. Detailed information on the data collection methodologies and metadata can be found in the associated journal publication, which is currently under review (placeholder for DOI).",
                   style={'textAlign': 'justify'}),
            html.H4("Purpose of the Tool:"),
            html.Ul([
                html.Li("Material Use Intensity and Embodied Carbon Visualization: Focuses on detailed presentation of material and carbon footprint data."),
                html.Li("Research and Data Background: Derived from the CLF’s comprehensive WBLCA Benchmarking Study V2, facilitating insights into sustainable building practices."),
            ]),
            html.H4("Scope of Analysis:"),
            html.Ul([
                html.Li("Life Cycle Assessment (LCA) scope is limited to cradle to gate impacts (A1 to A3)."),
                html.Li("Building scopes are limited to 'new construction' projects in North America."),
            ]),
            html.H4("Navigation Overview:"),
            html.Ul([
                html.Li("'Material Level Analysis': Allows detailed examination of material-specific data through filters, aggregation methods, and custom visualizations."),
                html.Li("'Building Level Analysis': Focuses on building-level data, offering insights through comparisons and analyses of different building types and construction metrics."),
            ]),
            html.H4("Using the Dashboard:"),
            html.Ul([
                html.Li("Interactive Visualizations: Graphs and charts update in real time based on user inputs."),
                html.Li("Customizable Outputs: Tailor visual outputs through detailed control panels to focus your analysis."),
                html.Li("Exportable Data: Download graphs and data summaries for offline use and further analysis."),
            ]),
            html.Br(),
            html.P("For questions, contact ashtiani@uw.edu. Enjoy exploring!",
                   style={'textAlign': 'center', 'marginTop': '20px'}),
            html.P("© Life Cycle Lab 2025", 
               style={'textAlign': 'center', 'marginTop': '20px', 'fontSize': '16px', 'color': 'gray'}),

        ], style={'padding': '20px'})

    elif tab == "glossary":
        # Define specific widths for each column based on typical content length
        column_styles = [
            {'if': {'column_id': df_glossary.columns[0]}, 'minWidth': '20px', 'width': '25px', 'maxWidth': '50px'},  # Adjusted for minimal content
            {'if': {'column_id': df_glossary.columns[1]}, 'minWidth': '50px', 'width': '125px', 'maxWidth': '125px'},  # Wider for more content
            {'if': {'column_id': df_glossary.columns[2]}, 'minWidth': '300px', 'width': '350px', 'maxWidth': '400px'},  # Description, usually lengthy
            {'if': {'column_id': df_glossary.columns[3]}, 'minWidth': '20px', 'width': '25px', 'maxWidth': '50px'}   # Units, typically short
        ]

        return html.Div([
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

    elif tab == "material_analysis":
        return html.Div([
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

    elif tab == "building_analysis":
        return html.Div([

            # Parent container for layout
            html.Div([
                # Left side (Dropdowns & Inputs) - 1/4 width
                html.Div([
                    # Filtering Area
                    html.Div([
                        html.Div("Add Filters (Optional):", style={"marginBottom": "5px"}),
                        dcc.Dropdown(
                            id="filter-categorical-features",
                            options=[
                                {"label": col, "value": col}
                                for col in wblca_meta_data.select_dtypes(
                                    include=["object", "category"]
                                ).columns
                            ],
                            placeholder="Select a feature...",
                            persistence=True,
                            persistence_type="session",
                            multi=True,
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Div(id="filter-values-container", children=[]),

                    html.Hr(),

                    # Dropdowns for categorical, numerical, and stacking variables
                    html.Div([
                        html.Label("Select Categories:"),
                        dcc.Dropdown(
                            id="categorical-variable",
                            options=[
                                {"label": col, "value": col}
                                for col in wblca_meta_data.select_dtypes(
                                    include=["object", "category"]
                                ).columns
                            ],
                            placeholder="Select a feature...",
                            persistence=True,
                            persistence_type="session",
                            style={'width': '100%'}
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Div([
                        html.Label("Select Metrics:"),
                        dcc.Dropdown(
                            id="numerical-variable",
                            options=[
                                {"label": col, "value": col}
                                for col in wblca_meta_data.select_dtypes(
                                    include=["number"]
                                ).columns
                            ],
                            placeholder="Select a feature...",
                            persistence=True,
                            persistence_type="session",
                            style={'width': '100%'}
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Div([
                        html.Label("Select Stacks (Optional):"),
                        dcc.Dropdown(
                            id="stacking-variable",
                            options=[
                                {"label": col, "value": col}
                                for col in wblca_meta_data.select_dtypes(
                                    include=["object", "category"]
                                ).columns
                            ],
                            placeholder="Select a feature...",
                            persistence=True,
                            persistence_type="session",
                            style={'width': '100%'}
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Hr(),

                    # Aggregation Method, Error Bars, and Orientation
                    html.Div([
                        html.Label("Aggregation Method:"),
                        dcc.RadioItems(
                            id="aggregation-method",
                            options=[
                                {"label": " Sum", "value": "sum"},
                                {"label": " Mean", "value": "mean"},
                                {"label": " Median", "value": "median"},
                                {"label": " Count", "value": "count"},
                            ],
                            value="sum",
                            inline=False,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Div([
                        dbc.Checkbox(  # ✅ FIX: Using dbc.Checkbox instead of dcc.Checkbox
                            id="show-error-bars",
                            label="Show Error Bars (quartiles)",
                            value=False,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Div([
                        html.Label("Orientation:"),
                        dcc.RadioItems(
                            id="graph-orientation",
                            options=[
                                {"label": " Vertical", "value": "v"},
                                {"label": " Horizontal", "value": "h"},
                            ],
                            value="v",
                            inline=False,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ], style={'marginBottom': '10px'}),

                    html.Hr(),

                    html.Div([
                        html.Label("Graph Dimensions:", style={'margin-bottom': '5px'}),

                        html.Div([
                            html.Div([
                                html.Label("W:", style={'margin-right': '5px'}),
                                dcc.Input(
                                    id='graph-width',
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
                                    id='graph-height',
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
                    dcc.Graph(id="bar-chart")
                ], style={'width': '70%', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'verticalAlign': 'top', 'padding-left': '10px' }),  # Right section (3/4 width)

            ], style={'display': 'flex', 'justify-content': 'space-between'}),  # Flex container to align sections horizontally
        ])

################## Material level callbacks ########################
@app.callback(
    Output("filter-values-container-material", "children"),
    Input("filter-categorical-features-material", "value"),
    State("material-level-selections", "data")  # ✅ Use stored selections
)
def update_filter_values_dropdowns_material(selected_features, stored_selections):
    if not selected_features:
        return []

    stored_selections = stored_selections or {}  # Ensure it's not None

    dropdowns = []
    for feature in selected_features:
        dropdowns.append(
            dbc.Col([
                html.Div(f"Filter {feature}:", style={"marginBottom": "5px"}),

                dcc.Dropdown(
                    id={"type": "filter-value-material", "feature": feature},
                    options=[{"label": val, "value": val} for val in merged_df[feature].dropna().unique()],
                    placeholder=f"Select values for {feature}",
                    multi=True,
                    value=stored_selections.get(feature, None),  # ✅ Restore stored selection
                    persistence=True,
                    persistence_type="session",
                ),
            ], width=6)
        )
    return dropdowns


@app.callback(
    [Output('visualization', 'figure'),
     Output("material-level-selections", "data"),
     Output("material-graph-data", "data")],
    [
        Input('primary_cat_feature_dropdown', 'value'),
        Input('secondary_cat_feature_dropdown', 'value'),
        Input('numerical_feature_dropdown', 'value'),
        Input('graph_width', 'value'),
        Input('graph_height', 'value'),
        Input('log_y_axis', 'value'),
        Input('stacked_100_percent', 'value'),
        Input('aggregation-method-material', "value"),
        Input({"type": "filter-value-material", "feature": dash.ALL}, "value"),
    ],
    [State("filter-categorical-features-material", "value")],
)
def process_data(
    primary_cat_feature, secondary_cat_feature, numerical_feature,
    graph_width, graph_height, log_y_axis, stacked_100_percent,
    aggregation_method_material,
    filter_values, filter_features
):

    # ✅ Handle empty selections
    if not secondary_cat_feature or not numerical_feature:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Please select features",
            xaxis_title="",
            yaxis_title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=graph_width if graph_width else 800,
            height=graph_height if graph_height else 600,
            font=dict(family="Open Sans", size=12),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
        return empty_fig, {}, empty_fig.to_dict()

    # ✅ Filter dataset for relevant conditions
    filtered_df = merged_df[
        (merged_df['life_cycle_stage'] == 'A1-A3') &
        (merged_df['bldg_proj_type'] == 'New Construction')
    ].copy()

    # ✅ Replace 0 values with NaN for correct calculations
    filtered_df[numerical_feature] = filtered_df[numerical_feature].replace(0, np.nan)

    if filter_features and filter_values:
        for feature, values in zip(filter_features, filter_values):
            if values:
                filtered_df = filtered_df[filtered_df[feature].isin(values)]

    if secondary_cat_feature in wblca_meta_data.columns:
    #### Code 1 ####
        # ✅ Step 1: Compute total material intensity per project
        project_totals = (
            filtered_df.groupby('project_index')[numerical_feature]
            .sum()
            .reset_index()
            .rename(columns={numerical_feature: 'total_material_intensity'})
        )

        # ✅ Step 2: Compute total material intensity by secondary_cat_feature (Mean or Median)
        project_totals = project_totals.merge(
            filtered_df[['project_index', secondary_cat_feature]].drop_duplicates(),
            on='project_index',
            how='left'
        )

        if aggregation_method_material == "mean":
            totals_by_secondary_cat = (
                project_totals.groupby(secondary_cat_feature)['total_material_intensity']
                .mean()
                .reset_index()
                .rename(columns={'total_material_intensity': 'secondary_cat_agg'})
            )
        else:  # Median
            totals_by_secondary_cat = (
                project_totals.groupby(secondary_cat_feature)['total_material_intensity']
                .median()
                .reset_index()
                .rename(columns={'total_material_intensity': 'secondary_cat_agg'})
            )

        # ✅ If primary_cat_feature is None, generate a simple bar chart
        if not primary_cat_feature:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=totals_by_secondary_cat[secondary_cat_feature],
                y=totals_by_secondary_cat['secondary_cat_agg'],
                name=aggregation_method_material.capitalize(),
                marker=dict(color='blue')
            ))

            fig.update_layout(
                title=f"Bar Chart of {numerical_feature} by {secondary_cat_feature} ({aggregation_method_material.capitalize()})",
                xaxis_title=secondary_cat_feature,
                yaxis_title=numerical_feature,
                plot_bgcolor='white',
                paper_bgcolor='white',
                width=graph_width if graph_width else 800,
                height=graph_height if graph_height else 600,
                font=dict(family="Open Sans", size=12),
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    type="log" if log_y_axis else "linear"
                )
            )
            return fig, {}, fig.to_dict()

        # ✅ Step 3: Compute contributions of primary_cat_feature per project
        contributions = (
            filtered_df.groupby(['project_index', primary_cat_feature])[numerical_feature]
            .sum()
            .reset_index()
        )

        # ✅ Merge project totals
        contributions = contributions.merge(
            project_totals,
            on='project_index',
            how='left'
        )

        # ✅ Compute contribution fraction per project
        contributions['primary_cat_contribution'] = (
            contributions[numerical_feature] / contributions['total_material_intensity']
        )

        # ✅ Step 4: Compute mean/median contributions by secondary_cat_feature
        if aggregation_method_material == "mean":
            contribution_means = (
                contributions.groupby([secondary_cat_feature, primary_cat_feature])['primary_cat_contribution']
                .mean()
                .reset_index()
            )
        else:  # Median
            contribution_means = (
                contributions.groupby([secondary_cat_feature, primary_cat_feature])['primary_cat_contribution']
                .median()
                .reset_index()
            )

        # ✅ Step 5: Normalize contributions to sum to 100%
        contribution_means['normalized_contribution'] = (
            contribution_means.groupby(secondary_cat_feature)['primary_cat_contribution'].transform(lambda x: x / x.sum())
        )

        # ✅ Step 6: Compute contributions to totals
        contribution_means = contribution_means.merge(
            totals_by_secondary_cat,
            on=secondary_cat_feature,
            how='left'
        )

        contribution_means['normalized_agg_contribution'] = (
            contribution_means['normalized_contribution'] * contribution_means['secondary_cat_agg']
        )

        # ✅ Prepare final output for visualization
        output_df = contribution_means[[secondary_cat_feature, primary_cat_feature, 'normalized_agg_contribution']]

        # ✅ Normalize values for 100% stacking mode
        if stacked_100_percent:
            total_per_category = output_df.groupby(secondary_cat_feature)['normalized_agg_contribution'].transform('sum')
            output_df['normalized_agg_contribution'] = output_df['normalized_agg_contribution'] / total_per_category
            y_label = "Percentage Contribution (%)"
        else:
            y_label = numerical_feature

        # Define a persistent color mapping
        def generate_color_map(categories):
            """Generate a distinct color for each category using a colormap"""
            cmap = cm.get_cmap('tab20', len(categories))  # Use a colormap with many distinct colors
            color_map = {category: f"rgb{tuple(int(255*x) for x in cmap(i)[:3])}" for i, category in enumerate(categories)}
            return color_map

        # Generate color mapping based on unique primary_cat_feature
        unique_primary_categories = output_df[primary_cat_feature].unique()
        color_mapping = generate_color_map(unique_primary_categories)

        # Apply the color mapping in the plot
        fig = px.bar(
            output_df,
            x=secondary_cat_feature,
            y="normalized_agg_contribution",
            color=primary_cat_feature,
            barmode="relative" if stacked_100_percent else "stack",
            color_discrete_map=color_mapping,  # ✅ Apply custom color mapping
            labels={secondary_cat_feature: secondary_cat_feature, "normalized_agg_contribution": y_label},
            title=f"Stacked Bar Plot of {primary_cat_feature} Contributions by {secondary_cat_feature} ({aggregation_method_material.capitalize()})",
        )

        fig.update_layout(
            font=dict(family="Open Sans", size=12),
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=graph_width if graph_width else 800,
            height=graph_height if graph_height else 600,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(showgrid=False, gridcolor="lightgray", gridwidth=0.5),
            yaxis=dict(
                showgrid=True,
                gridcolor="lightgray",
                gridwidth=0.5,
                type="log" if log_y_axis and not stacked_100_percent else "linear",
                tickformat=".0%" if stacked_100_percent else None,
                range=[0, 1] if stacked_100_percent else None  # ✅ Ensures 0-100% range for stacked mode
            ),
        )
        return fig, {}, fig.to_dict()


    else:
        #### Code 2 ####
        # ✅ Compute total per category (mean or median based on user selection)
        project_grouped_secondary = (
            filtered_df.groupby(['project_index', secondary_cat_feature])[numerical_feature]
            .sum()
            .reset_index()
        )

        # ✅ Choose aggregation method based on user selection
        if aggregation_method_material == "mean":
            secondary_cat_stats = (
                project_grouped_secondary.groupby(secondary_cat_feature)[numerical_feature]
                .mean()
                .reset_index()
                .rename(columns={numerical_feature: 'secondary_cat_agg'})
            )
        else:  # Median
            secondary_cat_stats = (
                project_grouped_secondary.groupby(secondary_cat_feature)[numerical_feature]
                .median()
                .reset_index()
                .rename(columns={numerical_feature: 'secondary_cat_agg'})
            )

        # ✅ If no stacking, generate a simple bar chart
        if not primary_cat_feature:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=secondary_cat_stats[secondary_cat_feature],
                y=secondary_cat_stats['secondary_cat_agg'],
                name=aggregation_method_material.capitalize(),
                marker=dict(color='blue')
            ))

            fig.update_layout(
                title=f"Bar Chart of {numerical_feature} by {secondary_cat_feature} ({aggregation_method_material.capitalize()})",
                xaxis_title=secondary_cat_feature,
                yaxis_title=numerical_feature,
                legend_title="Total",
                plot_bgcolor='white',
                paper_bgcolor='white',
                width=graph_width if graph_width else 800,
                height=graph_height if graph_height else 600,
                font={'family': 'Open Sans'},
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    type="log" if log_y_axis else "linear"
                ) if not stacked_100_percent else dict(
                    showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)'
                )  # ✅ Log scale only when not 100% stacked
            )
            return fig, {}, fig.to_dict()

        # ✅ Compute total per `primary_cat_feature` (mean or median based on user selection)
        project_grouped_primary = (
            filtered_df.groupby(['project_index', primary_cat_feature])[numerical_feature]
            .sum()
            .reset_index()
        )

        if aggregation_method_material == "mean":
            primary_cat_stats = (
                project_grouped_primary.groupby(primary_cat_feature)[numerical_feature]
                .mean()
                .reset_index()
                .rename(columns={numerical_feature: 'primary_agg'})
            )
        else:  # Median
            primary_cat_stats = (
                project_grouped_primary.groupby(primary_cat_feature)[numerical_feature]
                .median()
                .reset_index()
                .rename(columns={numerical_feature: 'primary_agg'})
            )

        # ✅ Map primary_cat_feature to secondary_cat_feature
        primary_to_secondary = filtered_df[[secondary_cat_feature, primary_cat_feature]].drop_duplicates()

        # ✅ Merge primary stats with secondary stats via mapping
        primary_cat_stats = primary_cat_stats.merge(primary_to_secondary, on=primary_cat_feature, how='left')
        primary_cat_stats = primary_cat_stats.merge(secondary_cat_stats, on=secondary_cat_feature, how='left')

        # ✅ Calculate **contribution percentage** per primary category
        primary_cat_stats['contribution'] = (
            primary_cat_stats['primary_agg'] / primary_cat_stats.groupby(secondary_cat_feature)['primary_agg'].transform('sum')
        )

        # ✅ Normalize contributions based on secondary_cat_feature stats
        primary_cat_stats['normalized_agg'] = primary_cat_stats['contribution'] * primary_cat_stats['secondary_cat_agg']

        # ✅ Prepare final dataframe for visualization
        output_df = primary_cat_stats[
            [secondary_cat_feature, primary_cat_feature, 'normalized_agg', 'contribution']
        ].sort_values(by=[secondary_cat_feature, 'normalized_agg'], ascending=[True, False])

        # ✅ Normalize values for 100% stacking mode
        if stacked_100_percent:
            total_per_category = output_df.groupby(secondary_cat_feature)['normalized_agg'].transform('sum')
            output_df['normalized_agg'] = output_df['normalized_agg'] / total_per_category
            y_label = "Percentage Contribution (%)"
        else:
            y_label = numerical_feature

        # ✅ Generate Stacked Bar Chart
        fig = px.bar(
            output_df,
            x=secondary_cat_feature,
            y="normalized_agg",
            color=primary_cat_feature,
            barmode="relative" if stacked_100_percent else "stack",
            labels={secondary_cat_feature: secondary_cat_feature, "normalized_agg": y_label},
            title=f"Stacked Bar Plot of {primary_cat_feature} Contributions by {secondary_cat_feature} ({aggregation_method_material.capitalize()})",
        )

        fig.update_layout(
            font=dict(family="Open Sans", size=12),
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=graph_width if graph_width else 800,
            height=graph_height if graph_height else 600,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(showgrid=False, gridcolor="lightgray", gridwidth=0.5),
            yaxis=dict(
                showgrid=True,
                gridcolor="lightgray",
                gridwidth=0.5,
                type="log" if log_y_axis else "linear",
                tickformat=".0%" if stacked_100_percent else None
            ),
        )

        return fig, {}, fig.to_dict()



################## Building level callbacks ########################

# ✅ Callback to dynamically generate filter dropdowns based on selected categorical features
@app.callback(
    Output("filter-values-container", "children"),
    Input("filter-categorical-features", "value"),
    State("building-level-selections", "data")  # ✅ Restore stored selections
)
def update_filter_values_dropdowns(selected_features, stored_selections):
    if not selected_features:
        return []

    stored_selections = stored_selections or {}  # Ensure it's not None

    dropdowns = []
    for feature in selected_features:
        dropdowns.append(
            dbc.Col(
                [
                    html.Div(f"Filter {feature}:", style={"marginBottom": "5px"}),

                    # ✅ Restore previously selected values
                    dcc.Dropdown(
                        id={"type": "filter-value", "feature": feature},
                        options=[
                            {"label": val, "value": val} for val in wblca_meta_data[feature].dropna().unique()
                        ],
                        value=stored_selections.get(feature, None),  # ✅ Restore previous selection
                        persistence=True,
                        persistence_type="session",
                        placeholder=f"Select values for {feature}",
                        multi=True,
                    ),
                ],
                width=6,
            )
        )
    return dropdowns


@app.callback(
    Output("building-level-selections", "data"),
    Input({"type": "filter-value", "feature": dash.ALL}, "value"),
    State("filter-categorical-features", "value"),
    prevent_initial_call=True  # ✅ Prevent overwriting on first load
)
def store_selected_filter_values(filter_values, selected_features):
    if not selected_features or not filter_values:
        return {}

    return {feature: values for feature, values in zip(selected_features, filter_values) if values}


@app.callback(
    Output("bar-chart", "figure"),
    [
        Input("categorical-variable", "value"),
        Input("numerical-variable", "value"),
        Input("aggregation-method", "value"),
        Input("graph-width", "value"),
        Input("graph-height", "value"),
        Input("graph-orientation", "value"),
        Input({"type": "filter-value", "feature": dash.ALL}, "value"),
        Input("stacking-variable", "value"),
        Input("show-error-bars", "value"),
    ],
    [State("filter-categorical-features", "value")],
)
def update_bar_chart(
    categorical, numerical, aggregation, width, height, orientation, filter_values, stacking, show_error_bars, filter_features
):
    # ✅ If no categorical or numerical feature is selected, return an empty placeholder figure
    if not categorical or not numerical:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Please select features",
            xaxis_title="",
            yaxis_title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=width if width else 800,
            height=height if height else 600,
            font={'family': 'Open Sans'},
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
        return empty_fig

    # Filter the data based on selected filters
    filtered_data = wblca_meta_data
    if filter_features and filter_values:
        for feature, values in zip(filter_features, filter_values):
            if values:
                filtered_data = filtered_data[filtered_data[feature].isin(values)]

    # Ensure a primary categorical variable is selected
    if not categorical:
        return {}

    # Get unique sorted categories to maintain consistent order
    sorted_categories = sorted(filtered_data[categorical].dropna().unique())

    if stacking:
        # Handle stacked bar chart
        if aggregation in ["mean", "median"]:
            # Calculate overall aggregation per primary category
            overall_agg = (
                filtered_data.groupby(categorical)[numerical]
                .agg(aggregation)
                .reset_index()
                .rename(columns={numerical: "OverallAggregate"})
            )

            # Calculate contributions to the overall aggregation
            contributions = (
                filtered_data.groupby([categorical, stacking])[numerical]
                .sum()
                .reset_index()
            )

            # Merge contributions with the overall aggregate
            contributions = contributions.merge(overall_agg, on=categorical)
            contributions["Contribution"] = (
                contributions[numerical] / contributions.groupby(categorical)[numerical].transform("sum")
            ) * contributions["OverallAggregate"]

            # Set x, y, and color for the stacked chart
            x = categorical
            y = "Contribution"
            color = stacking
        elif aggregation == "count":
            contributions = filtered_data.groupby([categorical, stacking]).size().reset_index(name="Count")
            x = categorical
            y = "Count"
            color = stacking
        elif categorical and numerical:
            contributions = (
                filtered_data.groupby([categorical, stacking])[numerical]
                .sum()
                .reset_index()
            )
            x = categorical
            y = numerical
            color = stacking
        else:
            return {}
    else:
        # Handle regular bar chart without stacking
        if aggregation == "count":
            grouped_data = filtered_data[categorical].value_counts().reset_index()
            grouped_data.columns = [categorical, "Count"]
            x = categorical
            y = "Count"
            color = None
        elif categorical and numerical:
            grouped_data = filtered_data.groupby(categorical).agg(
                {numerical: [aggregation, "count", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]}
            ).reset_index()
            grouped_data.columns = [categorical, "Value", "Count", "Q1", "Q3"]

            # Add error bars only if checkbox is checked and the aggregation method is mean or median
            if show_error_bars and aggregation in ["mean", "median"]:
                grouped_data["ErrorMinus"] = grouped_data["Value"] - grouped_data["Q1"]
                grouped_data["ErrorPlus"] = grouped_data["Q3"] - grouped_data["Value"]
            else:
                grouped_data["ErrorMinus"] = None
                grouped_data["ErrorPlus"] = None

            x = categorical
            y = "Value"
            color = None
        else:
            return {}

    # Create the y-axis label dynamically
    if stacking:
        y_axis_label = f"{numerical} (Contributions by '{stacking}')"
    else:
        y_axis_label = numerical if aggregation != "count" else "Count"

    # Swap x and y for horizontal orientation
    if orientation == "h":
        x, y = y, x
        x_axis_label = y_axis_label
        y_axis_label = categorical
        error_bar_plus = "ErrorPlus" if show_error_bars and aggregation in ["mean", "median"] else None
        error_bar_minus = "ErrorMinus" if show_error_bars and aggregation in ["mean", "median"] else None
        error_bar_args = {"error_x": error_bar_plus, "error_x_minus": error_bar_minus}
    else:
        x_axis_label = categorical
        error_bar_plus = "ErrorPlus" if show_error_bars and aggregation in ["mean", "median"] else None
        error_bar_minus = "ErrorMinus" if show_error_bars and aggregation in ["mean", "median"] else None
        error_bar_args = {"error_y": error_bar_plus, "error_y_minus": error_bar_minus}

    # Create the figure
    fig = px.bar(
        grouped_data if not stacking else contributions,
        x=x,
        y=y,
        color=color,
        barmode="stack" if stacking else "group",
        orientation=orientation,
        title=f"Bar Chart of {numerical if aggregation != 'count' else 'Counts'} by {categorical}"
              + (f" (Stacked by {stacking})" if stacking else ""),
        category_orders={categorical: sorted_categories},  # Maintain consistent order
        labels={
            x: x_axis_label,
            y: y_axis_label,
        },
        **error_bar_args,  # Dynamically add error bars
    )

    fig.update_layout(
        font=dict(family="Open Sans", size=12),
        width=width if width else 800,
        height=height if height else 600,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showgrid=orientation == "h", gridcolor="lightgray", gridwidth=0.5),
        yaxis=dict(showgrid=orientation == "v", gridcolor="lightgray", gridwidth=0.5),
    )
    return fig

# ✅ Ensure This Works with Gunicorn
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050)