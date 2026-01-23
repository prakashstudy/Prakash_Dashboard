# Koppal District Anemia Study Dashboard

An interactive real-time dashboard for tracking anemia study data across Area Codes and PSU Names in the Koppal District.

## Features
- **Real-time KPI Tracking**: Monitor total enrollment, hemoglobin levels, and anemia severity counts.
- **Interactive Map**: Visualize patient locations and village boundaries with detailed tooltips.
- **Dynamic Charts**: Distribution analysis by beneficiary group and anemia status.
- **Patient Tracking Table**: Filterable and sortable data table with conditional color-coding.

## Tech Stack
- **Dashboard Framework**: Plotly Dash
- **UI Components**: Dash Bootstrap Components
- **Data Processing**: Pandas
- **Visualization**: Plotly Graph Objects

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd anemia_dashboard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Dashboard

Start the local server:
```bash
python app2.py
```
The dashboard will be available at `http://localhost:8050`.

## Data Source
The dashboard fetches data from a Google Sheets backend via a Google Apps Script URL.

## Live Deployment (Hosting)
To make this dashboard accessible via a public URL:

1. **GitHub**: Push this repository to your GitHub account.
2. **Render**:
   - Create a free account on [Render.com](https://render.com).
   - Click **New +** and select **Web Service**.
   - Connect your GitHub repository.
   - Use the following settings:
     - **Runtime**: `Python`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app2:server`
3. Render will provide a live URL (e.g., `https://anemia-dashboard.onrender.com`).

