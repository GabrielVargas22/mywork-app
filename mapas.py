import folium
from folium.plugins import LocateControl

def mapa_hibrido(center, zoom=14):
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, zoom_control=True)

    # 1. Só ruas - Google limpo (igual Waze)
    ruas = folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='🗺️ Ruas',
        overlay=False,
        control=True
    )
    ruas.add_to(m)

    # 2. Híbrido - Satélite + ruas por cima
    hibrido = folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='🛰️ Híbrido',
        overlay=False,
        control=True
    )
    hibrido.add_to(m)

    # Botão de trocar Ruas / Híbrido no canto superior direito
    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    # Botão de localização no canto inferior direito
    LocateControl(
        position='bottomright',
        strings={'title': 'Ir para minha localização'},
        flyTo=True,
        keepCurrentZoomLevel=True,
        showPopup=False,
        locateOptions={'enableHighAccuracy': True}
    ).add_to(m)

    return m

def mapa_satelite(center, zoom=16):
    # Usado na criação do cliente
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, zoom_control=True)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='🗺️ Ruas',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='🛰️ Híbrido',
        overlay=False,
        control=True
    ).add_to(m)

    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    LocateControl(position='bottomright', flyTo=True, keepCurrentZoomLevel=True).add_to(m)
    return m

def adicionar_pino(m, lat, lng, cliente_id, nome, cor="blue", tem_amanha=False):
    cor_base = "#22c55e" if cor == "green" else "#2563eb"

    if tem_amanha:
        html = f"""
        <div style="position:relative; width:28px; height:28px;">
            <div style="width:24px; height:24px; background:{cor_base}; border:3px solid white; border-radius:50%; box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>
            <div style="position:absolute; top:-2px; right:0px; width:12px; height:12px; background:#facc15; border:2px solid white; border-radius:50%;"></div>
        </div>
        """
    else:
        html = f"""<div style="width:24px; height:24px; background:{cor_base}; border:3px solid white; border-radius:50%; box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>"""

    # Popup com seu botão + ID escondido para o Streamlit capturar
    popup_html = f"""
    <div style="min-width:160px; font-family:sans-serif;">
        <b style="font-size:13px;">{nome}</b><br>
        <span style="font-size:11px; color:#666;">ID: {cliente_id}</span><br>
        <a href="?cliente_id={cliente_id}" target="_self" style="display:inline-block; margin-top:8px; background:#2563eb; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">👁️ Ver cliente</a>
    </div>
    """
    folium.Marker(
        location=[lat, lng],
        tooltip=str(cliente_id),  # ID no tooltip pra detectar clique
        icon=folium.DivIcon(html=html, icon_size=(28,28), icon_anchor=(14,14)),
        popup=folium.Popup(popup_html, max_width=200)
    ).add_to(m)
