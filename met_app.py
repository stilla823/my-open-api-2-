# 1. Map + city search
st.header("1. Pick a place (search or click the map)")

@st.cache_data(ttl=3600)
def search_city(name):
    r = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={
        "name": name, "count": 5, "language": "en", "format": "json"}, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

if "pt" not in st.session_state:
    st.session_state.pt = (33.303, 126.738)
    st.session_state.last_click = None
    st.session_state.last_search = None

query = st.text_input("Search a city", placeholder="e.g. Busan, Tokyo, Paris")
if query:
    try:
        results = search_city(query)
    except requests.RequestException:
        st.error("City search failed. Please try again.")
        results = []
    if results:
        labels = [f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}" for r in results]
        choice = st.selectbox("Select a match", labels)
        sel = results[labels.index(choice)]
        new_pt = (sel["latitude"], sel["longitude"])
        if st.session_state.last_search != new_pt:   # only apply when the choice changes
            st.session_state.pt = new_pt
            st.session_state.last_search = new_pt
    else:
        st.warning("No city found. Try a different spelling.")

m = folium.Map(location=st.session_state.pt, zoom_start=8)
folium.Marker(st.session_state.pt).add_to(m)
out = st_folium(m, height=400, use_container_width=True)

click = out.get("last_clicked") if out else None
if click and click != st.session_state.last_click:   # only apply new clicks
    st.session_state.last_click = click
    st.session_state.pt = (click["lat"], click["lng"])
    st.rerun()