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

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-bottom: 120px!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="margin-bottom:0px; padding-bottom:0px; font-weight:800;">MyWork</h1>
<p style="color:#64748b; font-size:13px; margin-top:2px;">gestão de vendas e agenda</p>
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
    st.caption("A meta semanal é calculada automaticamente: diária x 5 dias úteis (seg a sex)")
    meta_diaria_c = int(get_config('meta_diaria_clientes'))
    meta_diaria_v = float(get_config('meta_diaria_vendas'))
    nd_c = st.number_input("Meta diária - visitas", value=meta_diaria_c, min_value=1, step=1)
    nd_v = st.number_input("Meta diária - vendas R$", value=meta_diaria_v, min_value=0.0, step=50.0)
    st.divider()
    st.info(f"Semanal será: **{nd_c*5} visitas** e **R$ {nd_v*5:.2f} em vendas**")
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
                obs_val = cli.get('observacoes') or cli.get('obs') or cli.get('observacao') or ""
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
            st.write("Clique no mapa para definir a localização")
            m = mapa_hibrido([cli['lat'] or -29.942, cli['lng'] or -50.99], 16)
            if cli['lat'] and cli['lng']: adicionar_pino(m, cli['lat'], cli['lng'], cli['id'], cli['nome'], "blue")
            map_data = st_folium(m, height=400, use_container_width=True, key=f"mapa_cli_{cli['id']}")
            if map_data and map_data['last_clicked']:
                if st.button("📍 Salvar esta localização", use_container_width=True):
                    atualizar_local(cli['id'], map_data['last_clicked']['lat'], map_data['last_clicked']['lng'])
                    st.success("Local salvo!"); st.rerun()
        with tab_venda:
            st.markdown("### Registrar visita")
            valor = st.number_input("Valor da venda R$", min_value=0.0, step=10.0)
            if ja_visitou_hoje(cli['id']):
                st.success(f"Já visitado hoje - R$ {get_valor_visita_hoje(cli['id']):.2f}")
                if st.button("❌ Remover visita de hoje", use_container_width=True):
                    deletar_visita_hoje(cli['id']); st.rerun()
            else:
                if st.button("✅ Registrar visita", type="primary", use_container_width=True):
                    registrar_visita(cli['id'], valor if valor>0 else None)
                    st.success("Visita registrada!"); st.rerun()
        st.stop()

# ===== CARD DE METAS - 1 QUADRO POR VEZ COM ARRASTE =====
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
    with c_tit:
        st.markdown("#### 🎯 Metas")
    with c_btn:
        if st.button("🛠️ Planejar", use_container_width=True, type="primary"):
            modal_config_metas()

    # ===== CORREÇÃO: use f''' e st.components.v1.html =====
# No card de metas troque para:

    html_metas = f'''
    <div style="display:flex; overflow-x:auto; scroll-snap-type:x mandatory; -webkit-overflow-scrolling:touch;" id="swipe-metas">
        <style>
        #swipe-metas::-webkit-scrollbar{{display:none}}
        .pg{{min-width:100%; scroll-snap-align:center; box-sizing:border-box;}}
        .box-card{{background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px; padding:14px;}}
        .ttl{{text-align:center; font-weight:800; font-size:14px; margin-bottom:10px;}}
        .row{{display:flex; gap:10px;}}
        .b{{flex:1; background:white; border-radius:12px; padding:10px; border:1px solid #e2e8f0;}}
        .lb{{font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase;}}
        .big{{font-size:18px; font-weight:800;}}
        .bar{{height:8px; background:#e2e8f0; border-radius:99px; margin-top:6px; overflow:hidden;}}
        .fill{{height:100%; border-radius:99px;}}
        </style>

        <div class="pg">
            <div class="box-card">
                <div class="ttl">🎯 DIÁRIA</div>
                <div class="row">
                    <div class="b">
                        <div class="lb">visitas</div>
                        <div class="big">{qtd_hoje}/{meta_diaria_c}</div>
                        <div class="bar"><div class="fill" style="width:{perc_d_c}%; background:#2563eb;"></div></div>
                        <div style="font-size:11px; color:#64748b; margin-top:4px;">{perc_d_c}%</div>
                    </div>
                    <div class="b">
                        <div class="lb">vendas</div>
                        <div class="big">R$ {venda_hoje:.0f}/{meta_diaria_v:.0f}</div>
                        <div class="bar"><div class="fill" style="width:{perc_d_v}%; background:#16a34a;"></div></div>
                        <div style="font-size:11px; color:#64748b; margin-top:4px;">{perc_d_v}%</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="pg">
            <div class="box-card">
                <div class="ttl">📅 SEMANAL</div>
                <div class="row">
                    <div class="b">
                        <div class="lb">visitas</div>
                        <div class="big">{qtd_semana}/{meta_semanal_c}</div>
                        <div class="bar"><div class="fill" style="width:{perc_s_c}%; background:#2563eb;"></div></div>
                        <div style="font-size:11px; color:#64748b; margin-top:4px;">{perc_s_c}%</div>
                    </div>
                    <div class="b">
                        <div class="lb">vendas</div>
                        <div class="big">R$ {venda_semana:.0f}/{meta_semanal_v:.0f}</div>
                        <div class="bar"><div class="fill" style="width:{perc_s_v}%; background:#16a34a;"></div></div>
                        <div style="font-size:11px; color:#64748b; margin-top:4px;">{perc_s_v}%</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div style="text-align:center; color:#94a3b8; font-size:11px; margin-top:8px;">👉 arraste para o lado 👉</div>
    '''
    st.components.v1.html(html_metas, height=200, scrolling=False)

# DRAG CONTROL DA AGENDA
if 'last_drag' not in st.session_state: st.session_state['last_drag'] = ""
drag_valor_atual = st.session_state.get('drag_result', '')
if drag_valor_atual and drag_valor_atual!= st.session_state['last_drag']:
    if "DETAIL|" in drag_valor_atual or "NEW|" in drag_valor_atual or "|" in drag_valor_atual:
        st.session_state['last_drag'] = drag_valor_atual
        if drag_valor_atual.startswith("NEW|"):
            _, hora_nova = drag_valor_atual.split("|")
            st.session_state['hora_clicada'] = hora_nova
            st.session_state['show_novo_comp'] = True
            st.session_state['show_detalhe_comp'] = False
            st.session_state['show_novo_cliente'] = False
        elif drag_valor_atual.startswith("DETAIL|"):
            _, id_str = drag_valor_atual.split("|")
            st.session_state['comp_detalhe_id'] = int(id_str)
            st.session_state['show_detalhe_comp'] = True
            st.session_state['show_novo_comp'] = False
            st.session_state['show_novo_cliente'] = False
        elif "|" in drag_valor_atual:
            try:
                id_mover, novo_h = drag_valor_atual.split("|")
                update_horario(int(id_mover), novo_h)
                st.toast(f"Movido para {novo_h}!")
            except: pass

st.text_input("drag", key="drag_result", label_visibility="collapsed")

if st.query_params.get("novo_cliente") == "1":
    st.session_state['show_novo_cliente'] = True
    st.session_state['show_novo_comp'] = False
    st.session_state['show_detalhe_comp'] = False
    st.query_params.clear()
    st.rerun()

if st.query_params.get("novo_comp") == "1":
    st.session_state['hora_clicada'] = "08:00"
    st.session_state['show_novo_comp'] = True
    st.session_state['show_novo_cliente'] = False
    st.session_state['show_detalhe_comp'] = False
    st.query_params.clear()
    st.rerun()

if st.session_state.get('show_detalhe_comp'):
    modal_detalhe_compromisso(st.session_state.get('comp_detalhe_id'))
elif st.session_state.get('show_novo_cliente'):
    modal_novo_cliente()
elif st.session_state.get('show_novo_comp'):
    data_sel_modal = st.session_state.get('data_agenda_sel', date.today())
    if isinstance(data_sel_modal, date):
        data_sel_modal = data_sel_modal.isoformat()
    modal_novo_compromisso(st.session_state.get('hora_clicada','08:00'), data_sel_modal)

aba_lista, aba_mapa, aba_agenda = st.tabs(["📋 Lista", "🛰️ Mapa", "📅 Agenda"])

with aba_lista:
    df = get_clientes()
    busca = st.text_input("🔍 Pesquisar", placeholder="Nome do cliente")
    if busca and not df.empty: df = df[df['nome'].str.contains(busca, case=False, na=False)]
    if df.empty: st.info("Nenhum cliente. Toque no + azul para adicionar.")
    else:
        for _, row in df.iterrows():
            visitado = ja_visitou_hoje(int(row['id']))
            with st.container(border=True):
                st.markdown(f"{'✅' if visitado else '⬜'} **{row['nome']}**")
                st.caption(f"{row['endereco'] or 'Sem endereço'}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("👁️ Ver / Vender", key=f"ver_{row['id']}", use_container_width=True):
                        st.session_state['cliente_id'] = int(row['id']); st.rerun()
                with c2: st.write("✅ Visitado" if visitado else "⬜ Pendente")
    st.markdown("""
    <a href="?novo_cliente=1" target="_self" style="
        position: fixed; bottom: 30px; right: 22px; width: 64px; height: 64px;
        border-radius: 50%; background: #2563eb; color: white; font-size: 36px;
        font-weight: 300; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 9999999; box-shadow: 0 6px 20px rgba(37,99,235,0.5); line-height: 1;
    ">+</a>
    """, unsafe_allow_html=True)

with aba_mapa:
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
    if st.query_params.get("cliente_id"):
        try:
            cid = int(st.query_params.get("cliente_id"))
            st.session_state['cliente_id'] = cid
            st.query_params.clear()
            st.rerun()
        except: pass

with aba_agenda:
    if 'data_agenda_sel' not in st.session_state:
        st.session_state['data_agenda_sel'] = date.today()
    if 'zoom_agenda' not in st.session_state:
        st.session_state['zoom_agenda'] = 0 # 0=15min 1=30min 2=60min 3=120min

    data_hoje = date.today()
    data_sel = st.session_state['data_agenda_sel']
    inicio_semana = data_sel - timedelta(days=data_sel.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    # --- CONTROLE DE DATA VIA DRAG INPUT ---
    drag_val = st.session_state.get('drag_result','')
    if drag_val.startswith("DATE|"):
        try:
            nova_data = date.fromisoformat(drag_val.split("|")[1])
            st.session_state['data_agenda_sel'] = nova_data
            st.rerun()
        except: pass
    if drag_val.startswith("ZOOM|"):
        try:
            st.session_state['zoom_agenda'] = int(drag_val.split("|")[1])
        except: pass

    # Header semana com setas
    c_ant, c_mid, c_prox = st.columns([1, 3, 1])
    with c_ant:
        if st.button("◀️", use_container_width=True, key="sem_ant"):
            st.session_state['data_agenda_sel'] = inicio_semana - timedelta(days=7)
            st.rerun()
    with c_mid:
        st.markdown(f"<div style='text-align:center; padding:6px; font-weight:800; font-size:13px; background:#f1f5f9; border-radius:10px;'>{inicio_semana.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}</div>", unsafe_allow_html=True)
    with c_prox:
        if st.button("▶️", use_container_width=True, key="sem_prox"):
            st.session_state['data_agenda_sel'] = inicio_semana + timedelta(days=7)
            st.rerun()

    # Gera HTML da semana em RETANGULO com 7 quadrados lado a lado
    dias_nomes = ["SEG","TER","QUA","QUI","SEX","SAB","DOM"]
    dias_html = ""
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        qtd = len(get_compromissos(dia.isoformat()))
        is_sel = dia == data_sel
        is_hoje = dia == data_hoje
        bg = "#2563eb" if is_sel else "white"
        color = "white" if is_sel else "#334155"
        borda = "2px solid #2563eb" if is_sel else "1px solid #e2e8f0"
        dias_html += f"""
        <div class="dia" data-date="{dia.isoformat()}" style="min-width:48px; flex:1; height:62px; background:{bg}; color:{color}; border:{borda}; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; position:relative;">
            <div style="font-size:10px; font-weight:800;">{dias_nomes[i]}</div>
            <div style="font-size:18px; font-weight:900; line-height:1;">{dia.day}</div>
            <div style="font-size:10px; margin-top:2px;">{'•'*min(qtd,3) if qtd>0 else ''}</div>
            { '<div style="position:absolute; bottom:-4px; width:18px; height:4px; background:#2563eb; border-radius:99px;"></div>' if is_hoje else '' }
        </div>
        """

    data_str = data_sel.isoformat()
    compromissos = get_compromissos(data_str)
    compromissos_json = json.dumps(compromissos)
    zoom_atual = st.session_state.get('zoom_agenda',0)

    html_code = f"""
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:14px; padding:8px; margin:10px 0 12px 0;">
        <div id="semana-row" style="display:flex; gap:6px; overflow-x:auto; scrollbar-width:none;">{dias_html}</div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin:6px 2px;">
        <div style="font-size:12px; color:#64748b;">📅 <b>{data_sel.strftime('%A %d/%m')}</b> • pinça com 2 dedos pra zoom</div>
        <div style="display:flex; gap:6px;">
            <button id="btn-zoom-out" style="width:32px; height:32px; border-radius:8px; border:1px solid #e2e8f0; background:white; font-weight:800;">-</button>
            <button id="btn-zoom-in" style="width:32px; height:32px; border-radius:8px; border:1px solid #e2e8f0; background:white; font-weight:800;">+</button>
        </div>
    </div>

    <div id="agenda-container" style="border:1.5px solid #ddd; border-radius:12px; font-family:sans-serif; background:white; overflow:hidden; user-select:none; touch-action:pan-y;">
        <div id="timeline" style="position:relative;"></div>
    </div>

    <style>
   .slot{{box-sizing:border-box; border-bottom:1px solid #f1f5f9; display:flex; align-items:center; cursor:pointer;}}
   .comp-card{{position:absolute; left:70px; right:6px; border-radius:10px; padding:8px 10px; cursor:pointer; border:1.5px solid #cbd5e1; border-left:6px solid #3b82f6; z-index:10; touch-action:none; box-shadow:0 2px 8px rgba(0,0,0,0.12); font-size:12px; overflow:hidden; user-select:none; box-sizing:border-box; line-height:1.2;}}
   .dragging{{opacity:0.9; z-index:100!important; box-shadow:0 12px 24px rgba(0,0,0,0.2)!important; transform:scale(1.03)!important;}}
    </style>

    <script>
    let zoomLevel = {zoom_atual};
    const zoomSteps = [15, 30, 60, 120];
    const SLOT_H = 65;
    const comps = {compromissos_json};

    const cores = {{"visita":"#dbeafe","viagem":"#f1f5f9","evento":"#ede9fe","outros":"#dcfce7","almoco":"#fef3c7"}};
    const borda = {{"visita":"#3b82f6","viagem":"#64748b","evento":"#8b5cf6","outros":"#22c55e","almoco":"#f59e0b"}};
    const labels = {{"visita":"👤","viagem":"🚗","evento":"🎉","outros":"📝","almoco":"🍽️"}};
    const timeline = document.getElementById('timeline');

    function horaParaMin(h){{ const [hh,mm]=h.split(':').map(Number); return hh*60+mm; }}
    function minParaHora(m){{ const hh=Math.floor(m/60); const mm=m%60; return String(hh).padStart(2,'0')+':'+String(mm).padStart(2,'0'); }}
    function sendToStreamlit(value) {{
        const input = window.parent.document.querySelector('input[aria-label="drag"]');
        if (!input) return;
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(input, value);
        input.dispatchEvent(new Event('input', {{bubbles:true}}));
        input.dispatchEvent(new Event('change', {{bubbles:true}}));
        input.dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, key:'Enter', code:'Enter', keyCode:13}}));
    }}

    function renderTimeline(){{
        timeline.innerHTML = '';
        const interval = zoomSteps[zoomLevel];
        let h=6, m=0;
        const slots=[];
        while(h < 20 || (h==20 && m==0)){{
            slots.push(`${{String(h).padStart(2,'0')}}:${{String(m).padStart(2,'0')}}`);
            m+=interval; if(m>=60){{ m=0; h+=1; }}
        }}
        slots.forEach(horario => {{
            const div = document.createElement('div');
            div.className='slot';
            div.dataset.hora=horario;
            div.style.height=SLOT_H+'px';
            div.innerHTML=`<div style="width:62px; min-width:62px; text-align:center; background:#f8fafc; height:100%; display:flex; align-items:center; justify-content:center; border-right:2px solid #e2e8f0; font-weight:800; font-size:12px; color:#334155;">${{horario}}</div><div style="flex:1; height:100%; display:flex; align-items:center; padding-left:10px; color:#e2e8f0; font-size:11px;">•</div>`;
            div.addEventListener('click', (e)=>{{ if(e.target.closest('.comp-card')) return; sendToStreamlit('NEW|'+horario); }});
            timeline.appendChild(div);
        }});

        comps.forEach(comp => {{
            const iniMin = horaParaMin(comp.hora_inicio);
            if(iniMin < 6*60 || iniMin > 20*60) return;
            const offsetTop = ((iniMin - 6*60)/interval)*SLOT_H;
            const height = Math.max(24, (comp.duracao/interval)*SLOT_H - 6);
            const fimMin = iniMin + comp.duracao;
            const div = document.createElement('div');
            div.className='comp-card';
            div.style.top=offsetTop+'px';
            div.style.height=height+'px';
            div.style.background=cores[comp.tipo] || '#fff';
            div.style.borderLeftColor=borda[comp.tipo] || '#3b82f6';
            div.innerHTML=`<b>${{labels[comp.tipo]}} ${{comp.titulo}}</b><br><span style="font-size:11px; opacity:0.8;">⏰ ${{comp.hora_inicio}} - ${{minParaHora(fimMin)}} • ${{comp.duracao}}min</span>`;
            let isDragging=false, startY=0, startTop=0, moved=false;
            div.addEventListener('pointerdown', (e)=>{{
                isDragging=true; moved=false; startY=e.clientY; startTop=parseInt(div.style.top)||0;
                div.classList.add('dragging'); div.setPointerCapture(e.pointerId); e.preventDefault(); e.stopPropagation();
            }});
            div.addEventListener('pointermove', (e)=>{{
                if(!isDragging) return;
                const diff=e.clientY-startY;
                if(Math.abs(diff)>6) moved=true;
                let newTop=startTop+diff;
                if(newTop<0) newTop=0;
                div.style.top=newTop+'px';
            }});
            div.addEventListener('pointerup', (e)=>{{
                if(!isDragging) return;
                isDragging=false; div.classList.remove('dragging');
                try{{ div.releasePointerCapture(e.pointerId); }}catch(_ ){{}}
                if(!moved){{ sendToStreamlit('DETAIL|'+comp.id); return; }}
                const newTop=parseInt(div.style.top)||0;
                let slotIndex=Math.round(newTop/SLOT_H);
                let newMin=6*60+slotIndex*interval;
                if(newMin<6*60) newMin=6*60;
                if(newMin+comp.duracao>20*60+15) newMin=20*60+15-comp.duracao;
                const snappedTop=((newMin-6*60)/interval)*SLOT_H;
                div.style.top=snappedTop+'px';
                const novoH=minParaHora(newMin);
                if(novoH!==comp.hora_inicio) sendToStreamlit(comp.id+'|'+novoH);
                e.stopPropagation();
            }});
            timeline.appendChild(div);
        }});
    }}

    // Zoom botoes
    document.getElementById('btn-zoom-in').onclick = ()=>{{ if(zoomLevel>0){{ zoomLevel--; renderTimeline(); sendToStreamlit('ZOOM|'+zoomLevel); }} }};
    document.getElementById('btn-zoom-out').onclick = ()=>{{ if(zoomLevel<zoomSteps.length-1){{ zoomLevel++; renderTimeline(); sendToStreamlit('ZOOM|'+zoomLevel); }} }};

    // Pinch to zoom
    let lastDist=0;
    timeline.addEventListener('touchstart', (e)=>{{ if(e.touches.length==2){{ lastDist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY); }} }}, {{passive:false}});
    timeline.addEventListener('touchmove', (e)=>{{
        if(e.touches.length==2){{
            e.preventDefault();
            const dist=Math.hypot(e.touches[0].pageX-e.touches[1].pageX, e.touches[0].pageY-e.touches[1].pageY);
            if(Math.abs(dist-lastDist)>30){{
                if(dist>lastDist && zoomLevel>0) zoomLevel--; // abre = mais detalhe
                else if(dist<lastDist && zoomLevel<zoomSteps.length-1) zoomLevel++;
                renderTimeline();
                sendToStreamlit('ZOOM|'+zoomLevel);
                lastDist=dist;
            }}
        }}
    }}, {{passive:false}});

    // Dias da semana clique
    document.querySelectorAll('.dia').forEach(el=>{{
        el.addEventListener('click', ()=>{{ sendToStreamlit('DATE|'+el.dataset.date); }});
    }});

    renderTimeline();
    </script>
    """
    st.components.v1.html(html_code, height=900, scrolling=True)

    st.markdown("""
    <a href="?novo_comp=1" target="_self" style="
        position: fixed; bottom: 30px; right: 22px; width: 64px; height: 64px;
        border-radius: 50%; background: #ea580c; color: white; font-size: 32px;
        font-weight: 300; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 9999999; box-shadow: 0 6px 20px rgba(234,88,12,0.5); line-height: 1;
    ">+</a>
    """, unsafe_allow_html=True)
