import dash
from dash import dcc, html, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime


# =========================
# DASH INIT
# =========================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# =========================
# LOAD DATA (URL or CSV)
# =========================
# REPLACE THIS WITH YOUR LIVE SCRIPT/SHEET URL
DATA_SOURCE_URL = "https://script.google.com/macros/s/AKfycbxfqwdEiWRaSUpfSQoE5V_WBbCT74vM3Wj9F1rNM354EieRMYsMWtGnU_sRegLua50Ycg/exec" 

BENEFICIARY_MAP = {
    2: "Pregnant Women",
    3: "Children 5-9 Months",
    4: "Children Aged 5-9 Years (60 Months)",
    5: "Adolescent Girls 10-19 Years",
    6: "Adolescent Boys 10-19 Years",
    7: "Women Of Reproductive Age"
}

def load_data():
    try:
        if "google.com" in DATA_SOURCE_URL or "http" in DATA_SOURCE_URL:
             import requests
             # Single fast request with 5s timeout
             r = requests.get(DATA_SOURCE_URL, timeout=5)
             r.raise_for_status()
             
             try:
                 # Try JSON first (likely for Apps Script)
                 data_json = r.json()
                 if isinstance(data_json, dict) and 'data' in data_json:
                     df = pd.DataFrame(data_json['data'])
                 else:
                     df = pd.DataFrame(data_json)
             except:
                 # Fallback to CSV if URL returns raw CSV
                 from io import StringIO
                 df = pd.read_csv(StringIO(r.text))
        else:
             df = pd.read_csv("Prakash - Sheet1.csv")

        if df.empty:
            return pd.DataFrame()

        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Filter for required columns
        required_cols = [
            "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
            "Name", "Household Name", "Gender", "Benificiery", "DOB", "Age",
            "sample_status", "Sample Collected Date", "Collected By",
            "HGB", "anemia_category", "field_investigator", "Diet", "data_operator"
        ]
        df = df[[c for c in required_cols if c in df.columns]]

        # Data cleaning
        date_cols = ["DATE_F", "enrollment_date", "DOB", "Sample Collected Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        if "HGB" in df.columns:
            df["HGB"] = pd.to_numeric(df["HGB"], errors="coerce")
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
        
        if "Area COde" in df.columns:
            df["Area COde"] = df["Area COde"].astype(str).str.zfill(3)

        if "anemia_category" in df.columns:
            df["anemia_category"] = df["anemia_category"].astype(str).str.strip()
            cat_map = {"Normal": "normal", "Mild anemia": "mild", "Moderate anemia": "moderate", "Severe anemia": "severe"}
            df["anemia_category"] = df["anemia_category"].map(cat_map).fillna(df["anemia_category"].str.lower())

        if "Benificiery" in df.columns:
            df["Benificiery"] = pd.to_numeric(df["Benificiery"], errors='coerce')
            df["Benificiery"] = df["Benificiery"].map(BENEFICIARY_MAP).fillna(df["Benificiery"])
            df["Benificiery"] = df["Benificiery"].astype(str).str.title()

        if "Name" in df.columns:
            df["Name"] = df["Name"].astype(str).str.title()

        return df
    except Exception as e:
        print(f"Data load error: {e}. Falling back to local data if possible.")
        try:
            return pd.read_csv("Prakash - Sheet1.csv")
        except:
            return pd.DataFrame()

# Non-blocking initial lists (empty)
psu_list = []
area_list = []
anemia_list = ["normal", "mild", "moderate", "severe"]

# =========================
# MAP (AREA CODE BASED)
# =========================
def area_coordinates():
    return {
        'Kunikera': {'lat': 15.28, 'lon': 76.21},
        'Ojanahalli': {'lat': 15.43, 'lon': 76.53},
        'Hirehalli': {'lat': 15.38, 'lon': 76.12},
        'Ginigera': {'lat': 15.36, 'lon': 76.18},
        'Kanakagiri': {'lat': 15.40, 'lon': 76.14},
        'Tavarekoppa': {'lat': 15.33, 'lon': 76.16},
        'Hire Sindogi': {'lat': 15.37, 'lon': 76.11},
        'Kalavathi': {'lat': 15.34, 'lon': 76.20},
        'Mahalingpur': {'lat': 15.39, 'lon': 76.17},
        'Naveenakere': {'lat': 15.35, 'lon': 76.13},
        'Ginigere': {'lat': 15.32, 'lon': 76.19},
        'Karatagi': {'lat': 15.41, 'lon': 76.16},

        # Gangavathi Taluk villages
        'Gangavathi Town': {'lat': 15.43, 'lon': 76.53},
        'Hirehal': {'lat': 15.45, 'lon': 76.50},
        'Harlapur': {'lat': 15.40, 'lon': 76.55},
        'Hirevankalkunta': {'lat': 15.47, 'lon': 76.52},
        'Hunnur': {'lat': 15.42, 'lon': 76.48},
        'Kustagi': {'lat': 15.38, 'lon': 76.51},
        'Maski': {'lat': 15.44, 'lon': 76.57},
        'Yelbarga': {'lat': 15.46, 'lon': 76.54},

        # Kushtagi Taluk villages
        'Tavargera': {'lat': 15.78, 'lon': 76.18},
        'Hanumanal': {'lat': 15.74, 'lon': 76.21},
        'Kukanur': {'lat': 15.80, 'lon': 76.17},
        'Hirehosur': {'lat': 15.76, 'lon': 76.23},
        'Karatgi': {'lat': 15.73, 'lon': 76.20},
        'Kustagi Town': {'lat': 15.75, 'lon': 76.19},
        'Malasamudra': {'lat': 15.82, 'lon': 76.22},
        'Mamadapura': {'lat': 15.77, 'lon': 76.16},
        'Mundaragi': {'lat': 15.79, 'lon': 76.24},
        'Tavaragera': {'lat': 15.81, 'lon': 76.15},

        # Yelburga Taluk villages
        'Yelburga Town': {'lat': 15.62, 'lon': 75.89},
        'Hirebenchi': {'lat': 15.65, 'lon': 75.85},
        'Hoolageri': {'lat': 15.60, 'lon': 75.92},
        'Kempanahalli': {'lat': 15.67, 'lon': 75.87},
        'Komalapur': {'lat': 15.58, 'lon': 75.90},
        'Navalagi': {'lat': 15.64, 'lon': 75.93},
        'Ramasagara': {'lat': 15.61, 'lon': 75.86},
        'Sangapur': {'lat': 15.66, 'lon': 75.91},
        'Vajjal': {'lat': 15.63, 'lon': 75.88},
        'Yaragera': {'lat': 15.59, 'lon': 75.94}
    }

def create_map(df):
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    coords = area_coordinates()
    df = df.copy()
    
    # Use PSU Name for mapping coordinates
    if "PSU Name" in df.columns:
        df["lat"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lat"))
        df["lon"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lon"))
    else:
        df["lat"] = None
        df["lon"] = None

    map_df = df.dropna(subset=["lat", "lon"])
    
    if map_df.empty:
        fig.add_annotation(text="No location data available", showarrow=False)
        return fig

    # Add Study Area Boundary (from GeoJSON)
    try:
        with open("koppal_district.geojson", "r") as f:
            geojson_data = json.load(f)
            
        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson_data,
            locations=["koppal_district"],
            z=[1],
            colorscale=[[0, "rgba(52, 152, 219, 0.1)"], [1, "rgba(52, 152, 219, 0.1)"]],
            marker_line_width=2,
            marker_line_color="#2980b9",
            marker_opacity=0.5,
            showscale=False,
            name="Study Area Boundary",
            hoverinfo="name"
        ))
    except Exception as e:
        print(f"DEBUG: Could not load GeoJSON boundary: {e}")

    color_map = {
        "normal": "#27ae60",     # Darker green
        "mild": "#f1c40f",       # Yellow
        "moderate": "#e67e22",   # Orange
        "severe": "#c0392b"      # Darker red
    }

    # Add markers for each category
    for status, color in color_map.items():
        d = map_df[map_df["anemia_category"] == status]
        if not d.empty:
            # Create detailed hover text
            hover_text = []
            for _, row in d.iterrows():
                text = (f"<b>ID: {row.get('ID', 'N/A')}</b><br>" +
                       f"Name: {row.get('Name', 'N/A')}<br>" +
                       f"PSU: {row.get('PSU Name', 'N/A')}<br>" +
                       f"Area: {row.get('Area COde', 'N/A')}<br>" +
                       f"Group: {row.get('Benificiery', 'N/A')}<br>" +
                       f"Age: {row.get('Age', 'N/A')}<br>" +
                       f"HGB: {row.get('HGB', 'N/A')}<br>" +
                       f"Anemia: {status.capitalize()}")
                hover_text.append(text)

            fig.add_trace(go.Scattermapbox(
                lat=d["lat"],
                lon=d["lon"],
                mode="markers",
                marker=dict(size=12, color=color, opacity=0.8),
                name=status.capitalize(),
                text=hover_text,
                hovertemplate='%{text}<extra></extra>'
            ))

    # Add PSU Summary labels
    psu_summary = map_df.groupby("PSU Name").agg({
        "lat": "first",
        "lon": "first",
        "ID": "count"
    }).reset_index()

    # Beneficiary breakdown for each PSU
    benif_counts = map_df.groupby(["PSU Name", "Benificiery"]).size().unstack(fill_value=0)
    
    hover_texts = []
    for psu in psu_summary["PSU Name"]:
        if psu in benif_counts.index:
            counts = benif_counts.loc[psu]
            # Create a bulleted list for the tooltip
            breakdown = "<br>".join([f"• {k}: {v}" for k, v in counts.items() if v > 0])
            hover_texts.append(breakdown)
        else:
            hover_texts.append("No data")

    psu_summary["hover_breakdown"] = hover_texts

    fig.add_trace(go.Scattermapbox(
        lat=psu_summary["lat"],
        lon=psu_summary["lon"],
        mode="text",
        text=psu_summary["PSU Name"],
        textfont=dict(size=10, color="#2c3e50", family="Arial Black"),
        hovertemplate='<b>%{text}</b><br>Total Patients: %{customdata[0]}<br><br><b>Beneficiary Breakdown:</b><br>%{customdata[1]}<extra></extra>',
        customdata=psu_summary[["ID", "hover_breakdown"]].values,
        showlegend=False
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": 15.45, "lon": 76.2},
        mapbox_zoom=8.5,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.7)"
        )
    )
    return fig

# =========================
# LAYOUT
# =========================
app.layout = dbc.Container([
    dcc.Interval(id="interval", interval=30_000, n_intervals=0),
    dcc.Store(id="stored-data"),  # Cache for fetched data

    html.H2("Koppal District Anemia Study Dashboard", className="text-center mt-3 mb-1 dashboard-title"),
    html.Div("Real-time tracking across Area Codes and PSU Names", className="text-center mb-3 text-muted"),

    dbc.Card([
        dbc.CardBody([
            html.H5("Filters", className="card-title mb-3"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id="area-dropdown",
                    options=[],
                    multi=True,
                    placeholder="Area Code"
                ), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(
                    id="psu-dropdown",
                    options=[],
                    multi=True,
                    placeholder="PSU Name"
                ), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(
                    id="benificiery-dropdown",
                    options=[],
                    multi=True,
                    placeholder="Subject Group"
                ), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(
                    id="anemia-dropdown",
                    options=[{"label": x.capitalize(), "value": x} for x in anemia_list],
                    multi=True,
                    placeholder="Anemia Status"
                ), xs=12, sm=6, md=3, className="mb-2"),
            ], className="filter-row"),
        ])
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="total", className="text-primary"),
            html.P("Total Enrolled", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="normal-count", className="text-success"),
            html.P("Normal", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="moderate-count", className="text-info"),
            html.P("Moderate", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="severe-count", className="text-danger"),
            html.P("Severe", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="mild-count", className="text-warning"),
            html.P("Mild Anemia", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id="avg-hgb", className="text-secondary"),
            html.P("Average Hb", className="mb-0 text-truncate")
        ], className="summary-card text-center")), xs=6, md=2),
    ], className="mb-3 g-2"),

    html.H5("Interactive Patient Map - Koppal District", className="mb-2 mt-2"),
    html.Div(
        dcc.Loading(dcc.Graph(id="map", config={"responsive": True}), type="default"),
        style={"minHeight": "500px"}
    ),

    dbc.Row([
        dbc.Col(html.Div(
            dcc.Loading(dcc.Graph(id="benificiery-bar", config={"responsive": True}), type="default"),
            style={"minHeight": "350px"}
        ), xs=12, md=4),
        dbc.Col(html.Div(
            dcc.Loading(dcc.Graph(id="anemia-pie", config={"responsive": True}), type="default"),
            style={"minHeight": "350px"}
        ), xs=12, md=4),
        dbc.Col(html.Div(
            dcc.Loading(dcc.Graph(id="anemia-area-bar", config={"responsive": True}), type="default"),
            style={"minHeight": "350px"}
        ), xs=12, md=4),
    ], className="mb-3"),

    html.H5("Patient Tracking Details", className="mb-2 mt-2"),
    dcc.Loading(dash_table.DataTable(
        id="table",
        page_size=12,
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"padding": "8px", "textAlign": "left"},
        style_header={"fontWeight": "bold"},
        # EXPORT FEATURE ADDED (Commented out as requested)
        # export_format="xlsx",
        # export_headers="display",
        # merge_duplicate_headers=True,
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{anemia_category} = "Normal"',
                    'column_id': 'anemia_category'
                },
                'color': '#27ae60'
            },
            {
                'if': {
                    'filter_query': '{anemia_category} = "Mild"',
                    'column_id': 'anemia_category'
                },
                'color': '#d4ac0d'  # Darker gold for better visibility on white
            },
            {
                'if': {
                    'filter_query': '{anemia_category} = "Moderate"',
                    'column_id': 'anemia_category'
                },
                'color': '#e67e22'
            },
            {
                'if': {
                    'filter_query': '{anemia_category} = "Severe"',
                    'column_id': 'anemia_category'
                },
                'color': '#c0392b'
            },
        ]
    ), type="default")
], fluid=True)

# =========================
# CALLBACK - DATA FETCHING (Background)
# =========================
@app.callback(
    Output("stored-data", "data"),
    Input("interval", "n_intervals")
)
def refresh_data(_):
    df = load_data()
    return df.to_dict("records")

# =========================
# CALLBACK - UI FILTERING (Instant)
# =========================
@app.callback(
    [
        Output("total", "children"),
        Output("normal-count", "children"),
        Output("moderate-count", "children"),
        Output("severe-count", "children"),
        Output("mild-count", "children"),
        Output("avg-hgb", "children"),
        Output("map", "figure"),
        Output("benificiery-bar", "figure"),
        Output("anemia-pie", "figure"),
        Output("anemia-area-bar", "figure"),
        Output("table", "data"),
        Output("table", "columns"),
        Output("area-dropdown", "options"),
        Output("psu-dropdown", "options"),
        Output("benificiery-dropdown", "options"),
    ],
    [
        Input("stored-data", "data"),
        Input("psu-dropdown", "value"),
        Input("area-dropdown", "value"),
        Input("benificiery-dropdown", "value"),
        Input("anemia-dropdown", "value"),
        Input("interval", "n_intervals"),
    ]
)
def update_dashboard(stored_data, psu, area, benificiery, anemia, n_intervals):
    if not stored_data:
        return [0]*6 + [go.Figure()]*4 + [[], [], [], [], []]
        
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Full update if: Dropdown changed OR first load
    is_full_update = triggered_id in ["psu-dropdown", "area-dropdown", "benificiery-dropdown", "anemia-dropdown"] or \
                     triggered_id is None or \
                     (triggered_id == "stored-data" and n_intervals == 0)

    df_full = pd.DataFrame(stored_data)
    
    # Calculate options once for dropdowns
    area_opts = [{"label": x, "value": x} for x in sorted(df_full["Area COde"].dropna().unique())]
    psu_opts = [{"label": x, "value": x} for x in sorted(df_full["PSU Name"].dropna().unique())]
    benif_opts = [{"label": x, "value": x} for x in sorted(df_full["Benificiery"].dropna().unique())]

    # Filtering
    df = df_full.copy()
    if psu:
        df = df[df["PSU Name"].isin(psu)]
    if area:
        df = df[df["Area COde"].astype(str).isin(area)]
    if benificiery:
        df = df[df["Benificiery"].isin(benificiery)]
    if anemia:
        df = df[df["anemia_category"].isin(anemia)]

    # Summary cards
    total = len(df)
    normal = (df["anemia_category"] == "normal").sum()
    mild = (df["anemia_category"] == "mild").sum()
    moderate = (df["anemia_category"] == "moderate").sum()
    severe = (df["anemia_category"] == "severe").sum()
    avg_hgb = round(df["HGB"].mean(), 2) if not df.empty else 0

    # Color Mapping for consistency across all charts
    color_map = {
        "normal": "#27ae60",
        "mild": "#f1c40f",
        "moderate": "#e67e22",
        "severe": "#c0392b"
    }

    # Bar chart: Benificiery distribution
    benif_counts = df["Benificiery"].value_counts().sort_index()
    benif_bar = go.Figure([go.Bar(x=benif_counts.index, y=benif_counts.values, marker_color="#3498db")])
    benif_bar.update_layout(title="Subject Group Distribution", xaxis_title="Benificiery", yaxis_title="Count", margin=dict(t=40, b=40))

    # Pie chart: Anemia category
    anemia_counts = df["anemia_category"].value_counts()
    anemia_pie = go.Figure([go.Pie(
        labels=[l.capitalize() for l in anemia_counts.index], 
        values=anemia_counts.values, 
        hole=0.4,
        marker=dict(colors=[color_map.get(l, "#95a5a6") for l in anemia_counts.index])
    )])
    anemia_pie.update_layout(title="Anemia Category Distribution", margin=dict(t=40, b=40))

    # Stacked bar: Anemia by Area Code
    area_anemia = df.groupby(["Area COde", "anemia_category"]).size().unstack(fill_value=0)
    anemia_area_bar = go.Figure()
    # Ensure categories are plotted in a specific order: Normal -> Mild -> Moderate -> Severe
    for cat in ["normal", "mild", "moderate", "severe"]:
        if cat in area_anemia:
            anemia_area_bar.add_bar(
                name=cat.capitalize(), 
                x=area_anemia.index.astype(str), 
                y=area_anemia[cat],
                marker_color=color_map.get(cat)
            )
    anemia_area_bar.update_layout(barmode="stack", title="Anemia Status by Area Code", xaxis_title="Area Code", yaxis_title="Number of Patients", margin=dict(t=40, b=40))

    # Ensure specific column order for table
    table_order = [
        "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
        "Name", "Household Name", "Gender", "Benificiery", "DOB", "Age",
        "sample_status", "Sample Collected Date", "Collected By",
        "HGB", "anemia_category", "field_investigator", "Diet", "data_operator"
    ]
    
    # Filter only available columns from requested list
    available_cols = [c for c in table_order if c in df.columns]
    df_table = df[available_cols].copy()

    # Robust date formatting (DD/MM/YYYY)
    # Re-parsing is needed because dcc.Store serializes dates to ISO strings
    date_cols_to_format = ["enrollment_date", "DOB", "Sample Collected Date"]
    for col in date_cols_to_format:
        if col in df_table.columns:
            df_table[col] = pd.to_datetime(df_table[col], errors='coerce').dt.strftime('%d/%m/%Y')
            # Fill NaT with empty string for cleaner display
            df_table[col] = df_table[col].fillna("")

    # Apply Title Case to all string columns for universal appearance
    for col in df_table.columns:
        if df_table[col].dtype == 'object':
            df_table[col] = df_table[col].astype(str).str.title()

    # If not a full update, return no_update for all heavy visual components
    if not is_full_update:
        return (
            total,
            normal,
            moderate,
            severe,
            mild,
            avg_hgb,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            area_opts,
            psu_opts,
            benif_opts
        )

    # VISUALS
    map_fig = create_map(df)
    
    benif_counts = df["Benificiery"].value_counts().sort_index()
    benif_bar = go.Figure([go.Bar(x=benif_counts.index, y=benif_counts.values, marker_color="#3498db")])
    benif_bar.update_layout(title="Subject Group Distribution", margin=dict(t=40, b=40))

    anemia_counts = df["anemia_category"].value_counts()
    anemia_pie = go.Figure([go.Pie(
        labels=[l.capitalize() for l in anemia_counts.index], 
        values=anemia_counts.values, 
        hole=0.4,
        marker=dict(colors=[color_map.get(l, "#95a5a6") for l in anemia_counts.index])
    )])
    anemia_pie.update_layout(title="Anemia Category Distribution", margin=dict(t=40, b=40))

    area_anemia = df.groupby(["Area COde", "anemia_category"]).size().unstack(fill_value=0)
    anemia_area_bar = go.Figure()
    for cat in ["normal", "mild", "moderate", "severe"]:
        if cat in area_anemia:
            anemia_area_bar.add_bar(
                name=cat.capitalize(), x=area_anemia.index.astype(str), y=area_anemia[cat], marker_color=color_map.get(cat)
            )
    anemia_area_bar.update_layout(barmode="stack", title="Anemia Status by Area Code", margin=dict(t=40, b=40))

    return (
        total,
        normal,
        moderate,
        severe,
        mild,
        avg_hgb,
        map_fig,
        benif_bar,
        anemia_pie,
        anemia_area_bar,
        df_table.to_dict("records"),
        [{"name": c, "id": c} for c in available_cols],
        area_opts,
        psu_opts,
        benif_opts
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("Dashboard running at http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
