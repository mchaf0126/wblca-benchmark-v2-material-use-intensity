from dash import html, register_page


register_page(__name__, path='/')

layout = html.Div(
    [
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
        html.P([
            "CC BY 4.0 International Life Cycle Lab 2025 – ",
            html.A("Creative Commons Attribution 4.0 International License", 
                href="https://creativecommons.org/licenses/by/4.0/", 
                target="_blank", 
                style={'color': 'gray', 'textDecoration': 'none'})
        ], style={'textAlign': 'center', 'marginTop': '20px', 'fontSize': '16px', 'color': 'gray'})

    ], 
    style={'padding': '20px'}
)