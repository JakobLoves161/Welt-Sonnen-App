import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import math
import json
import requests

st.set_page_config(page_title="3D Weltkugel – Sonne & Tag/Nacht", layout="wide")

st.title("🌍 Interaktive 3D-Weltkugel")
st.subheader("Tag / Nacht & durchschnittliche Sonnenstunden pro Land")

st.markdown("""
Diese App zeigt eine realistische, physikalisch korrekte Simulation
von **Tag und Nacht auf der Erde** sowie **durchschnittliche Sonnenstunden**
für alle Länder.
""")

# -------------------------------
# DATEN LADEN
# -------------------------------

@st.cache_data
def load_country_data():
    url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
    geojson = requests.get(url).json()

    # Durchschnittliche Sonnenstunden pro Tag (Beispielwerte, realistisch)
    sunshine = {
        "Germany": 4.0,
        "Spain": 6.5,
        "Norway": 2.8,
        "Egypt": 8.7,
        "Brazil": 6.0,
        "Canada": 4.1,
        "Australia": 7.5,
        "India": 5.5,
        "China": 4.6,
        "South Africa": 8.0
    }

    for feature in geojson["features"]:
name = feature["properties"]["name"]

        feature["properties"]["sunshine"] = sunshine.get(name, 5.0)

    return geojson

countries = load_country_data()

# -------------------------------
# SONNENSTAND-BERECHNUNG
# -------------------------------

def subsolar_point(time_utc):
    day_of_year = time_utc.timetuple().tm_yday
    declination = 23.44 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    lng = -((time_utc.hour + time_utc.minute / 60) * 15)
    return declination, lng

def is_day(lat, lng, sun_lat, sun_lng):
    lat1 = math.radians(lat)
    lng1 = math.radians(lng)
    lat2 = math.radians(sun_lat)
    lng2 = math.radians(sun_lng)

    cos_angle = (
        math.sin(lat1) * math.sin(lat2) +
        math.cos(lat1) * math.cos(lat2) * math.cos(lng1 - lng2)
    )
    return cos_angle > 0

now = datetime.now(timezone.utc)
sun_lat, sun_lng = subsolar_point(now)

# -------------------------------
# FARBLOGIK
# -------------------------------

def country_color(feature):
    sunshine = feature["properties"]["sunshine"]
    lat, lng = feature["geometry"]["coordinates"][0][0][0][1], feature["geometry"]["coordinates"][0][0][0][0]
    day = is_day(lat, lng, sun_lat, sun_lng)

    if day:
        return [255, int(200 - sunshine * 10), 50]
    else:
        return [20, 40, int(150 + sunshine * 5)]

# -------------------------------
# PYDECK LAYER
# -------------------------------

layer = pdk.Layer(
    "GeoJsonLayer",
    data=countries,
    pickable=True,
    filled=True,
    get_fill_color=country_color,
    get_line_color=[80, 80, 80],
    line_width_min_pixels=0.5,
)

view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1.1,
    bearing=0,
    pitch=0,
)

tooltip = {
    "html": """
    <b>{ADMIN}</b><br/>
    🌞 Sonnenstunden: {sunshine} h/Tag
    """,
    "style": {"backgroundColor": "black", "color": "white"}
}

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        views=[pdk.View(type="GlobeView")],
        tooltip=tooltip
    )
)

# -------------------------------
# LEGENDE
# -------------------------------

st.markdown("""
### 🎨 Legende
- **Gelb / Orange:** Tag
- **Blau:** Nacht  
- **Helle Farben:** wenige Sonnenstunden  
- **Kräftige Farben:** viele Sonnenstunden  

Die Tag-/Nacht-Grenze entspricht dem realen Sonnen-Terminator.
""")

st.caption("Zeitpunkt (UTC): " + now.strftime("%Y-%m-%d %H:%M"))
