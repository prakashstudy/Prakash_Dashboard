import dash
from dash import dcc, html, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import json
import re
from datetime import datetime


# =========================
# DASH INIT
# =========================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# =========================
# LOAD DATA (URL or CSV)
# =========================
DATA_SOURCE_URL = "https://script.google.com/macros/s/AKfycbxfqwdEiWRaSUpfSQoE5V_WBbCT74vM3Wj9F1rNM354EieRMYsMWtGnU_sRegLua50Ycg/exec" 

BENEFICIARY_MAP = {
    2: "Pregnant Women",
    3: "Children 5-9 Months",
    4: "Children Aged 5-9 Years  (60 Months)",
    5: "Adolescent Girls 10-19 Years",
    6: "Adolescent Boys 10-19 Years",
    7: "Women Of Reproductive Age"
}

def parse_age(age_val):
    if pd.isna(age_val) or age_val == "":
        return None
    
    # Handle already numeric values
    if isinstance(age_val, (int, float)):
        return age_val if age_val < 150 else None
        
    # Handle datetime objects if pandas parsed them accidentally
    if hasattr(age_val, 'year') and hasattr(age_val, 'month'):
        # If it's a date, we probably can't infer age without a reference date, 
        # but let's assume it's not an age.
        return None

    age_str = str(age_val).lower().strip()
    
    # 1. If it's just a simple number string (e.g. "21" or "21.5")
    clean_num = age_str.replace('yr', '').replace('yrs', '').replace('yr.', '').strip()
    try:
        val = float(clean_num)
        return val if val < 150 else None
    except:
        pass

    # 2. Rule out strings that look like full dates (e.g., "2021-06-01" or "21/06/19")
    if re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', age_str):
        return None

    years = 0.0
    months = 0.0
    
    # 3. Explicit search for suffixes (Highest priority)
    y_match = re.search(r'(\d+(\.\d+)?)\s*(y|yr|year)', age_str)
    m_match = re.search(r'(\d+(\.\d+)?)\s*(m|mo|month)', age_str)
    
    if y_match or m_match:
        if y_match: years = float(y_match.group(1))
        if m_match: months = float(m_match.group(1))
        # If years looks like a birth year, disregard it
        if years > 1900: years = 0
    else:
        # 4. Fallback: No suffixes, look for "Number Number"
        nums = re.findall(r'(\d+(\.\d+)?)', age_str)
        if len(nums) >= 1:
            val1 = float(nums[0][0])
            if val1 > 1900: # First number is a year
                if len(nums) >= 2: years = float(nums[1][0])
                if len(nums) >= 3: months = float(nums[2][0])
            else:
                years = val1
                if len(nums) >= 2: months = float(nums[1][0])
            
    res = round(years + (months / 12), 2)
    return res if 0 < res < 150 else None

def classify_anemia_who(hgb, age, gender, beneficiary):
    """
    Classify anemia based on WHO guidelines.
    
    Parameters:
    - hgb: Hemoglobin level in g/dL (REQUIRED)
    - age: Age in years (Optional if beneficiary type is specific)
    - gender: Gender (Male/Female)
    - beneficiary: Beneficiary category
    
    Returns: 'normal', 'mild', 'moderate', 'severe', or 'incomplete' if data is insufficient
    """
    # Handle missing HGB - REQUIRED
    if pd.isna(hgb) or hgb is None:
        return "incomplete"
    
    # Convert HGB to float
    try:
        hgb = float(hgb)
    except:
        return "incomplete"

    # Handle Age (Optional, but convert if present)
    try:
        if age is not None and not pd.isna(age) and str(age).strip() != "":
            age = float(age)
        else:
            age = None
    except:
        age = None
    
    # Normalize inputs
    gender_str = str(gender).lower().strip() if not pd.isna(gender) else ""
    beneficiary_str = str(beneficiary).lower().strip() if not pd.isna(beneficiary) else ""
    
    # Determine classification based on beneficiary type OR age
    
    # Pregnant Women
    if "pregnant" in beneficiary_str:
        if hgb >= 11.0:
            return "normal"
        elif hgb >= 10.0:
            return "mild"
        elif hgb >= 7.0:
            return "moderate"
        else:
            return "severe"
    
    # Children 5-9 Months (6-59 months WHO category)
    elif "5-9 months" in beneficiary_str or "children 5-9 months" in beneficiary_str:
        if hgb >= 11.0:
            return "normal"
        elif hgb >= 10.0:
            return "mild"
        elif hgb >= 7.0:
            return "moderate"
        else:
            return "severe"
    
    # Children Aged 5-9 Years (60 Months)
    elif "5-9 years" in beneficiary_str or "60 months" in beneficiary_str:
        if hgb >= 11.5:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Adolescent Girls 10-19 Years
    elif "adolescent girls" in beneficiary_str or ("adolescent" in beneficiary_str and "female" in gender_str):
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Adolescent Boys 10-19 Years
    elif "adolescent boys" in beneficiary_str or ("adolescent" in beneficiary_str and "male" in gender_str):
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Women Of Reproductive Age (non-pregnant)
    elif "women of reproductive age" in beneficiary_str or "reproductive age" in beneficiary_str:
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Fallback: Use age and gender if beneficiary type doesn't match
    elif age is not None:
        # Children under 5 years
        if age < 5:
            if hgb >= 11.0:
                return "normal"
            elif hgb >= 10.0:
                return "mild"
            elif hgb >= 7.0:
                return "moderate"
            else:
                return "severe"
        
        # Children 5-11 years
        elif age < 12:
            if hgb >= 11.5:
                return "normal"
            elif hgb >= 11.0:
                return "mild"
            elif hgb >= 8.0:
                return "moderate"
            else:
                return "severe"
        
        # Adolescents and Adults (12+ years)
        else:
            # Female thresholds
            if "female" in gender_str or "f" == gender_str:
                if hgb >= 12.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"
            # Male thresholds
            elif "male" in gender_str or "m" == gender_str:
                if hgb >= 13.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"
            # Unknown gender - use female thresholds (more conservative)
            else:
                if hgb >= 12.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"

    # If we can't determine (missing/unclear beneficiary AND missing age), return incomplete
    return "incomplete"



def load_data():
    """
    Fetches data from Google Apps Script. 
    Returns: (df, status_message, is_error)
    """
    status_msg = "Live"
    is_error = False
    try:
        import requests
        # Increased timeout slightly for reliability on slower connections
        r = requests.get(DATA_SOURCE_URL, timeout=10)
        r.raise_for_status()
        
        try:
            data_json = r.json()
            # Debug: Print a snippet of the JSON to the console
            print("DEBUG: Fetched JSON Data (snippet):", str(data_json)[:500] + "...")
            
            if isinstance(data_json, dict) and 'data' in data_json:
                df = pd.DataFrame(data_json['data'])
            else:
                df = pd.DataFrame(data_json)
        except:
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            
        if df.empty:
            return pd.DataFrame(), "No Data in Script", True

        df.columns = df.columns.str.strip()
        
        required_cols = [
            "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
            "Name", "Household Name", "Gender", "Benificiery", "DOB", "Age",
            "sample_status", "Sample Collected Date", "Collected By",
            "HGB", "anemia_category", "field_investigator", "Diet", "data_operator"
        ]
        df = df[[c for c in required_cols if c in df.columns]]

        date_cols = ["DATE_F", "enrollment_date", "DOB", "Sample Collected Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        if "HGB" in df.columns:
            df["HGB"] = pd.to_numeric(df["HGB"], errors="coerce")
        
        # Parse Age with special logic
        if "Age" in df.columns:
            df["Age"] = df["Age"].apply(parse_age)
        else:
            df["Age"] = None
            
        # Cross-calculate Age from DOB if missing
        if "DOB" in df.columns:
            # Use enrollment_date as reference, fallback to today
            ref_date = df["enrollment_date"].fillna(pd.Timestamp.now())
            
            # Mask for missing Ages where DOB exists
            mask = df["Age"].isna() & df["DOB"].notna()
            
            if mask.any():
                # Ensure compatibility by removing timezones (tz-naive)
                try:
                    ref_dt_naive = pd.to_datetime(ref_date[mask]).dt.tz_localize(None)
                    dob_dt_naive = pd.to_datetime(df.loc[mask, "DOB"]).dt.tz_localize(None)
                    diff = (ref_dt_naive - dob_dt_naive).dt.days
                    calculated_ages = (diff / 365.25).round(2)
                    # Only apply if result is sane
                    df.loc[mask, "Age"] = calculated_ages.apply(lambda x: x if 0 <= x < 150 else None)
                except Exception as age_err:
                    print(f"DEBUG: Age calculation fallback failed: {age_err}")
        
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

        # Apply WHO-based automatic anemia classification
        if "HGB" in df.columns:
            df["anemia_category"] = df.apply(
                lambda row: classify_anemia_who(
                    row.get("HGB"),
                    row.get("Age"),
                    row.get("Gender"),
                    row.get("Benificiery")
                ),
                axis=1
            )
        else:
            df["anemia_category"] = None

        # FILTER: Keep rows where either Age OR Beneficiary is present
        # Check for valid Age (not None/NaN)
        has_age = df["Age"].notna()
        
        # Check for valid Beneficiary (not None/NaN/empty/"Nan")
        # Since we converted to string title case earlier, check against "Nan" and "None" strings
        has_beneficiary = (
            df["Benificiery"].notna() & 
            (df["Benificiery"] != "") & 
            (df["Benificiery"].str.lower() != "nan") & 
            (df["Benificiery"].str.lower() != "none")
        )
        
        df = df[has_age | has_beneficiary]

        return df, "Live", False
        
    except requests.exceptions.ConnectionError:
        return pd.DataFrame(), "Connection Error (Check DNS/Network)", True
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "Request Timeout", True
    except Exception as e:
        return pd.DataFrame(), f"Script Error: {str(e)}", True

psu_list = []
area_list = []
anemia_list = ["normal", "mild", "moderate", "severe", "incomplete"]

def area_coordinates():
    return {
        'Kunikera': {'lat': 15.2832, 'lon': 76.2142},
        'Ojanahalli': {'lat': 15.3856, 'lon': 76.1472},
        'Bannikoppa': {'lat': 15.3877, 'lon': 75.9420},
        'Tadkal': {'lat': 15.3507, 'lon': 76.1554},
        'Hulegudda': {'lat': 15.6235, 'lon': 76.1146},
        'Konasagar': {'lat': 15.6916, 'lon': 76.1030},
        'Kawalbodur': {'lat': 15.8267, 'lon': 76.1744},
        'Balutagi': {'lat': 15.8627, 'lon': 76.2653},
        'HireGonnagar': {'lat': 15.8096, 'lon': 75.9535},
        'Anegundi': {'lat': 15.3507, 'lon': 76.4925},
        'Kilarhatti': {'lat': 15.8107, 'lon': 76.3994},
        'Challur': {'lat': 15.6000, 'lon': 76.5833},
        'Marlanahalli': {'lat': 15.5740, 'lon': 76.6499},
        'Gouripur': {'lat': 15.6188, 'lon': 76.3550},
        'Hatti': {'lat': 15.2117, 'lon': 75.9350},
        'Komlapur': {'lat': 15.350708, 'lon': 76.155434},
        'Chikwankal Kunta': {'lat': 15.5828, 'lon': 76.1852},
        'Hire Wankal Kunta': {'lat': 15.5972, 'lon': 76.1931},
        'Talkere': {'lat': 15.5471, 'lon': 76.1555},
        'Ningalbandi': {'lat': 15.6881, 'lon': 76.2235},
        'Badimnhal': {'lat': 15.7197, 'lon': 76.1432},
        'Venkatapur': {'lat': 15.8239, 'lon': 76.2081},
        'Garjanhal': {'lat': 15.7062, 'lon': 76.0681},
        'Teggihal': {'lat': 15.6836, 'lon': 76.0441},
        'Mallapur': {'lat': 15.7481, 'lon': 76.2361},
        'Rampur': {'lat': 15.3934, 'lon': 76.1415},
        'Hagedal': {'lat': 15.6562, 'lon': 76.0315},
        'Basrihal': {'lat': 15.6031, 'lon': 75.9521},
        'Chikka Madinal': {'lat': 15.6621, 'lon': 75.9876},
        'Wadganhal': {'lat': 15.6214, 'lon': 75.9562},
        'Hirebommanahal': {'lat': 15.6421, 'lon': 76.0214},
        'Hiresulikeri': {'lat': 15.6791, 'lon': 76.1721},
        'Jinnapur': {'lat': 15.5342, 'lon': 75.9731},
        'Belgatti': {'lat': 15.4851, 'lon': 75.8921},
        'Kawaloor': {'lat': 15.3512, 'lon': 75.9921},
        'Kesor': {'lat': 15.4021, 'lon': 76.5467},
        'Gangawati (CMC+OG) WARD No- 0005': {'lat': 15.4350, 'lon': 76.5330},
        'Gangawati (CMC+OG) WARD No- 0009': {'lat': 15.4280, 'lon': 76.5250},
        'Gangawati (CMC+OG) WARD No- 0015': {'lat': 15.4330, 'lon': 76.5350},
        'Koppal (CMC) WARD No-0008': {'lat': 15.3530, 'lon': 76.1580},
        'Koppal (CMC) WARD No-0021': {'lat': 15.3480, 'lon': 76.1520},
        'Koppal (CMC) WARD No-0001': {'lat': 15.3550, 'lon': 76.1500}
    }

def create_map(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False)
        return fig
    coords = area_coordinates()
    df = df.copy()
    if "PSU Name" in df.columns:
        df["lat"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lat"))
        df["lon"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lon"))
    else:
        df["lat"] = None
        df["lon"] = None
    map_df = df.dropna(subset=["lat", "lon"])
    
    # Calculate counts per PSU and Beneficiary
    psu_counts = map_df.groupby("PSU Name").size().to_dict() if not map_df.empty else {}
    benif_breakdown = map_df.groupby(["PSU Name", "Benificiery"]).size().unstack(fill_value=0).to_dict('index') if not map_df.empty else {}
    
    # All defined villages with their count (default 0)
    village_status = []
    for v_name, v_coord in coords.items():
        count = psu_counts.get(v_name, 0)
        breakdown_dict = benif_breakdown.get(v_name, {})
        # Create a formatted string for the tooltip
        breakdown_str = "<br>".join([f"• {k}: {v}" for k, v in breakdown_dict.items() if v > 0])
        if not breakdown_str:
            breakdown_str = "No data"
            
        status = "No Data" if count == 0 else ("In Progress" if count < 48 else "Complete")
        color = "#922b21" if count == 0 else ("#e67e22" if count < 48 else "#27ae60")
        village_status.append({
            "name": v_name, "lat": v_coord["lat"], "lon": v_coord["lon"],
            "count": count, "status": status, "color": color, "breakdown": breakdown_str
        })
    status_df = pd.DataFrame(village_status)

    # Always try to draw the boundary
    try:
        with open("koppal_district_official.geojson", "r") as f:
            geojson_data = json.load(f)
        fig.add_trace(go.Choroplethmap(
            geojson=geojson_data, locations=["Koppal"], featureidkey="properties.district",
            z=[1], colorscale=[[0, "rgba(52, 152, 219, 0.1)"], [1, "rgba(52, 152, 219, 0.1)"]],
            marker_line_width=2, marker_line_color="#2980b9", marker_opacity=0.5,
            showscale=False, name="Study Area Boundary", hoverinfo="name"
        ))
    except Exception as e:
        print(f"DEBUG: Could not load GeoJSON boundary: {e}")

    # Add Progress-based Markers (Three Groups)
    categories = [
        {"name": "No Data Collected", "color": "#922b21", "filter": status_df["count"] == 0},
        {"name": "In Progress (1-47)", "color": "#e67e22", "filter": (status_df["count"] > 0) & (status_df["count"] < 48)},
        {"name": "Complete (48+ Samples)", "color": "#27ae60", "filter": status_df["count"] >= 48}
    ]
    
    for cat in categories:
        d_cat = status_df[cat["filter"]]
        if not d_cat.empty:
            fig.add_trace(go.Scattermap(
                lat=d_cat["lat"], lon=d_cat["lon"], mode="markers+text",
                marker=dict(size=14, color=cat["color"], opacity=0.9),
                name=cat["name"],
                text=d_cat["name"],
                textfont=dict(size=10, color="#2c3e50", family="Arial"),
                textposition="top center",
                hovertemplate='<b>%{text}</b><br>Total Samples: %{customdata[0]}<br>Status: %{customdata[1]}<br><br><b>Beneficiary Breakdown:</b><br>%{customdata[2]}<extra></extra>',
                customdata=d_cat[["count", "status", "breakdown"]].values
            ))
    
    fig.update_layout(
        map_style="open-street-map", map_center={"lat": 15.6, "lon": 76.15},
        map_zoom=8.3, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255, 255, 255, 0.7)")
    )
    return fig

# Custom styles for the layout
CARD_STYLE = {"height": "400px"}
MAP_CARD_STYLE = {"height": "650px"}

app.layout = dbc.Container([
    dcc.Interval(id="interval", interval=30_000, n_intervals=0),
    dcc.Store(id="stored-data"),
    
    # Header Section
    html.Div([
        html.H2("Prakash-Koppal District Study Dashboard", className="text-center mt-4 mb-2 dashboard-title"),
        html.Div([
            html.Span("Real-time Health Surveillance | Koppal, Karnataka", className="text-muted")
        ], className="text-center mb-4"),
    ]),

    # Filter Section
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id="area-dropdown", options=[], multi=True, placeholder="Filter Area Code"), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(id="psu-dropdown", options=[], multi=True, placeholder="Filter PSU Name"), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(id="benificiery-dropdown", options=[], multi=True, placeholder="Benificiery"), xs=12, sm=6, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(id="anemia-dropdown", options=[{"label": x.capitalize(), "value": x} for x in anemia_list], multi=True, placeholder="Anemia Status"), xs=12, sm=6, md=3, className="mb-2"),
            ], className="filter-row g-2"),
        ], className="p-3")
    ], className="mb-4 glass-card"),

    # KPI Row (Responsive Grid)
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="total"), html.P("Enrolled")], className="summary-card kpi-total text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="normal-count"), html.P("Normal")], className="summary-card kpi-normal text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="mild-count"), html.P("Mild")], className="summary-card kpi-mild text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="moderate-count"), html.P("Moderate")], className="summary-card kpi-moderate text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="severe-count"), html.P("Severe")], className="summary-card kpi-severe text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="prevalence-val"), html.P("Prevalence (%)")], className="summary-card kpi-prevalence text-center")), xs=6, sm=4, md=True),
        dbc.Col(dbc.Card(dbc.CardBody([html.H4(id="avg-hgb"), html.P("Avg Hb (g/dL)")], className="summary-card kpi-hgb text-center")), xs=6, sm=4, md=True),
    ], className="mb-4 g-2 justify-content-center"),

    # Main Row (Map + Side Charts)
    dbc.Row([
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H5("Spatial Distribution - Case Status", className="mb-3 text-muted text-center", style={"fontSize": "14px", "fontWeight": "600"}),
                dcc.Loading(dcc.Graph(id="map", config={"responsive": True}, style={"height": "580px", "minHeight": "400px"}), type="default"), 
            ], className="p-2"), className="glass-card", style={"minHeight": "650px"}),
        ], xs=12, md=8),
        
        dbc.Col([
            dbc.Card(dbc.CardBody([
                dcc.Loading(dcc.Graph(id="anemia-pie", config={"responsive": True}), type="default"),
            ], className="p-2"), className="mb-3 glass-card", style={"height": "315px"}),
            
            dbc.Card(dbc.CardBody([
                dcc.Loading(dcc.Graph(id="benificiery-bar", config={"responsive": True}), type="default"), 
            ], className="p-2"), className="glass-card", style={"height": "315px"}),
        ], xs=12, md=4),
    ], className="mb-4 g-3"),

    # Secondary Analysis (Full Width Comparison)
    dbc.Row([
        dbc.Col([
            dbc.Card(dbc.CardBody([
                dcc.Loading(dcc.Graph(id="anemia-area-bar", config={"responsive": True}), type="default"),
            ], className="p-3"), className="glass-card", style={"height": "450px"}),
        ], width=12),
    ], className="mb-4 g-3"),

    # Table Section
    html.Div([
        html.H5("Patient Tracking & Detailed Records", className="mb-3 mt-4 text-muted"),
        dcc.Loading(dash_table.DataTable(
            id="table", page_size=15, filter_action="native", sort_action="native",
            style_table={"overflowX": "auto"}, style_cell={"padding": "12px", "textAlign": "left", "fontFamily": "Inter"},
            style_header={"fontWeight": "700", "backgroundColor": "#e0f2fe", "color": "#0369a1"},
            style_data_conditional=[
                {'if': {'filter_query': '{anemia_category} = "Normal"'}, 'backgroundColor': '#dcfce7', 'color': '#166534'},
                {'if': {'filter_query': '{anemia_category} = "Mild"'}, 'backgroundColor': '#fef9c3', 'color': '#854d0e'},
                {'if': {'filter_query': '{anemia_category} = "Moderate"'}, 'backgroundColor': '#fee2e2', 'color': '#991b1b'},
                {'if': {'filter_query': '{anemia_category} = "Severe"'}, 'backgroundColor': '#fecaca', 'color': '#7f1d1d'},
                {'if': {'filter_query': '{anemia_category} = "Incomplete"'}, 'backgroundColor': '#f3f4f6', 'color': '#64748b'},
            ]
        ), type="default")
    ], className="mb-5")
], fluid=True, className="px-2 px-md-4")

@app.callback(Output("stored-data", "data"), Input("interval", "n_intervals"))
def refresh_data(_):
    df, msg, is_err = load_data()
    return {
        "records": df.to_dict("records"),
        "status": msg,
        "is_error": is_err,
        "last_updated": datetime.now().strftime("%H:%M:%S")
    }

@app.callback(
    [
        Output("total", "children"), Output("normal-count", "children"),
        Output("moderate-count", "children"), Output("severe-count", "children"),
        Output("mild-count", "children"), Output("avg-hgb", "children"),
        Output("prevalence-val", "children"),
        Output("map", "figure"), Output("benificiery-bar", "figure"),
        Output("anemia-pie", "figure"), Output("anemia-area-bar", "figure"),
        Output("table", "data"), Output("table", "columns"),
        Output("area-dropdown", "options"), Output("psu-dropdown", "options"),
        Output("benificiery-dropdown", "options"), Output("anemia-dropdown", "options"),
        Output("psu-dropdown", "value"),
    ],
    [
        Input("stored-data", "data"), Input("psu-dropdown", "value"),
        Input("area-dropdown", "value"), Input("benificiery-dropdown", "value"),
        Input("anemia-dropdown", "value"), Input("interval", "n_intervals"),
        Input("map", "clickData"),
    ]
)
def update_dashboard(stored_dict, psu, area, benificiery, anemia, n_intervals, clickData):
    if not stored_dict or "records" not in stored_dict:
        return [0]*7 + [go.Figure()]*4 + [[], [], [], [], [], [], None]
    
    records = stored_dict["records"]
    status_msg = stored_dict["status"]
    is_error = stored_dict["is_error"]
    last_upd = stored_dict.get("last_updated", "")

    if not records and is_error:
        return [0]*7 + [go.Figure()]*4 + [[], [], [], [], [], [], None]

    df_full = pd.DataFrame(records)
    
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Handle Map Clicks
    if triggered_id == "map" and clickData:
        village_clicked = clickData["points"][0].get("text")
        if village_clicked:
            if village_clicked in df_full["PSU Name"].values:
                psu = [village_clicked]

    driver_triggers = ["stored-data", "interval"]
    # We will always update the dashboard components to ensure they stay in sync with filters
    is_full_update = True 

    # Dynamic Options (Cascading Filters)
    # 1. PSU options: Filtered by Area, Benificiery, Anemia
    df_psu = df_full.copy()
    if area: df_psu = df_psu[df_psu["Area COde"].astype(str).isin(area)]
    if benificiery: df_psu = df_psu[df_psu["Benificiery"].isin(benificiery)]
    if anemia: df_psu = df_psu[df_psu["anemia_category"].isin(anemia)]
    psu_opts = [{"label": x, "value": x} for x in sorted(df_psu["PSU Name"].dropna().unique())]

    # Clean up PSU selection if not in new options
    if psu:
        valid_psus = [o["value"] for o in psu_opts]
        psu = [p for p in psu if p in valid_psus]

    # 2. Area options: Filtered by PSU, Benificiery, Anemia
    df_area = df_full.copy()
    if psu: df_area = df_area[df_area["PSU Name"].isin(psu)]
    if benificiery: df_area = df_area[df_area["Benificiery"].isin(benificiery)]
    if anemia: df_area = df_area[df_area["anemia_category"].isin(anemia)]
    area_opts = [{"label": x, "value": x} for x in sorted(df_area["Area COde"].dropna().unique())]

    # 3. Benificiery options: Filtered by Area, PSU, Anemia
    df_benif = df_full.copy()
    if area: df_benif = df_benif[df_benif["Area COde"].astype(str).isin(area)]
    if psu: df_benif = df_benif[df_benif["PSU Name"].isin(psu)]
    if anemia: df_benif = df_benif[df_benif["anemia_category"].isin(anemia)]
    benif_opts = [{"label": x, "value": x} for x in sorted(df_benif["Benificiery"].dropna().unique())]

    # 4. Anemia options: Filtered by Area, PSU, Benificiery (Logic added for dynamic cascading)
    df_anemia_opts = df_full.copy()
    if area: df_anemia_opts = df_anemia_opts[df_anemia_opts["Area COde"].astype(str).isin(area)]
    if psu: df_anemia_opts = df_anemia_opts[df_anemia_opts["PSU Name"].isin(psu)]
    if benificiery: df_anemia_opts = df_anemia_opts[df_anemia_opts["Benificiery"].isin(benificiery)]
    # Normalize anemia categories to capitalize for label
    anemia_opts_raw = sorted(df_anemia_opts["anemia_category"].dropna().unique())
    anemia_opts = [{"label": x.capitalize(), "value": x} for x in anemia_opts_raw]

    # Apply all final filters to the main df for stats/charts
    df = df_full.copy()
    if psu: df = df[df["PSU Name"].isin(psu)]
    if area: df = df[df["Area COde"].astype(str).isin(area)]
    if benificiery: df = df[df["Benificiery"].isin(benificiery)]
    if anemia: 
        # Ensure case-insensitive matching for anemia category
        df = df[df["anemia_category"].str.lower().isin([x.lower() for x in anemia])]

    total = len(df)
    normal = (df["anemia_category"] == "normal").sum()
    mild = (df["anemia_category"] == "mild").sum()
    moderate = (df["anemia_category"] == "moderate").sum()
    severe = (df["anemia_category"] == "severe").sum()
    avg_hgb = round(df["HGB"].mean(), 2) if not df.empty else 0
    prevalence = round(((mild + moderate + severe) / total * 100), 1) if total > 0 else 0
    prevalence_str = f"{prevalence}%"

    # Formatting KPIs with percentages (Percentage not bold)
    def get_kpi_str(count, total):
        pct = round((count / total * 100), 1) if total > 0 else 0
        return [
            str(count), 
            html.Span(f" ({pct}%)", style={"fontWeight": "400", "fontSize": "0.85em", "color": "#64748b", "marginLeft": "2px"})
        ]

    normal_kpi = get_kpi_str(normal, total)
    mild_kpi = get_kpi_str(mild, total)
    moderate_kpi = get_kpi_str(moderate, total)
    severe_kpi = get_kpi_str(severe, total)

    color_map = {"normal": "#27ae60", "mild": "#f1c40f", "moderate": "#e67e22", "severe": "#c0392b", "incomplete": "#95a5a6"}

    table_order = [
        "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
        "Name", "Household Name", "Gender", "Benificiery", "Age",
        "sample_status", "Sample Collected Date", "Collected By",
        "HGB", "anemia_category", "field_investigator", "Diet", "data_operator"
    ]
    available_cols = [c for c in table_order if c in df.columns]
    df_table = df[available_cols].copy()
    date_cols_to_format = ["enrollment_date", "Sample Collected Date"]
    for col in date_cols_to_format:
        if col in df_table.columns:
            df_table[col] = pd.to_datetime(df_table[col], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")

    for col in df_table.columns:
        if df_table[col].dtype == 'object':
            df_table[col] = df_table[col].astype(str).str.title()

    # Removed is_full_update check to ensure dashboard always reflects current filter state

    map_fig = create_map(df)
    
    # Age-wise breakdown for Benificiery Hover
    def get_age_bucket(age):
        if pd.isna(age): return "Unknown"
        if age < 1: return f"{int(round(age*12))} Months"
        if age < 5: return "1-4 Years"
        if age <=9: return "5-9 Years"
        if age < 18: return "10-17 Years"
        if age < 30: return "18-29 Years"
        if age < 40: return "30-39 Years"
        if age < 50: return "40-49 Years"
        return "50+ Years"

    benif_counts = df["Benificiery"].value_counts().sort_index()
    age_hover_data = []
    for b_group in benif_counts.index:
        sub = df[df["Benificiery"] == b_group]
        buckets = sub["Age"].apply(get_age_bucket).value_counts()
        # Sort buckets logically if possible, or just by index
        b_str = "<br>".join([f"• {b}: {c}" for b, c in buckets.items()])
        age_hover_data.append(b_str)

    benif_bar = go.Figure([go.Bar(
        x=benif_counts.index, 
        y=benif_counts.values, 
        customdata=age_hover_data,
        hovertemplate="<b>%{x}</b><br>Total: %{y}<br><br><b>Age Breakdown:</b><br>%{customdata}<extra></extra>",
        marker_color="#3b82f6",
        marker_line_width=0,
        opacity=0.8
    )])
    benif_bar.update_layout(
        title=dict(text="Benificiery Breakdown", font=dict(size=14, color="#64748b", family="Inter"), x=0.5, y=0.92),
        margin=dict(t=60, b=120, l=40, r=20),
        xaxis=dict(tickangle=-45, automargin=True, title=None, showgrid=False),
        yaxis=dict(title=None, automargin=True, showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=315
    )

    anemia_counts = df["anemia_category"].value_counts()
    colors = [color_map.get(l, "#95a5a6") for l in anemia_counts.index]
    anemia_pie = go.Figure([go.Pie(
        labels=[l.capitalize() for l in anemia_counts.index], 
        values=anemia_counts.values, 
        hole=0.6, 
        marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
        textinfo='percent',
        hoverinfo='label+value'
    )])
    anemia_pie.update_layout(
        title=dict(text="Case Distribution", font=dict(size=14, color="#64748b", family="Inter"), x=0.5, y=0.92),
        margin=dict(t=60, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=315
    )

    area_anemia = df.groupby(["Area COde", "anemia_category"]).size().unstack(fill_value=0)
    
    # Detailed hover info (Villages and their counts per Area and Category)
    hover_info = {}
    if not df.empty:
        for (area, cat), sub_df in df.groupby(["Area COde", "anemia_category"]):
            v_counts = sub_df["PSU Name"].value_counts()
            v_str = "<br>".join([f"{v}: {count}" for v, count in v_counts.items()])
            hover_info[(str(area), cat)] = v_str

    anemia_area_bar = go.Figure()
    for cat in ["normal", "mild", "moderate", "severe", "incomplete"]:
        if cat in area_anemia:
            custom_hover = [hover_info.get((str(area), cat), "No data") for area in area_anemia.index]
            
            anemia_area_bar.add_bar(
                name=cat.capitalize(), 
                x=area_anemia.index.astype(str), 
                y=area_anemia[cat], 
                customdata=custom_hover,
                hovertemplate="<b>Status: " + cat.capitalize() + "</b><br>%{customdata}<extra></extra>",
                marker_color=color_map.get(cat), 
                opacity=0.85
            )
    anemia_area_bar.update_layout(
        barmode="stack", 
        title=dict(text="Anemia Status Comparison by Area Code", font=dict(size=16, color="#1e293b", family="Inter"), x=0.01),
        margin=dict(t=60, b=60, l=40, r=20),
        xaxis=dict(title="Area Code", automargin=True, showgrid=False),
        yaxis=dict(title="Count", automargin=True, showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )

    return (total, normal_kpi, moderate_kpi, severe_kpi, mild_kpi, avg_hgb, prevalence_str, map_fig, benif_bar, anemia_pie, anemia_area_bar, df_table.to_dict("records"), [{"name": "HGB (g/dL)" if c == "HGB" else c, "id": c} for c in available_cols], area_opts, psu_opts, benif_opts, anemia_opts, psu)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
