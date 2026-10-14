import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date, datetime, timedelta
from database import init_db, get_clientes, get_cliente_dict, salvar_cliente, atualizar_cliente, atualizar_local, deletar_cliente
from mapas import mapa_hibrido, adicionar_pino
from metas import init_metas, get_config, set_config, registrar_visita, deletar_visita_hoje, get_visitas_hoje, get_visitas_semana, ja_visitou_hoje, get_valor_visita_hoje
from agenda import init_agenda, add_compromisso, get_compromissos, deletar_compromisso, hora_para_minutos, update_horario
import json
import sqlite3

init_db()
init_metas()
init_agenda()
st.set_page_config(page_title="MyWork", layout="wide", initial_sidebar_state="collapsed")

if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'menu'
if 'last_drag' not in st.session_state:
    st.session_state['last_drag'] = ""
if 'data_agenda_sel' not in st.session_state:
    st.session_state['data_agenda_sel'] = date.today()
if 'zoom_agenda' not in st.session_state:
    st.session_state['zoom_agenda'] = 0
if 'filtro_historico' not in st.session_state:
    st.session_state['filtro_historico'] = 'recentes'
if 'editando_cliente' not in st.session_state:
    st.session_state['editando_cliente'] = False
if 'pagina_anterior' not in st.session_state:
    st.session_state['pagina_anterior'] = 'mapa'

# Voltar via link - limpa cliente e volta
if st.query_params.get("voltar") == "1":
    if 'cliente_id' in st.session_state:
        del st.session_state['cliente_id']
    st.session_state['editando_cliente'] = False
    # se tinha pagina anterior, volta pra ela, se não vai pro mapa
    if 'pagina_anterior' in st.session_state:
        st.session_state['pagina'] = st.session_state['pagina_anterior']
    st.query_params.clear()
    st.rerun()

if st.query_params.get("pagina") in ["menu","clientes","agenda","mapa","historico"]:
    # se está saindo do detalhe do cliente pra outra pagina via barra, limpa cliente_id
    if 'cliente_id' in st.session_state:
        del st.session_state['cliente_id']
    st.session_state['editando_cliente'] = False
    st.session_state['pagina'] = st.query_params.get("pagina")
    st.query_params.clear()

if st.query_params.get("cliente_id"):
    try:
        st.session_state['pagina_anterior'] = st.session_state.get('pagina', 'mapa')
        st.session_state['cliente_id'] = int(st.query_params.get("cliente_id"))
        st.session_state['editando_cliente'] = False
        st.query_params.clear()
        st.rerun()
    except:
        pass

st.markdown("""
<style>
.stApp { background-color: #121212!important; }
#MainMenu, footer, header {visibility: hidden; display:none;}
.block-container {padding-top: 0px!important; padding-bottom:150px!important; margin-top:0px!important;}
div[data-testid="stVerticalBlock"] { gap: 6px!important; }
div[data-testid="stVerticalBlockBorderWrapper"] { margin-top:2px!important; margin-bottom:6px!important; padding-top:8px!important; padding-bottom:8px!important;}
div[data-testid="stContainer"] { padding-top:8px!important; padding-bottom:8px!important; }
input[aria-label="drag"] { display: none!important; }
div[data-testid="stTextInput"]:has(input[aria-label="drag"]) { display: none!important; height: 0!important; margin: 0!important; padding: 0!important;}
div[data-testid="stButton"] button[kind="primary"] { background-color: #00acc1!important; border-color: #00acc1!important; color: white!important; }
div[data-testid="stButton"] button[kind="secondary"] { background-color: #1f1f1f!important; border:1px solid #2c2c2c!important; color:#9a9a9a!important; }
.linha-div { height:1px; background:#2c2c2c; margin:10px 0; }
div[data-baseweb="select"] > div { background:#1f1f1f!important; border-color:#2c2c2c!important; color:white!important;}
.bloco-visitas { background:#1e1e1e; border:1px solid #2c2c2c; border-radius:14px; max-height:160px; overflow-y:auto; padding:6px; }
.item-visita { padding:8px 10px; border-bottom:1px solid #2a2a2a; color:white; font-size:13px; display:flex; justify-content:space-between; }
.item-visita:last-child { border-bottom:none; }
div[data-testid="stDialog"] { background-color: #2a2a2a!important; }
div[data-testid="stDialog"] > div { background-color: #2a2a2a!important; }
[data-testid="stDialog"] div[data-testid="stVerticalBlock"] { background-color: #2a2a2a!important; }
div[role="dialog"] { background-color: #2a2a2a!important; border:1px solid #3a3a3a!important; }
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] p, div[data-testid="stDialog"] label, div[data-testid="stDialog"] span { color: #e0e0e0!important; }
div[data-testid="stDialog"] input, div[data-testid="stDialog"] textarea, div[data-testid="stDialog"] div[data-baseweb="select"] > div { background-color: #1f1f1f!important; border-color: #3a3a3a!important; color: white!important; }
div[data-testid="stDialog"] hr { border-color: #3a3a3a!important; }
.btn-voltar { display:block; text-align:center; background:#1f1f1f; border:1px solid #2c2c2c; color:#e0e0e0!important; padding:10px; border-radius:10px; text-decoration:none; font-weight:700; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<h1 style="margin:0; padding:0; margin-top:-4px; margin-bottom:4px; color:white; font-weight:800; font-size:26px; line-height:30px;">MyWork</h1>""", unsafe_allow_html=True)

st.text_input("drag", key="drag_result", label_visibility="collapsed")
drag_valor_atual = st.session_state.get('drag_result', '')
if drag_valor_atual and drag_valor_atual!= st.session_state.get('last_drag',''):
    st.session_state['last_drag'] = drag_valor_atual
    if drag_valor_atual.startswith("NAV|"):
        st.session_state['pagina'] = drag_valor_atual.split("|")[1]
        st.rerun()
    elif drag_valor_atual.startswith("DATE|"):
        try:
            st.session_state['data_agenda_sel'] = date.fromisoformat(drag_valor_atual.split("|")[1])
            st.rerun()
        except: pass
    elif drag_valor_atual.startswith("ZOOM|"):
        try: st.session_state['zoom_agenda'] = int(drag_valor_atual.split("|")[1])
        except: pass
    elif drag_valor_atual.startswith("NEW|"):
        _, hora_nova = drag_valor_atual.split("|")
        st.session_state['hora_clicada'] = hora_nova
        st.session_state['show_novo_comp'] = True
        st.rerun()
    elif drag_valor_atual.startswith("DETAIL|"):
        _, id_str = drag_valor_atual.split("|")
        st.session_state['comp_detalhe_id'] = int(id_str)
        st.session_state['show_detalhe_comp'] = True
        st.rerun()
    elif "|" in drag_valor_atual:
        try:
            id_mover, novo_h = drag_valor_atual.split("|")
            if id_mover.isdigit():
                update_horario(int(id_mover), novo_h)
                st.toast(f"Movido para {novo_h}!")
        except: pass

@st.dialog("Novo Compromisso", width="large")
def modal_novo_compromisso(hora_pre, data_str):
    st.markdown(f"**📅 {data_str} | ⏰ {hora_pre}**")
    tipo = st.selectbox("Tipo", ["visita", "viagem", "evento", "outros", "almoco"], format_func=lambda x: {"visita":"👤 Visita Cliente","viagem":"🚗 Viagem","evento":"🎉 Evento","outros":"📝 Outros","almoco":"🍽 Almoço"}[x], key="tipo_modal_dialog")
    col_h1, col_h2 = st.columns(2)
    with col_h1: hora_ini = st.time_input("Horário início", value=datetime.strptime(hora_pre, "%H:%M").time(), key="hora_ini_dialog")
    with col_h2: duracao = st.selectbox("Duração", [15,30,45,60,90,120,180], format_func=lambda x: f"{x} min" if x<60 else f"{x//60}h" if x%60==0 else f"{x//60}h {x%60}min", key="dur_dialog")
    cliente_id_sel = None
    titulo_final = ""
    if tipo == "visita":
        todos_cli = get_clientes()
        busca_cli = st.text_input("🔍 Buscar cliente", key="busca_dialog")
        if busca_cli and not todos_cli.empty: todos_cli = todos_cli[todos_cli['nome'].str.contains(busca_cli, case=False, na=False)]
        if not todos_cli.empty:
            opcoes = {f"{row['nome']} - {row['endereco'] or ''}": int(row['id']) for _, row in todos_cli.iterrows()}
            sel = st.selectbox("Selecione o cliente", list(opcoes.keys()), key="sel_cli_dialog")
            cliente_id_sel = opcoes[sel]
            titulo_final = sel.split(" - ")[0]
    elif tipo == "viagem": titulo_final = "Viagem"
    elif tipo == "almoco": titulo_final = "Almoço"
    else: titulo_final = st.text_input("Título", key="tit_dialog")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if tipo == "visita" and not cliente_id_sel: st.error("Selecione um cliente")
            elif not titulo_final: st.error("Digite um título")
            else:
                add_compromisso(data_str, hora_ini.strftime("%H:%M"), duracao, tipo, cliente_id_sel, titulo_final)
                st.session_state['show_novo_comp'] = False
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state['show_novo_comp'] = False
            st.rerun()

@st.dialog("Novo Cliente", width="large")
def modal_novo_cliente():
    st.markdown("### ➕ Novo Cliente")
    if 'novo_cli_lat' not in st.session_state:
        st.session_state['novo_cli_lat'] = None
        st.session_state['novo_cli_lng'] = None
    nome = st.text_input("Nome *", placeholder="Ex: Mercado do João", key="fab_nome")
    endereco = st.text_input("Endereço", placeholder="Rua, número, bairro", key="fab_end")
    whatsapp = st.text_input("WhatsApp", placeholder="(51) 99999-9999", key="fab_whats")
    pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro", "PIX", "Cartão", "Fiado", "Outro"], key="fab_pag")
    obs = st.text_area("Observações", placeholder="Ex: Entregar segunda de manhã...", key="fab_obs")
    st.divider()
    st.markdown("#### 📍 Localização no mapa")
    st.caption("Clique no mapa para marcar ou use o botão 🎯 no mapa para ir até você.")
    from mapas import mapa_satelite
    m_novo = mapa_satelite([-29.942, -50.99], 16)
    if st.session_state['novo_cli_lat'] and st.session_state['novo_cli_lng']:
        adicionar_pino(m_novo, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'], 0, "Novo cliente", "green")
        st.success(f"📍 Local marcado: {st.session_state['novo_cli_lat']:.6f}, {st.session_state['novo_cli_lng']:.6f}")
    map_data = st_folium(m_novo, height=350, use_container_width=True, key="mapa_novo_cli")
    if map_data and map_data['last_clicked']:
        st.session_state['novo_cli_lat'] = map_data['last_clicked']['lat']
        st.session_state['novo_cli_lng'] = map_data['last_clicked']['lng']
        st.rerun()
    if st.session_state['novo_cli_lat']:
        if st.button("❌ Remover localização", use_container_width=True):
            st.session_state['novo_cli_lat'] = None
            st.session_state['novo_cli_lng'] = None
            st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar Cliente", type="primary", use_container_width=True):
            if not nome:
                st.error("Digite o nome")
            else:
                try:
                    novo_id = None
                    try:
                        novo_id = salvar_cliente(nome, endereco, whatsapp, pagamento, obs, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'])
                    except TypeError:
                        novo_id = salvar_cliente(nome, endereco, whatsapp, pagamento, obs)
                        if st.session_state['novo_cli_lat'] and st.session_state['novo_cli_lng']:
                            if novo_id:
                                try: atualizar_local(novo_id, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'])
                                except: pass
                            else:
                                df_temp = get_clientes()
                                if not df_temp.empty:
                                    ultimo_id = int(df_temp.sort_values('id').iloc[-1]['id'])
                                    try: atualizar_local(ultimo_id, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'])
                                    except: pass
                    st.session_state['novo_cli_lat'] = None
                    st.session_state['novo_cli_lng'] = None
                    st.session_state['show_novo_cliente'] = False
                    st.toast("Cliente salvo!", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state['novo_cli_lat'] = None
            st.session_state['novo_cli_lng'] = None
            st.session_state['show_novo_cliente'] = False
            st.rerun()

@st.dialog("Detalhe do Compromisso", width="large")
def modal_detalhe_compromisso(comp_id):
    data_sel_base = st.session_state.get('data_agenda_sel', date.today())
    if isinstance(data_sel_base, str):
        try: data_sel_base = date.fromisoformat(data_sel_base)
        except: data_sel_base = date.today()
    comp_encontrado = None
    for offset in range(-3, 4):
        d = (data_sel_base + timedelta(days=offset)).isoformat()
        for c in get_compromissos(d):
            if c['id'] == comp_id:
                comp_encontrado = c
                comp_encontrado['data'] = d
                break
        if comp_encontrado: break
    if not comp_encontrado:
        st.error("Compromisso não encontrado")
        if st.button("Fechar"):
            st.session_state['show_detalhe_comp'] = False
            st.rerun()
        return
    tipo_label = {"visita":"👤 Visita","viagem":"🚗 Viagem","evento":"🎉 Evento","outros":"📝 Outros","almoco":"🍽 Almoço"}.get(comp_encontrado['tipo'], comp_encontrado['tipo'])
    fim_min = hora_para_minutos(comp_encontrado['hora_inicio']) + comp_encontrado['duracao']
    fim_hora = f"{fim_min//60:02d}:{fim_min%60:02d}"
    st.markdown(f"### {tipo_label} - {comp_encontrado['titulo']}")
    st.markdown(f"**📅 {comp_encontrado['data']} | ⏰ {comp_encontrado['hora_inicio']} - {fim_hora} ({comp_encontrado['duracao']} min)**")
    if comp_encontrado['tipo'] == 'visita' and comp_encontrado['cliente_id']:
        cli = get_cliente_dict(comp_encontrado['cliente_id'])
        if cli:
            st.divider()
            st.markdown(f"**👤 Cliente:** {cli['nome']}")
            st.caption(f"📍 {cli['endereco'] or 'Sem endereço'}")
            if cli['whatsapp']: st.caption(f"📱 {cli['whatsapp']}")
            obs_val = cli.get('observacoes') or cli.get('obs') or ""
            if obs_val: st.info(f"📝 {obs_val}")
            if st.button("👁 Ver dados completos do cliente", type="primary", use_container_width=True):
                st.session_state['cliente_id'] = cli['id']
                st.session_state['editando_cliente'] = False
                st.session_state['show_detalhe_comp'] = False
                st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑 Excluir compromisso", use_container_width=True):
            deletar_compromisso(comp_id)
            st.session_state['show_detalhe_comp'] = False
            st.toast("Compromisso excluído")
            st.rerun()
    with c2:
        if st.button("Fechar", use_container_width=True):
            st.session_state['show_detalhe_comp'] = False
            st.rerun()

@st.dialog("Configurar Metas", width="large")
def modal_config_metas():
    st.markdown("### ⚙ Configurar Metas")
    meta_diaria_c = int(get_config('meta_diaria_clientes'))
    meta_diaria_v = float(get_config('meta_diaria_vendas'))
    nd_c = st.number_input("Meta diária - visitas", value=meta_diaria_c, min_value=1, step=1)
    nd_v = st.number_input("Meta diária - vendas R$", value=meta_diaria_v, min_value=0.0, step=50.0)
    st.divider()
    st.info(f"Semanal será: **{nd_c*5} visitas** e **R$ {nd_v*5:.2f}**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            set_config('meta_diaria_clientes', nd_c)
            set_config('meta_diaria_vendas', nd_v)
            set_config('meta_semanal_clientes', nd_c*5)
            set_config('meta_semanal_vendas', nd_v*5)
            st.toast("Metas salvas!")
            st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

def get_historico_dados():
    try:
        conn = sqlite3.connect('banco.db')
        c = conn.cursor()
        c.execute("SELECT cliente_id, COUNT(*) as qtd, MAX(data) as ultima, SUM(CASE WHEN valor IS NULL THEN 0 ELSE valor END) as total FROM visitas GROUP BY cliente_id")
        dados = {row[0]: {'qtd': row[1], 'ultima': row[2], 'total': row[3]} for row in c.fetchall()}
        c.execute("SELECT cliente_id, data, valor FROM visitas ORDER BY data DESC LIMIT 20")
        recentes = c.fetchall()
        conn.close()
        return dados, recentes
    except:
        return {}, []

def get_ultimas_visitas_lista():
    try:
        conn = sqlite3.connect('banco.db')
        c = conn.cursor()
        c.execute("SELECT v.cliente_id, v.data, v.valor, c2.nome FROM visitas v LEFT JOIN clientes c2 ON v.cliente_id = c2.id ORDER BY v.data DESC LIMIT 15")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

# =====================
# CONTEÚDO PRINCIPAL - SEM st.stop() PARA MANTER A BARRA SEMPRE VISÍVEL
# =====================

# 1. Se tem cliente_id, mostra detalhe do cliente
if 'cliente_id' in st.session_state and st.session_state['cliente_id'] is not None:
    cli = get_cliente_dict(st.session_state['cliente_id'])
    if cli:
        col_voltar, col_edit = st.columns([1,1])
        with col_voltar:
            st.markdown('<a href="?voltar=1" target="_self" class="btn-voltar">⬅ Voltar</a>', unsafe_allow_html=True)
        with col_edit:
            if not st.session_state['editando_cliente']:
                if st.button("✏ Editar", use_container_width=True, key="btn_editar_cliente"):
                    st.session_state['editando_cliente'] = True
                    st.rerun()

        if not st.session_state['editando_cliente']:
            st.subheader(f"{cli['nome']}")
            with st.container(border=True):
                whats_raw = cli['whatsapp'] or ""
                whats_limpo = "".join(filter(str.isdigit, whats_raw))
                if len(whats_limpo) >= 10:
                    numero_wa = whats_limpo
                    if not numero_wa.startswith("55"):
                        numero_wa = "55" + numero_wa[-11:]
                    st.markdown(f"**📱 WhatsApp:** [{whats_raw}](https://wa.me/{numero_wa})")
                else:
                    st.markdown(f"**📱 WhatsApp:** {whats_raw or 'Não informado'}")

                end = cli['endereco'] or ""
                if cli['lat'] and cli['lng']:
                    maps_link = f"https://www.google.com/maps?q={cli['lat']},{cli['lng']}"
                    st.markdown(f"**📍 Endereço:** [{end or 'Ver no mapa'}]({maps_link})")
                elif end:
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={end.replace(' ', '+')}"
                    st.markdown(f"**📍 Endereço:** [{end}]({maps_link})")
                else:
                    st.markdown("**📍 Endereço:** Não informado")

                st.markdown(f"**💳 Pagamento:** {cli.get('forma_pagamento') or cli.get('pagamento') or 'Não informado'}")
                obs_val = cli.get('observacoes') or cli.get('obs') or ""
                if obs_val:
                    st.info(f"📝 {obs_val}")

                st.divider()
                st.markdown("#### 💰 Venda / Visita")
                valor = st.number_input("Valor da venda R$", min_value=0.0, step=10.0, key="valor_venda_readonly")
                if ja_visitou_hoje(cli['id']):
                    st.success(f"✅ Já visitado hoje - R$ {get_valor_visita_hoje(cli['id']):.2f}")
                    if st.button("❌ Remover visita de hoje", use_container_width=True, key=f"rem_{cli['id']}"):
                        deletar_visita_hoje(cli['id']); st.rerun()
                else:
                    if st.button("✅ Registrar visita", type="primary", use_container_width=True, key=f"reg_{cli['id']}"):
                        registrar_visita(cli['id'], valor if valor>0 else None)
                        st.success("Visita registrada!"); st.rerun()

                st.divider()
                m = mapa_hibrido([cli['lat'] or -29.942, cli['lng'] or -50.99], 16)
                if cli['lat'] and cli['lng']: adicionar_pino(m, cli['lat'], cli['lng'], cli['id'], cli['nome'], "blue")
                st_folium(m, height=350, use_container_width=True, key=f"mapa_cli_{cli['id']}")
        else:
            st.subheader(f"Editando: {cli['nome']}")
            with st.form("edit"):
                nome = st.text_input("Nome", value=cli['nome'])
                endereco = st.text_input("Endereço", value=cli['endereco'] or "")
                whatsapp = st.text_input("WhatsApp", value=cli['whatsapp'] or "")
                pagamento = st.selectbox("Pagamento", ["Dinheiro", "PIX", "Cartão", "Fiado", "Outro"], index=0)
                obs_val = cli.get('observacoes') or cli.get('obs') or ""
                obs = st.text_area("Obs", value=obs_val)
                col_s, col_d = st.columns(2)
                with col_s:
                    if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                        atualizar_cliente(cli['id'], nome, endereco, whatsapp, pagamento, obs)
                        st.session_state['editando_cliente'] = False
                        st.success("Salvo!"); st.rerun()
                with col_d:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state['editando_cliente'] = False
                        st.rerun()
            with st.container(border=True):
                st.markdown("#### 📍 Alterar localização")
                m = mapa_hibrido([cli['lat'] or -29.942, cli['lng'] or -50.99], 16)
                if cli['lat'] and cli['lng']: adicionar_pino(m, cli['lat'], cli['lng'], cli['id'], cli['nome'], "blue")
                map_data = st_folium(m, height=400, use_container_width=True, key=f"mapa_cli_edit_{cli['id']}")
                if map_data and map_data['last_clicked']:
                    if st.button("📍 Salvar esta localização", use_container_width=True):
                        atualizar_local(cli['id'], map_data['last_clicked']['lat'], map_data['last_clicked']['lng'])
                        st.success("Local salvo!"); st.rerun()
            if st.button("🗑 Excluir cliente", use_container_width=True):
                deletar_cliente(cli['id'])
                if 'cliente_id' in st.session_state:
                    del st.session_state['cliente_id']
                st.session_state['editando_cliente'] = False
                st.rerun()

# 2. Se NÃO tem cliente_id, mostra a pagina normal
else:
    if st.query_params.get("novo_cliente") == "1":
        st.session_state['show_novo_cliente'] = True
        st.query_params.clear(); st.rerun()
    if st.query_params.get("novo_comp") == "1":
        st.session_state['hora_clicada'] = "08:00"
        st.session_state['show_novo_comp'] = True
        st.query_params.clear(); st.rerun()
    if st.session_state.get('show_detalhe_comp'):
        modal_detalhe_compromisso(st.session_state.get('comp_detalhe_id'))
    elif st.session_state.get('show_novo_cliente'):
        modal_novo_cliente()
    elif st.session_state.get('show_novo_comp'):
        data_sel_modal = st.session_state.get('data_agenda_sel', date.today())
        if isinstance(data_sel_modal, date): data_sel_modal = data_sel_modal.isoformat()
        modal_novo_compromisso(st.session_state.get('hora_clicada','08:00'), data_sel_modal)

    if st.session_state['pagina'] == 'menu':
        st.markdown('<div class="linha-div"></div>', unsafe_allow_html=True)
        qtd_hoje, venda_hoje = get_visitas_hoje()
        qtd_semana, venda_semana = get_visitas_semana()
        meta_diaria_c = int(get_config('meta_diaria_clientes'))
        meta_diaria_v = float(get_config('meta_diaria_vendas'))
        meta_semanal_c = meta_diaria_c * 5
        meta_semanal_v = meta_diaria_v * 5
        perc_d_c = min(100, int((qtd_hoje/meta_diaria_c*100) if meta_diaria_c>0 else 0))
        perc_d_v = min(100, int((venda_hoje/meta_diaria_v*100) if meta_diaria_v>0 else 0))
        perc_s_c = min(100, int((qtd_semana/meta_semanal_c*100) if meta_semanal_c>0 else 0))
        perc_s_v = min(100, int((venda_semana/meta_semanal_v*100) if meta_semanal_v>0 else 0))
        with st.container(border=True):
            st.markdown("#### 🎯 Metas")
            html_metas = f'''
            <div style="display:flex; overflow-x:auto; scroll-snap-type:x mandatory; -webkit-overflow-scrolling:touch;" id="swipe-metas">
                <style>#swipe-metas::-webkit-scrollbar{{display:none}}.pg{{min-width:100%; scroll-snap-align:center;}}.box-card{{background:#1e1e1e; border:1px solid #2c2c2c; border-radius:14px; padding:10px; min-height:110px;}}.ttl{{text-align:center; font-weight:800; color:white; font-size:14px; margin-bottom:6px;}}.row{{display:flex; gap:6px;}}.b{{flex:1; background:#2a2a2a; border-radius:10px; padding:8px; border:1px solid #333;}}.lb{{font-size:10px; color:#8a8a8a; font-weight:700; text-transform:uppercase;}}.big{{font-size:20px; color:white; font-weight:900; margin-top:1px;}}.bar{{height:6px; background:#121212; border-radius:99px; margin-top:4px; border:1px solid #333; overflow:hidden;}}.fill{{height:100%; background:#00acc1; border-radius:99px;}}</style>
                <div class="pg"><div class="box-card"><div class="ttl">🎯 DIÁRIA</div><div class="row"><div class="b"><div class="lb">visitas</div><div class="big">{qtd_hoje}/{meta_diaria_c}</div><div class="bar"><div class="fill" style="width:{perc_d_c}%;"></div></div></div><div class="b"><div class="lb">vendas</div><div class="big">R$ {venda_hoje:.0f}/{meta_diaria_v:.0f}</div><div class="bar"><div class="fill" style="width:{perc_d_v}%;"></div></div></div></div></div></div>
                <div class="pg"><div class="box-card"><div class="ttl">📅 SEMANAL</div><div class="row"><div class="b"><div class="lb">visitas</div><div class="big">{qtd_semana}/{meta_semanal_c}</div><div class="bar"><div class="fill" style="width:{perc_s_c}%;"></div></div></div><div class="b"><div class="lb">vendas</div><div class="big">R$ {venda_semana:.0f}/{meta_semanal_v:.0f}</div><div class="bar"><div class="fill" style="width:{perc_s_v}%;"></div></div></div></div></div></div>
            </div>
            '''
            st.components.v1.html(html_metas, height=158, scrolling=False)
            if st.button("🛠 Planejar Metas", use_container_width=True, type="primary", key="planejar_topo"):
                modal_config_metas()
        st.markdown('<div class="linha-div"></div>', unsafe_allow_html=True)
        st.markdown("#### 🕒 Últimas Visitas")
        ultimas = get_ultimas_visitas_lista()
        if not ultimas:
            st.caption("Nenhuma visita registrada ainda.")
        else:
            html_lista = '<div class="bloco-visitas">'
            for cid, data_v, valor, nome_cli in ultimas:
                nome_ex = nome_cli or f"Cliente {cid}"
                valor_txt = f"R$ {valor:.2f}" if valor else "—"
                html_lista += f'<div class="item-visita"><span>✅ {nome_ex}</span><span style="color:#8a8a8a; font-size:11px;">{data_v} • {valor_txt}</span></div>'
            html_lista += '</div>'
            st.markdown(html_lista, unsafe_allow_html=True)
        st.markdown('<div class="linha-div"></div>', unsafe_allow_html=True)
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        col_hist, col_vazio = st.columns([1, 3.5])
        with col_hist:
            if st.button("📜", key="btn_hist_quad", help="Histórico"):
                st.session_state['pagina'] = 'historico'
                st.rerun()
            st.caption("Histórico")

    if st.session_state['pagina'] == 'historico':
        st.markdown('<div style="margin-top:-10px;"></div>', unsafe_allow_html=True)
        st.markdown("### 📜 Histórico")
        c_voltar, c_filtro = st.columns([1, 2])
        with c_voltar:
            if st.button("⬅", use_container_width=True, key="voltar_hist"):
                st.session_state['pagina'] = 'menu'
                st.rerun()
        with c_filtro:
            filtro = st.selectbox(" ", ["🕒 Recentes", "🔁 Mais Visitados", "💰 Mais Vendidos"], key="filtro_unico_hist", label_visibility="collapsed")
        if "Recentes" in filtro:
            st.session_state['filtro_historico'] = 'recentes'
        elif "Visitados" in filtro:
            st.session_state['filtro_historico'] = 'visitados'
        else:
            st.session_state['filtro_historico'] = 'vendidos'
        st.markdown('<div class="linha-div"></div>', unsafe_allow_html=True)
        dados_hist, _ = get_historico_dados()
        df_all = get_clientes()
        if df_all.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            lista = []
            for _, row in df_all.iterrows():
                cid = int(row['id'])
                info = dados_hist.get(cid, {'qtd':0, 'ultima':'', 'total':0})
                lista.append({'id': cid, 'nome': row['nome'], 'endereco': row['endereco'], 'qtd': info['qtd'], 'ultima': info['ultima'] or 'Nunca', 'total': info['total'] or 0})
            if st.session_state['filtro_historico'] == 'recentes':
                lista = sorted(lista, key=lambda x: x['ultima'], reverse=True)
            elif st.session_state['filtro_historico'] == 'visitados':
                lista = sorted(lista, key=lambda x: x['qtd'], reverse=True)
            else:
                lista = sorted(lista, key=lambda x: x['total'], reverse=True)
            for item in lista:
                with st.container(border=True):
                    st.markdown(f"**{item['nome']}**")
                    st.caption(f"📍 {item['endereco'] or 'Sem endereço'} | 🕒 {item['ultima']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Visitas", item['qtd'])
                    with col_b:
                        st.metric("Total", f"R$ {item['total']:.2f}")
                    if st.button("👁 Ver", key=f"hist_ver_{item['id']}", use_container_width=True, type="secondary"):
                        st.session_state['pagina_anterior'] = 'historico'
                        st.session_state['cliente_id'] = item['id']
                        st.session_state['editando_cliente'] = False
                        st.rerun()

    if st.session_state['pagina'] == 'clientes':
        df = get_clientes()
        busca = st.text_input("🔍 Pesquisar", placeholder="Nome do cliente", key="busca_cli_page")
        if busca and not df.empty: df = df[df['nome'].str.contains(busca, case=False, na=False)]
        if df.empty: st.info("Nenhum cliente.")
        else:
            for _, row in df.iterrows():
                visitado = ja_visitou_hoje(int(row['id']))
                cor_bola = "#00acc1" if visitado else "#3b82f6"
                with st.container(border=True):
                    st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:700;">{'✅' if visitado else '⬜'} {row['nome']}</div><div style="color:#8a8a8a; font-size:12px;">{row['endereco'] or 'Sem endereço'}</div></div><div style="width:12px; height:12px; background:{cor_bola}; border-radius:50%;"></div></div>""", unsafe_allow_html=True)
                    if st.button("👁 Ver / Vender", key=f"ver_{row['id']}", use_container_width=True, type="secondary"):
                        st.session_state['pagina_anterior'] = 'clientes'
                        st.session_state['cliente_id'] = int(row['id'])
                        st.session_state['editando_cliente'] = False
                        st.rerun()
        st.markdown("""<a href="?novo_cliente=1" target="_self" style="position: fixed; bottom: 95px; right: 18px; width: 56px; height: 56px; border-radius: 50%; background: #00acc1; color: white; font-size: 32px; display: flex; align-items: center; justify-content: center; text-decoration: none; z-index: 999998;">+</a>""", unsafe_allow_html=True)

    if st.session_state['pagina'] == 'mapa':
        df_all = get_clientes()
        df_loc = df_all.dropna(subset=['lat', 'lng'])
        amanha_str = (date.today() + timedelta(days=1)).isoformat()
        comps_amanha = get_compromissos(amanha_str)
        ids_amanha = set([c['cliente_id'] for c in comps_amanha if c['cliente_id']])
        if df_loc.empty:
            m_geral = mapa_hibrido([-29.942, -50.99], 14)
            st_folium(m_geral, height=500, use_container_width=True, key="geral_vazio")
        else:
            m_geral = mapa_hibrido([df_loc['lat'].mean(), df_loc['lng'].mean()], 14)
            for _, r in df_loc.iterrows():
                visitado = ja_visitou_hoje(int(r['id']))
                cor = "green" if visitado else "blue"
                tem_amanha = int(r['id']) in ids_amanha
                adicionar_pino(m_geral, r['lat'], r['lng'], int(r['id']), r['nome'], cor, tem_amanha)

            map_data_geral = st_folium(m_geral, height=500, use_container_width=True, key="geral")

            if map_data_geral:
                clicked_id = None
                tooltip_val = map_data_geral.get('last_object_clicked_tooltip')
                if tooltip_val:
                    try:
                        clicked_id = int(str(tooltip_val).strip())
                    except:
                        pass
                if not clicked_id:
                    popup_val = map_data_geral.get('last_object_clicked_popup')
                    if popup_val:
                        import re
                        m = re.search(r'ID:\s*(\d+)', str(popup_val))
                        if m:
                            clicked_id = int(m.group(1))

                if clicked_id:
                    st.session_state['pagina_anterior'] = 'mapa'
                    st.session_state['cliente_id'] = clicked_id
                    st.session_state['editando_cliente'] = False
                    st.rerun()

    if st.session_state['pagina'] == 'agenda':
        data_hoje = date.today()
        data_sel = st.session_state['data_agenda_sel']
        inicio_semana = data_sel - timedelta(days=data_sel.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        st.markdown(f"<div style='text-align:center; padding:6px; font-weight:800; font-size:12px; background:#1e1e1e; border:1px solid #2c2c2c; border-radius:10px; color:white; margin-bottom:6px; margin-top:-6px;'>{inicio_semana.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        dias_nomes = ["SEG","TER","QUA","QUI","SEX","SAB","DOM"]
        dias_html = ""
        for i in range(7):
            dia = inicio_semana + timedelta(days=i)
            qtd = len(get_compromissos(dia.isoformat()))
            is_sel = dia == data_sel
            bg = "#2c2c2c"
            color = "white" if is_sel else "#9a9a9a"
            borda = "2px solid #00acc1" if is_sel else "1px solid #2c2c2c"
            dias_html += f"""<div class="dia" data-date="{dia.isoformat()}" style="min-width:48px; flex:1; height:58px; background:{bg}; color:{color}; border:{borda}; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer;"><div style="font-size:10px; font-weight:800;">{dias_nomes[i]}</div><div style="font-size:18px; font-weight:900;">{dia.day}</div><div style="font-size:10px;">{'•'*min(qtd,3) if qtd>0 else ''}</div></div>"""
        data_str = data_sel.isoformat()
        compromissos = get_compromissos(data_str)
        compromissos_json = json.dumps(compromissos)
        zoom_atual = st.session_state.get('zoom_agenda',0)
        html_code = f"""
        <div style="background:#1a1a1a; border:1px solid #2c2c2c; border-radius:12px; padding:6px; margin:6px 0 8px 0;"><div id="semana-row" style="display:flex; gap:6px; overflow-x:auto;">{dias_html}</div></div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin:4px 2px;"><div style="font-size:12px; color:#8a8a8a;">📅 <b style="color:white;">{data_sel.strftime('%A %d/%m')}</b> • pinça 2 dedos pra zoom</div><div style="display:flex; gap:6px;"><button id="btn-zoom-out" style="width:32px; height:32px; border-radius:8px; border:1px solid #333; background:#2c2c2c; color:white;">-</button><button id="btn-zoom-in" style="width:32px; height:32px; border-radius:8px; border:1px solid #333; background:#2c2c2c; color:white;">+</button></div></div>
        <div id="agenda-container" style="border:1px solid #2c2c2c; border-radius:12px; background:#121212; overflow:hidden; touch-action:pan-y;"><div id="timeline" style="position:relative;"></div></div>
        <style>.slot{{box-sizing:border-box; border-bottom:1px solid #1e1e1e; display:flex; align-items:center; height:65px;}}.comp-card{{position:absolute; left:62px; right:6px; border-radius:4px; padding:8px 10px; background:#3a3a3a; color:#e8e8e8; border-left:4px solid #00acc1; z-index:10; font-size:12px;}}</style>
        <script>
        let zoomLevel = {zoom_atual}; const zoomSteps = [15, 30, 60, 120]; const SLOT_H = 65; const comps = {compromissos_json};
        const borda = {{"visita":"#00acc1","viagem":"#9ca3af","evento":"#a78bfa","outros":"#facc15","almoco":"#fb7185"}}; const labels = {{"visita":"👤","viagem":"🚗","evento":"🎉","outros":"📝","almoco":"🍽"}};
        const timeline = document.getElementById('timeline');
        function horaParaMin(h){{ const [hh,mm]=h.split(':').map(Number); return hh*60+mm; }} function minParaHora(m){{ const hh=Math.floor(m/60); const mm=m%60; return String(hh).padStart(2,'0')+':'+String(mm).padStart(2,'0'); }}
        function send(v){{ const input = window.parent.document.querySelector('input[aria-label="drag"]'); if(!input) return; const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; setter.call(input, v); input.dispatchEvent(new Event('input',{{bubbles:true}})); input.dispatchEvent(new Event('change',{{bubbles:true}})); input.dispatchEvent(new KeyboardEvent('keydown',{{bubbles:true, key:'Enter'}})); }}
        function render(){{ timeline.innerHTML=''; const interval=zoomSteps[zoomLevel]; let h=6,m=0; const slots=[]; while(h<20 || (h==20 && m==0)){{ slots.push(String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')); m+=interval; if(m>=60){{ m=0; h++; }} }} slots.forEach(hor=>{{ const div=document.createElement('div'); div.className='slot'; div.dataset.hora=hor; div.innerHTML=`<div style="width:62px; background:#121212; height:100%; display:flex; align-items:center; justify-content:center; border-right:1px solid #1e1e1e; color:#555; font-size:12px; font-weight:700;">${{hor}}</div><div style="flex:1;"></div>`; div.addEventListener('click',()=>{{ send('NEW|'+hor); }}); timeline.appendChild(div); }}); comps.forEach(c=>{{ const ini=horaParaMin(c.hora_inicio); const top=((ini-6*60)/interval)*SLOT_H; const hh=Math.max(28,(c.duracao/interval)*SLOT_H-4); const fim=ini+c.duracao; const div=document.createElement('div'); div.className='comp-card'; div.style.top=top+'px'; div.style.height=hh+'px'; div.style.borderLeftColor=borda[c.tipo]||'#00acc1'; div.innerHTML=`${{labels[c.tipo]}} ${{c.titulo}} <span style="color:#aaa;">${{c.hora_inicio}} - ${{minParaHora(fim)}}</span>`; let drag=false,sY=0,sT=0,mov=false; div.addEventListener('pointerdown',e=>{{ drag=true; mov=false; sY=e.clientY; sT=parseInt(div.style.top)||0; e.preventDefault(); }}); div.addEventListener('pointermove',e=>{{ if(!drag) return; const diff=e.clientY-sY; if(Math.abs(diff)>6) mov=true; div.style.top=(sT+diff)+'px'; }}); div.addEventListener('pointerup',e=>{{ if(!drag) return; drag=false; if(!mov){{ send('DETAIL|'+c.id); return; }} const newTop=parseInt(div.style.top)||0; let idx=Math.round(newTop/SLOT_H); let newMin=6*60+idx*interval; const newH=minParaHora(newMin); if(newH!==c.hora_inicio) send(c.id+'|'+newH); }}); timeline.appendChild(div); }}); }}
        document.getElementById('btn-zoom-in').onclick=()=>{{ if(zoomLevel>0){{ zoomLevel--; render(); send('ZOOM|'+zoomLevel); }} }};
        document.getElementById('btn-zoom-out').onclick=()=>{{ if(zoomLevel<3){{ zoomLevel++; render(); send('ZOOM|'+zoomLevel); }} }};
        let lastDist=0;
        timeline.addEventListener('touchstart', (e)=>{{ if(e.touches.length==2){{ lastDist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY); }} }}, {{passive:false}});
        timeline.addEventListener('touchmove', (e)=>{{ if(e.touches.length==2){{ e.preventDefault(); const dist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY); const diff=dist-lastDist; if(Math.abs(diff)>8){{ if(diff>0 && zoomLevel>0) zoomLevel--; else if(diff<0 && zoomLevel<3) zoomLevel++; render(); send('ZOOM|'+zoomLevel); lastDist=dist; }} }} }}, {{passive:false}});
        document.querySelectorAll('.dia').forEach(el=>{{ el.addEventListener('click',()=>{{ send('DATE|'+el.dataset.date); }}); }}); render();
        </script>
        """
        st.components.v1.html(html_code, height=900, scrolling=True)
        st.markdown("""<a href="?novo_comp=1" target="_self" style="position: fixed; bottom: 95px; right: 18px; width: 56px; height: 56px; border-radius: 50%; background: #00acc1; color: white; font-size: 32px; display: flex; align-items: center; justify-content: center; text-decoration: none; z-index: 999998;">+</a>""", unsafe_allow_html=True)

# =====================
# BARRA FIXA - SEMPRE VISÍVEL, EM QUALQUER TELA
# =====================
pag = st.session_state['pagina']
# se estiver no detalhe do cliente, considera a pagina_anterior como ativa visualmente
pag_visual = st.session_state.get('pagina_anterior', pag) if 'cliente_id' in st.session_state and st.session_state['cliente_id'] is not None else pag

st.markdown(f"""
<div style="position: fixed; bottom: 12px; left: 12px; right: 12px; height: 74px; background: #1f1f1f; border: 1px solid #2c2c2c; border-radius: 20px; display: flex; justify-content: space-around; align-items: center; z-index: 9999999; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
    <a href="?pagina=menu" target="_self" style="width:56px; height:56px; background:{'#00acc1' if pag_visual in ['menu','historico'] else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'white' if pag_visual in ['menu','historico'] else '#8a8a8a'};">☰</a>
    <a href="?pagina=clientes" target="_self" style="width:56px; height:56px; background:{'#00acc1' if pag_visual=='clientes' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'white' if pag_visual=='clientes' else '#8a8a8a'};">👥</a>
    <a href="?pagina=agenda" target="_self" style="width:56px; height:56px; background:{'#00acc1' if pag_visual=='agenda' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'white' if pag_visual=='agenda' else '#8a8a8a'};">📅</a>
    <a href="?pagina=mapa" target="_self" style="width:56px; height:56px; background:{'#00acc1' if pag_visual=='mapa' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'white' if pag_visual=='mapa' else '#8a8a8a'};">📍</a>
</div>
""", unsafe_allow_html=True)
