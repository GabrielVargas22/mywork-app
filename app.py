import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date, datetime, timedelta
from database import init_db, get_clientes, get_cliente_dict, salvar_cliente, atualizar_cliente, atualizar_local, deletar_cliente
from mapas import mapa_hibrido, adicionar_pino
from metas import init_metas, get_config, set_config, registrar_visita, deletar_visita_hoje, get_visitas_hoje, get_visitas_semana, ja_visitou_hoje, get_valor_visita_hoje
from agenda import init_agenda, add_compromisso, get_compromissos, deletar_compromisso, hora_para_minutos, update_horario
import json

init_db()
init_metas()
init_agenda()
st.set_page_config(page_title="MyWork", layout="wide", initial_sidebar_state="collapsed")

# ESTADOS
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'menu'
if 'last_drag' not in st.session_state:
    st.session_state['last_drag'] = ""
if 'data_agenda_sel' not in st.session_state:
    st.session_state['data_agenda_sel'] = date.today()
if 'zoom_agenda' not in st.session_state:
    st.session_state['zoom_agenda'] = 0

# NAV POR QUERY PARAMS - PARA BARRA FIXA
if st.query_params.get("pagina") in ["menu","clientes","agenda","mapa"]:
    st.session_state['pagina'] = st.query_params.get("pagina")
    st.query_params.clear()

st.markdown("""
<style>
.stApp { background-color: #121212!important; }
#MainMenu, footer, header {visibility: hidden; display:none;}
.block-container {padding-top:10px!important; padding-bottom:140px!important;}
h1, h2, h3 { color: white!important; }
div[data-testid="stTabs"] { background-color: #121212; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="margin:0; color:white; font-weight:800; font-size:22px;">MyWork</h1>
<p style="color:#8a8a8a; font-size:12px; margin:0 0 10px 0;">gestão de vendas e agenda</p>
""", unsafe_allow_html=True)

@st.dialog("Novo Compromisso", width="large")
def modal_novo_compromisso(hora_pre, data_str):
    st.markdown(f"**📅 {data_str} | ⏰ {hora_pre}**")
    tipo = st.selectbox("Tipo", ["visita", "viagem", "evento", "outros", "almoco"], format_func=lambda x: {"visita":"👤 Visita Cliente","viagem":"🚗 Viagem","evento":"🎉 Evento","outros":"📝 Outros","almoco":"🍽️ Almoço"}[x], key="tipo_modal_dialog")
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
    nome = st.text_input("Nome *", placeholder="Ex: Mercado do João", key="fab_nome")
    endereco = st.text_input("Endereço", placeholder="Rua, número, bairro", key="fab_end")
    whatsapp = st.text_input("WhatsApp", placeholder="(51) 99999-9999", key="fab_whats")
    pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro", "PIX", "Cartão", "Fiado", "Outro"], key="fab_pag")
    obs = st.text_area("Observações", placeholder="Ex: Entregar segunda de manhã...", key="fab_obs")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar Cliente", type="primary", use_container_width=True):
            if not nome: st.error("Digite o nome")
            else:
                salvar_cliente(nome, endereco, whatsapp, pagamento, obs)
                st.session_state['show_novo_cliente'] = False
                st.toast("Cliente salvo!", icon="✅")
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
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
    tipo_label = {"visita":"👤 Visita","viagem":"🚗 Viagem","evento":"🎉 Evento","outros":"📝 Outros","almoco":"🍽️ Almoço"}.get(comp_encontrado['tipo'], comp_encontrado['tipo'])
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
            if st.button("👁️ Ver dados completos do cliente", type="primary", use_container_width=True):
                st.session_state['cliente_id'] = cli['id']
                st.session_state['show_detalhe_comp'] = False
                st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Excluir compromisso", use_container_width=True):
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
    st.markdown("### ⚙️ Configurar Metas")
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

if 'cliente_id' in st.session_state and st.session_state['cliente_id'] is not None:
    cli = get_cliente_dict(st.session_state['cliente_id'])
    if cli:
        st.button("⬅️ Voltar", on_click=lambda: st.session_state.pop('cliente_id'))
        st.subheader(f"Cliente: {cli['nome']}")
        tab_dados, tab_mapa_cli, tab_venda = st.tabs(["📝 Dados", "🛰️ Local", "💰 Venda"])
        with tab_dados:
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
                        st.success("Salvo!"); st.rerun()
                with col_d:
                    if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                        deletar_cliente(cli['id'])
                        st.session_state.pop('cliente_id')
                        st.rerun()
        with tab_mapa_cli:
            m = mapa_hibrido([cli['lat'] or -29.942, cli['lng'] or -50.99], 16)
            if cli['lat'] and cli['lng']: adicionar_pino(m, cli['lat'], cli['lng'], cli['id'], cli['nome'], "blue")
            map_data = st_folium(m, height=400, use_container_width=True, key=f"mapa_cli_{cli['id']}")
            if map_data and map_data['last_clicked']:
                if st.button("📍 Salvar esta localização", use_container_width=True):
                    atualizar_local(cli['id'], map_data['last_clicked']['lat'], map_data['last_clicked']['lng'])
                    st.success("Local salvo!"); st.rerun()
        with tab_venda:
            valor = st.number_input("Valor da venda R$", min_value=0.0, step=10.0)
            if ja_visitou_hoje(cli['id']):
                st.success(f"Já visitado - R$ {get_valor_visita_hoje(cli['id']):.2f}")
                if st.button("❌ Remover visita de hoje", use_container_width=True):
                    deletar_visita_hoje(cli['id']); st.rerun()
            else:
                if st.button("✅ Registrar visita", type="primary", use_container_width=True):
                    registrar_visita(cli['id'], valor if valor>0 else None)
                    st.success("Visita registrada!"); st.rerun()
        st.stop()

# DRAG FIX - SEM LIMPAR WIDGET
st.text_input("drag", key="drag_result", label_visibility="collapsed")
drag_valor_atual = st.session_state.get('drag_result', '')
if drag_valor_atual and drag_valor_atual!= st.session_state.get('last_drag',''):
    st.session_state['last_drag'] = drag_valor_atual
    if drag_valor_atual.startswith("NAV|"):
        st.session_state['pagina'] = drag_valor_atual.split("|")[1]
        st.rerun()
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
    elif "|" in drag_valor_atual and not drag_valor_atual.startswith("DATE|") and not drag_valor_atual.startswith("ZOOM|"):
        try:
            id_mover, novo_h = drag_valor_atual.split("|")
            update_horario(int(id_mover), novo_h)
            st.toast(f"Movido para {novo_h}!")
        except: pass

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

pagina = st.session_state['pagina']

# MENU - SOMENTE METAS
if pagina == 'menu':
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
        c_tit, c_btn = st.columns([3, 1.3])
        with c_tit: st.markdown("#### 🎯 Metas")
        with c_btn:
            if st.button("🛠️ Planejar", use_container_width=True, type="primary"):
                modal_config_metas()
        html_metas = f'''
        <div style="display:flex; overflow-x:auto; scroll-snap-type:x mandatory;" id="swipe-metas">
            <style>
            #swipe-metas::-webkit-scrollbar{{display:none}}
          .pg{{min-width:100%;}}
          .box-card{{background:#1e1e1e; border:1px solid #2c2c2c; border-radius:16px; padding:14px;}}
          .ttl{{text-align:center; font-weight:800; color:white;}}
          .row{{display:flex; gap:10px;}}
          .b{{flex:1; background:#2a2a2a; border-radius:12px; padding:10px; border:1px solid #333;}}
          .lb{{font-size:10px; color:#8a8a8a;}}
          .big{{font-size:18px; color:white; font-weight:800;}}
          .bar{{height:8px; background:#121212; border-radius:99px; margin-top:6px; border:1px solid #333; overflow:hidden;}}
          .fill{{height:100%; background:#a8d8ff;}}
            </style>
            <div class="pg"><div class="box-card"><div class="ttl">🎯 DIÁRIA</div><div class="row"><div class="b"><div class="lb">visitas</div><div class="big">{qtd_hoje}/{meta_diaria_c}</div><div class="bar"><div class="fill" style="width:{perc_d_c}%;"></div></div></div><div class="b"><div class="lb">vendas</div><div class="big">R$ {venda_hoje:.0f}</div><div class="bar"><div class="fill" style="width:{perc_d_v}%;"></div></div></div></div></div></div>
            <div class="pg"><div class="box-card"><div class="ttl">📅 SEMANAL</div><div class="row"><div class="b"><div class="lb">visitas</div><div class="big">{qtd_semana}/{meta_semanal_c}</div><div class="bar"><div class="fill" style="width:{perc_s_c}%;"></div></div></div><div class="b"><div class="lb">vendas</div><div class="big">R$ {venda_semana:.0f}</div><div class="bar"><div class="fill" style="width:{perc_s_v}%;"></div></div></div></div></div></div>
        </div>
        <div style="text-align:center; color:#555; font-size:11px; margin-top:8px;">👉 arraste para o lado 👉</div>
        '''
        st.components.v1.html(html_metas, height=200, scrolling=False)

if pagina == 'clientes':
    df = get_clientes()
    busca = st.text_input("🔍 Pesquisar", placeholder="Nome do cliente")
    if busca and not df.empty: df = df[df['nome'].str.contains(busca, case=False, na=False)]
    if df.empty: st.info("Nenhum cliente.")
    else:
        for _, row in df.iterrows():
            visitado = ja_visitou_hoje(int(row['id']))
            cor_bola = "#22c55e" if visitado else "#3b82f6"
            with st.container(border=True):
                st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:700;">{'✅' if visitado else '⬜'} {row['nome']}</div><div style="color:#8a8a8a; font-size:12px;">{row['endereco'] or 'Sem endereço'}</div></div><div style="width:12px; height:12px; background:{cor_bola}; border-radius:50%;"></div></div>""", unsafe_allow_html=True)
                if st.button("👁️ Ver / Vender", key=f"ver_{row['id']}", use_container_width=True):
                    st.session_state['cliente_id'] = int(row['id']); st.rerun()
    st.markdown("""<a href="?novo_cliente=1" target="_self" style="position: fixed; bottom: 95px; right: 18px; width: 56px; height: 56px; border-radius: 50%; background: #a8d8ff; color: #121212; font-size: 32px; display: flex; align-items: center; justify-content: center; text-decoration: none; z-index: 999998;">+</a>""", unsafe_allow_html=True)

if pagina == 'mapa':
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
        st_folium(m_geral, height=500, use_container_width=True, key="geral")

if pagina == 'agenda':
    data_hoje = date.today()
    data_sel = st.session_state['data_agenda_sel']
    inicio_semana = data_sel - timedelta(days=data_sel.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    drag_val = st.session_state.get('drag_result','')
    if drag_val.startswith("DATE|"):
        try:
            nova_data = date.fromisoformat(drag_val.split("|")[1])
            st.session_state['data_agenda_sel'] = nova_data
            st.rerun()
        except: pass
    if drag_val.startswith("ZOOM|"):
        try: st.session_state['zoom_agenda'] = int(drag_val.split("|")[1])
        except: pass
    c_ant, c_mid, c_prox = st.columns([1, 3, 1])
    with c_ant:
        if st.button("◀️", use_container_width=True, key="sem_ant"):
            st.session_state['data_agenda_sel'] = inicio_semana - timedelta(days=7); st.rerun()
    with c_mid:
        st.markdown(f"<div style='text-align:center; padding:6px; font-weight:800; font-size:13px; background:#1e1e1e; border:1px solid #2c2c2c; border-radius:10px; color:white;'>{inicio_semana.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}</div>", unsafe_allow_html=True)
    with c_prox:
        if st.button("▶️", use_container_width=True, key="sem_prox"):
            st.session_state['data_agenda_sel'] = inicio_semana + timedelta(days=7); st.rerun()
    dias_nomes = ["SEG","TER","QUA","QUI","SEX","SAB","DOM"]
    dias_html = ""
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        qtd = len(get_compromissos(dia.isoformat()))
        is_sel = dia == data_sel
        bg = "#2c2c2c"
        color = "white" if is_sel else "#9a9a9a"
        borda = "2px solid #a8d8ff" if is_sel else "1px solid #2c2c2c"
        dias_html += f"""<div class="dia" data-date="{dia.isoformat()}" style="min-width:48px; flex:1; height:62px; background:{bg}; color:{color}; border:{borda}; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer;"><div style="font-size:10px; font-weight:800;">{dias_nomes[i]}</div><div style="font-size:18px; font-weight:900;">{dia.day}</div><div style="font-size:10px;">{'•'*min(qtd,3) if qtd>0 else ''}</div></div>"""
    data_str = data_sel.isoformat()
    compromissos = get_compromissos(data_str)
    compromissos_json = json.dumps(compromissos)
    zoom_atual = st.session_state.get('zoom_agenda',0)
    html_code = f"""
    <div style="background:#1a1a1a; border:1px solid #2c2c2c; border-radius:14px; padding:8px; margin:10px 0 12px 0;"><div id="semana-row" style="display:flex; gap:6px; overflow-x:auto;">{dias_html}</div></div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin:6px 2px;"><div style="font-size:12px; color:#8a8a8a;">📅 <b style="color:white;">{data_sel.strftime('%A %d/%m')}</b> • pinça 2 dedos pra zoom</div><div style="display:flex; gap:6px;"><button id="btn-zoom-out" style="width:32px; height:32px; border-radius:8px; border:1px solid #333; background:#2c2c2c; color:white;">-</button><button id="btn-zoom-in" style="width:32px; height:32px; border-radius:8px; border:1px solid #333; background:#2c2c2c; color:white;">+</button></div></div>
    <div id="agenda-container" style="border:1px solid #2c2c2c; border-radius:12px; background:#121212; overflow:hidden; touch-action:pan-y;"><div id="timeline" style="position:relative;"></div></div>
    <style>.slot{{box-sizing:border-box; border-bottom:1px solid #1e1e1e; display:flex; align-items:center; height:65px;}}.comp-card{{position:absolute; left:62px; right:6px; border-radius:4px; padding:8px 10px; background:#3a3a3a; color:#e8e8e8; border-left:4px solid #a8d8ff; z-index:10; font-size:12px;}}</style>
    <script>
    let zoomLevel = {zoom_atual}; const zoomSteps = [15, 30, 60, 120]; const SLOT_H = 65; const comps = {compromissos_json};
    const borda = {{"visita":"#f472b6","viagem":"#9ca3af","evento":"#a78bfa","outros":"#facc15","almoco":"#fb7185"}}; const labels = {{"visita":"👤","viagem":"🚗","evento":"🎉","outros":"📝","almoco":"🍽️"}};
    const timeline = document.getElementById('timeline');
    function horaParaMin(h){{ const [hh,mm]=h.split(':').map(Number); return hh*60+mm; }} function minParaHora(m){{ const hh=Math.floor(m/60); const mm=m%60; return String(hh).padStart(2,'0')+':'+String(mm).padStart(2,'0'); }}
    function send(v){{ const input = window.parent.document.querySelector('input[aria-label="drag"]'); if(!input) return; const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; setter.call(input, v); input.dispatchEvent(new Event('input',{{bubbles:true}})); input.dispatchEvent(new Event('change',{{bubbles:true}})); input.dispatchEvent(new KeyboardEvent('keydown',{{bubbles:true, key:'Enter'}})); }}
    function render(){{ timeline.innerHTML=''; const interval=zoomSteps[zoomLevel]; let h=6,m=0; const slots=[]; while(h<20 || (h==20 && m==0)){{ slots.push(String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')); m+=interval; if(m>=60){{ m=0; h++; }} }} slots.forEach(hor=>{{ const div=document.createElement('div'); div.className='slot'; div.dataset.hora=hor; div.innerHTML=`<div style="width:62px; background:#121212; height:100%; display:flex; align-items:center; justify-content:center; border-right:1px solid #1e1e1e; color:#555; font-size:12px; font-weight:700;">${{hor}}</div><div style="flex:1;"></div>`; div.addEventListener('click',()=>{{ send('NEW|'+hor); }}); timeline.appendChild(div); }}); comps.forEach(c=>{{ const ini=horaParaMin(c.hora_inicio); const top=((ini-6*60)/interval)*SLOT_H; const hh=Math.max(28,(c.duracao/interval)*SLOT_H-4); const fim=ini+c.duracao; const div=document.createElement('div'); div.className='comp-card'; div.style.top=top+'px'; div.style.height=hh+'px'; div.style.borderLeftColor=borda[c.tipo]||'#a8d8ff'; div.innerHTML=`${{labels[c.tipo]}} ${{c.titulo}} <span style="color:#aaa;">${{c.hora_inicio}} - ${{minParaHora(fim)}}</span>`; let drag=false,sY=0,sT=0,mov=false; div.addEventListener('pointerdown',e=>{{ drag=true; mov=false; sY=e.clientY; sT=parseInt(div.style.top)||0; e.preventDefault(); }}); div.addEventListener('pointermove',e=>{{ if(!drag) return; const diff=e.clientY-sY; if(Math.abs(diff)>6) mov=true; div.style.top=(sT+diff)+'px'; }}); div.addEventListener('pointerup',e=>{{ if(!drag) return; drag=false; if(!mov){{ send('DETAIL|'+c.id); return; }} const newTop=parseInt(div.style.top)||0; let idx=Math.round(newTop/SLOT_H); let newMin=6*60+idx*interval; const newH=minParaHora(newMin); if(newH!==c.hora_inicio) send(c.id+'|'+newH); }}); timeline.appendChild(div); }}); }}
    document.getElementById('btn-zoom-in').onclick=()=>{{ if(zoomLevel>0){{ zoomLevel--; render(); send('ZOOM|'+zoomLevel); }} }};
    document.getElementById('btn-zoom-out').onclick=()=>{{ if(zoomLevel<3){{ zoomLevel++; render(); send('ZOOM|'+zoomLevel); }} }};
    let lastDist=0;
    timeline.addEventListener('touchstart', (e)=>{{ if(e.touches.length==2){{ lastDist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY); }} }}, {{passive:false}});
    timeline.addEventListener('touchmove', (e)=>{{ if(e.touches.length==2){{ e.preventDefault(); const dist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY); if(Math.abs(dist-lastDist)>30){{ if(dist>lastDist && zoomLevel>0) zoomLevel--; else if(dist<lastDist && zoomLevel<3) zoomLevel++; render(); send('ZOOM|'+zoomLevel); lastDist=dist; }} }} }}, {{passive:false}});
    document.querySelectorAll('.dia').forEach(el=>{{ el.addEventListener('click',()=>{{ send('DATE|'+el.dataset.date); }}); }}); render();
    </script>
    """
    st.components.v1.html(html_code, height=900, scrolling=True)
    st.markdown("""<a href="?novo_comp=1" target="_self" style="position: fixed; bottom: 95px; right: 18px; width: 56px; height: 56px; border-radius: 50%; background: #a8d8ff; color: #121212; font-size: 32px; display: flex; align-items: center; justify-content: center; text-decoration: none; z-index: 999998;">+</a>""", unsafe_allow_html=True)

# BARRA INFERIOR FIXA DE VERDADE - 4 QUADRADOS COM ICONE
pag = st.session_state['pagina']
st.markdown(f"""
<div style="position: fixed; bottom: 12px; left: 12px; right: 12px; height: 74px; background: #1f1f1f; border: 1px solid #2c2c2c; border-radius: 20px; display: flex; justify-content: space-around; align-items: center; z-index: 9999999; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
    <a href="?pagina=menu" target="_self" style="width:56px; height:56px; background:{'#a8d8ff' if pag=='menu' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'#121212' if pag=='menu' else '#8a8a8a'};">☰</a>
    <a href="?pagina=clientes" target="_self" style="width:56px; height:56px; background:{'#a8d8ff' if pag=='clientes' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'#121212' if pag=='clientes' else '#8a8a8a'};">👥</a>
    <a href="?pagina=agenda" target="_self" style="width:56px; height:56px; background:{'#a8d8ff' if pag=='agenda' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'#121212' if pag=='agenda' else '#8a8a8a'};">📅</a>
    <a href="?pagina=mapa" target="_self" style="width:56px; height:56px; background:{'#a8d8ff' if pag=='mapa' else '#2c2c2c'}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; text-decoration:none; color:{'#121212' if pag=='mapa' else '#8a8a8a'};">📍</a>
</div>
""", unsafe_allow_html=True)
