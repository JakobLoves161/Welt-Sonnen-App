import streamlit as st
import pydeck as pdk
import numpy as np
from datetime import datetime, timezone
import math
import requests

st.set_page_config(page_title="3D Weltkugel – Sonne & Tag/Nacht", layout="wide")

st.title("🌍 Interaktive 3D-Weltkugel")
st.subheader("Tag / Nacht & durchschnittliche Sonnenstunden pro Land")

st.markdown("""
Diese App zeigt eine Simulation von **Tag und Nacht auf der Erde**
sowie **durchschnittliche Sonnenstunden** pro Land.
""")

# -------------------------------
# DATEN LADEN
# -------------------------------

@st.cache_data
def load_country_data():
    url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
    geojson = requests.get(url).json()

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
# SONNENSTAND BERECHNUNG
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

# -------------------------------
# ROBUSTE MITTELPUNKT-BERECHNUNG
# -------------------------------

def get_center(feature):
    coords = feature["geometry"]["coordinates"]
    lats = []
    lngs = []

    def extract(c):
        if isinstance(c, (int, float)):
            return

        if (
            isinstance(c, list)
            and len(c) == 2
            and isinstance(c[0], (int, float))
            and isinstance(c[1], (int, float))
        ):
            lngs.append(c[0])
            lats.append(c[1])
            return

        if isinstance(c, list):
            for item in c:
                extract(item)

    extract(coords)

    if len(lats) == 0:
        return 0, 0

    return np.mean(lats), np.mean(lngs)

# -------------------------------
# AKTUELLE SONNENPOSITION
# -------------------------------

now = datetime.now(timezone.utc)
sun_lat, sun_lng = subsolar_point(now)

# -------------------------------
# FARBEN BERECHNEN
# -------------------------------

for feature in countries["features"]:
    sunshine = feature["properties"]["sunshine"]
    lat, lng = get_center(feature)
    day = is_day(lat, lng, sun_lat, sun_lng)

    if day:
        color = [255, int(200 - sunshine * 10), 50]
    else:
        color = [20, 40, int(150 + sunshine * 5)]

    feature["properties"]["color"] = color

# -------------------------------
# PYDECK LAYER
# -------------------------------

layer = pdk.Layer(
    "GeoJsonLayer",
    data=countries,
    pickable=True,
    filled=True,
    get_fill_color="properties.color",
    get_line_color=[80, 80, 80],
    line_width_min_pixels=0.5,
)

view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1.1,
)

tooltip = {
    "html": """
    <b>{name}</b><br/>
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
- **Kräftige Farben:** viele Sonnenstunden  
""")

st.caption("Zeitpunkt (UTC): " + now.strftime("%Y-%m-%d %H:%M"))
