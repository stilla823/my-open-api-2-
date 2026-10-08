# Open API Service 2 - Click the map, get the weather
# A click on the map becomes latitude and longitude, which become an API request.

import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


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


st.set_page_config(page_title="Interactive Weather Map", layout="centered")
st.title("Interactive Weather Dashboard")
st.caption("Arts and Advanced Big Data | Open API, Service 2")

st.subheader("1. Pick a place (click the map)")
fmap = folium.Map(location=[36.5, 127.5], zoom_start=6)
result = st_folium(fmap, height=380, width=700)

clicked = (result or {}).get("last_clicked")
if not clicked:
    st.info("Click anywhere on the map to load the hourly temperature for that place.")
    st.stop()

lat, lon = round(clicked["lat"], 3), round(clicked["lng"], 3)
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
