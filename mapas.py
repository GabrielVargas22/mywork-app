import folium

def mapa_hibrido(center, zoom=14):
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, zoom_control=True)

    # 1. Satélite base - sem API key
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satelite',
        overlay=False,
        control=False
    ).add_to(m)

    # 2. Estradas / Ruas por cima do satélite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Estradas',
        overlay=True,
        control=False,
        opacity=1
    ).add_to(m)

    # 3. Nomes de ruas, bairros, cidades por cima de tudo - bem nítido
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Nomes',
        overlay=True,
        control=False,
        opacity=1
    ).add_to(m)

    return m

def adicionar_pino(m, lat, lng, cliente_id, nome, cor="blue", tem_amanha=False):
    if cor == "green":
        cor_base = "#22c55e"
    else:
        cor_base = "#2563eb"

    if tem_amanha:
        html = f"""
        <div style="position:relative; width:28px; height:28px;">
            <div style="width:24px; height:24px; background:{cor_base}; border:3px solid white; border-radius:50%; box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>
            <div style="position:absolute; top:-2px; right:0px; width:12px; height:12px; background:#facc15; border:2px solid white; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>
        </div>
        """
    else:
        html = f"""
        <div style="width:24px; height:24px; background:{cor_base}; border:3px solid white; border-radius:50%; box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>
        """

    popup_html = f"""
    <div style="min-width:160px; font-family:sans-serif;">
        <b style="font-size:13px;">{nome}</b><br>
        <a href="?cliente_id={cliente_id}" target="_self" style="display:inline-block; margin-top:8px; background:#2563eb; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">👁️ Ver cliente</a>
    </div>
    """

    folium.Marker(
        location=[lat, lng],
        icon=folium.DivIcon(html=html, icon_size=(28,28), icon_anchor=(14,14)),
        popup=folium.Popup(popup_html, max_width=200)
    ).add_to(m)