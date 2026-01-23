import requests
import json

url = "https://raw.githubusercontent.com/udit-001/india-maps-data/refs/heads/main/geojson/states/karnataka.geojson"

try:
    print(f"Fetching data from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    koppal_feature = None
    for feature in data['features']:
        # Check various property names for 'Koppal'
        props = feature.get('properties', {})
        if any(str(val).lower() == 'koppal' for val in props.values()):
            koppal_feature = feature
            break
            
    if koppal_feature:
        # Create a FeatureCollection with just Koppal
        output = {
            "type": "FeatureCollection",
            "features": [koppal_feature]
        }
        with open("koppal_district_official.geojson", "w") as f:
            json.dump(output, f, indent=2)
        print("Successfully extracted Koppal boundary to koppal_district_official.geojson")
    else:
        print("Could not find Koppal district in the GeoJSON data.")
        
except Exception as e:
    print(f"Error: {e}")
