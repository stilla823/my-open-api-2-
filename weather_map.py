# Open API Service 2 - Search a city or click the map, get the weather
# A search or a click becomes latitude and longitude, which become an API request.

import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@st.cache_data(ttl=600)  # remember answers for 10 minutes
def get_hourly_temperature(lat, lon):
    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m",
            "forecast_days": 2,
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    hourly = resp.json()["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "Temperature (°C)": hourly["temperature_2m"],
    })
    return df.set_index("time")


@st.cache_data(ttl=3600)  # city names rarely change
def search_city(name):
    resp = requests.get(
        GEOCODING_URL,
        params={"name": name, "count": 5, "language": "en", "format": "json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


st.set_page_config(page_title="Interactive Weather Map", layout="centered")
st.title("Interactive Weather Dashboard")
st.caption("Arts and Advanced Big Data | Open API, Service 2")

# Remember the chosen point between reruns (default: Jeju)
if "pt" not in st.session_state:
    st.session_state.pt = (33.303, 126.738)
    st.session_state.last_click = None
    st.session_state.last_search = None

st.subheader("1. Pick a place (search a city or click the map)")

query = st.text_input("Search a city", placeholder="e.g. Busan, Tokyo, Paris")
if query:
    try:
        results = search_city(query)
    except requests.RequestException:
        st.error("City search failed. Please try again.")
        results = []
    if results:
        labels = [
            f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}"
            for r in results
        ]
        choice = st.selectbox("Select a match", labels)
        sel = results[labels.index(choice)]
        new_pt = (sel["latitude"], sel["longitude"])
        if st.session_state.last_search != new_pt:  # apply only when the choice changes
            st.session_state.pt = new_pt
            st.session_state.last_search = new_pt
    else:
        st.warning("No city found. Try a different spelling.")

fmap = folium.Map(location=st.session_state.pt, zoom_start=7)
folium.Marker(st.session_state.pt).add_to(fmap)
result = st_folium(fmap, height=380, width=700)

clicked = (result or {}).get("last_clicked")
if clicked and clicked != st.session_state.last_click:  # apply only new clicks
    st.session_state.last_click = clicked
    st.session_state.pt = (clicked["lat"], clicked["lng"])
    st.rerun()

lat, lon = round(st.session_state.pt[0], 3), round(st.session_state.pt[1], 3)
st.subheader(f"2. Hourly temperature at {lat}, {lon}")

try:
    df = get_hourly_temperature(lat, lon)
except requests.RequestException:
    st.error("Could not reach the weather service right now. Please try again in a minute.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Now (first hour)", f"{df.iloc[0, 0]:.1f} °C")
col2.metric("Highest", f"{df.iloc[:, 0].max():.1f} °C")
col3.metric("Lowest", f"{df.iloc[:, 0].min():.1f} °C")
st.line_chart(df)

st.caption("Data: Open-Meteo.com (free for non-commercial use).")