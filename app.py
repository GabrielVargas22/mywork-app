import streamlit as st
from streamlit_folium import st_folium
from datetime import date, datetime, timedelta
import folium

from database import init_db, get_clientes, get_cliente_dict, salvar_cliente
from agenda import init_agenda, get_compromissos, add_compromisso, deletar_compromisso, update_horario, hora_para_minutos, CORES
from metas import init_metas, tela_metas_completa, registrar_visita, ja_visitou_hoje
from mapas import mapa_hibrido, mapa_satelite, adicionar_pino

st.set_page_config(page_title="MyWork", layout="wide", page_icon="💼")

init_db()
init_agenda()
init_metas()

# --- ESTILO GLOBAL ---
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.block-container { padding-top: 10px; padding-bottom: 90px; }
.bottom-nav {
    position: fixed; bottom: 0; left: 0; right: 0; height: 70px;
    background: white; border-top: 1px solid #e5e7eb;
    display: flex; justify-content: space-around; align-items: center;
    z-index: 100; box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'menu'
if 'data_agenda' not in st.session_state:
    st.session_state['data_agenda'] = date.today().isoformat()
if 'novo_cli_lat' not in st.session_state:
    st.session_state['novo_cli_lat'] = None
    st.session_state['novo_cli_lng'] = None

query_params = st.query_params
if 'cliente_id' in query_params:
    st.session_state['cliente_detalhe'] = int(query_params['cliente_id'])

def pagina_menu():
    st.markdown("## 💼 MyWork")
    tela_metas_completa()
    st.divider()
    st.markdown("### 📋 Visitas de hoje")
    clientes = get_clientes()
    for cli in clientes:
        if ja_visitou_hoje(cli[0]):
            st.success(f"✅ {cli[1]} - visitado")

def pagina_clientes():
    st.markdown("## 👥 Clientes")

    busca = st.text_input("🔍 Buscar cliente", placeholder="Digite nome...")
    clientes = get_clientes()
    if busca:
        clientes = [c for c in clientes if busca.lower() in c[1].lower()]

    for cli in clientes:
        cid, nome, endereco, whats, pag, obs, lat, lng = cli
        visitado = ja_visitou_hoje(cid)
        cor_card = "#dcfce7" if visitado else "#ffffff"
        st.markdown(f"""
        <div style="background:{cor_card}; border:1px solid #e5e7eb; border-radius:14px; padding:12px; margin-bottom:10px;">
            <b>{nome}</b> {'✅' if visitado else ''}<br>
            <small style="color:#666;">{endereco or 'Sem endereço'} • {whats or ''}</small>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👁️ Ver", key=f"ver_{cid}", use_container_width=True):
                st.session_state['cliente_detalhe'] = cid
                st.session_state['pagina'] = 'menu'
                st.rerun()
        with c2:
            if not visitado:
                if st.button("✔️ Visitei", key=f"vis_{cid}", use_container_width=True):
                    registrar_visita(cid, 0)
                    st.rerun()
            else:
                st.button("Visitado", key=f"vis2_{cid}", disabled=True, use_container_width=True)

    if 'cliente_detalhe' in st.session_state:
        cli = get_cliente_dict(st.session_state['cliente_detalhe'])
        if cli:
            @st.dialog(f"{cli['nome']}", width="large")
            def detalhe():
                st.write(f"📍 {cli['endereco']}")
                st.write(f"📱 {cli['whatsapp']}")
                st.write(f"💳 {cli['pagamento']}")
                st.write(f"📝 {cli['obs']}")
                if st.button("Fechar"):
                    del st.session_state['cliente_detalhe']
                    st.rerun()
            detalhe()

@st.dialog("Novo Cliente", width="large")
def modal_novo_cliente():
    st.markdown("### ➕ Novo Cliente")
    nome = st.text_input("Nome *", placeholder="Ex: Mercado do João", key="fab_nome")
    endereco = st.text_input("Endereço", placeholder="Rua, número, bairro", key="fab_end")
    whatsapp = st.text_input("WhatsApp", placeholder="(51) 99999-9999", key="fab_whats")
    pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro", "PIX", "Cartão", "Fiado", "Outro"], key="fab_pag")
    obs = st.text_area("Observações", placeholder="Ex: Entregar segunda de manhã...", key="fab_obs")

    st.divider()
    st.markdown("#### 📍 Localização no mapa")
    st.caption("Clique no mapa para marcar ou use o botão 🎯 (canto inferior direito) para ir até você.")

    m_novo = mapa_satelite([-29.942, -50.99], 15)
    if st.session_state['novo_cli_lat'] and st.session_state['novo_cli_lng']:
        adicionar_pino(m_novo, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'], 0, "Novo cliente", "green")
        st.success(f"📍 Marcado: {st.session_state['novo_cli_lat']:.5f}, {st.session_state['novo_cli_lng']:.5f}")

    map_data = st_folium(m_novo, height=350, use_container_width=True, key="mapa_novo_cli")
    if map_data and map_data['last_clicked']:
        st.session_state['novo_cli_lat'] = map_data['last_clicked']['lat']
        st.session_state['novo_cli_lng'] = map_data['last_clicked']['lng']
        st.rerun()

    if st.session_state['novo_cli_lat']:
        if st.button("❌ Remover localização"):
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
                salvar_cliente(nome, endereco, whatsapp, pagamento, obs, st.session_state['novo_cli_lat'], st.session_state['novo_cli_lng'])
                st.session_state['novo_cli_lat'] = None
                st.session_state['novo_cli_lng'] = None
                st.toast("Cliente salvo!", icon="✅")
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state['novo_cli_lat'] = None
            st.session_state['novo_cli_lng'] = None
            st.rerun()

def pagina_agenda():
    from datetime import date, timedelta, datetime
    import streamlit.components.v1 as components

    st.markdown("""
    <style>
   .dias-wrapper {
        position: sticky; top: 0; z-index: 20; background: white;
        padding: 8px 0 12px 0; margin: -10px -16px 10px -16px;
        padding-left: 16px; padding-right: 16px;
        border-bottom: 1px solid #f0f0f0;
    }
   .agenda-container { touch-action: pan-y pinch-zoom; transform-origin: top left; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📅 Agenda")

    # DIAS SEM SETAS - ARRASTÁVEL
    dias = []
    for i in range(-3, 8):
        d = date.today() + timedelta(days=i)
        dias.append(d)

    cols = st.columns(11)
    for idx, d in enumerate(dias):
        label = f"{['S','T','Q','Q','S','S','D'][d.weekday()]}\n{d.day}"
        is_active = d.isoformat() == st.session_state['data_agenda']
        with cols[idx]:
            if st.button(label, key=f"dia_{d.isoformat()}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state['data_agenda'] = d.isoformat()
                st.rerun()

    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap!important; overflow-x:auto!important; gap:8px!important; }
    div[data-testid="stHorizontalBlock"]::-webkit-scrollbar{display:none}
    div[data-testid="column"] { min-width: 56px!important; flex: 0 0 56px!important; }
    </style>
    """, unsafe_allow_html=True)

    data_sel = date.fromisoformat(st.session_state['data_agenda'])
    st.markdown(f"### {data_sel.strftime('%d/%m')} - {['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'][data_sel.weekday()]}")

    compromissos = get_compromissos(st.session_state['data_agenda'])

    st.markdown('<div class="agenda-container" id="agendaZoom">', unsafe_allow_html=True)
    if not compromissos:
        st.info("Nenhum compromisso neste dia.")
    else:
        for comp in compromissos:
            cor = CORES.get(comp['tipo'], '#f3f4f6')
            hora = comp['hora_inicio']
            fim_min = hora_para_minutos(hora) + comp['duracao']
            fim_h = f"{fim_min//60:02d}:{fim_min%60:02d}"
            st.markdown(f"""
            <div style="background:{cor}; border-radius:12px; padding:12px 14px; margin-bottom:10px; border-left:5px solid #2563eb;">
                <div style="display:flex; justify-content:space-between;">
                    <b>{hora} - {fim_h} • {comp['tipo'].upper()}</b>
                    <span style="font-size:12px;">{comp['duracao']}min</span>
                </div>
                <div style="margin-top:4px;">{comp['titulo'] or 'Sem título'}</div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                nova_hora = st.time_input("Mover", value=datetime.strptime(hora, "%H:%M").time(), key=f"mover_{comp['id']}", label_visibility="collapsed")
                if st.button("⏰ Atualizar", key=f"upd_{comp['id']}", use_container_width=True):
                    update_horario(comp['id'], nova_hora.strftime("%H:%M"))
                    st.toast("Horário atualizado!", icon="✅")
                    st.rerun()
            with c2:
                if st.button("🗑️ Excluir", key=f"del_{comp['id']}", use_container_width=True):
                    deletar_compromisso(comp['id'])
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # JS zoom pinça corrigido
    components.html("""
    <script>
    const el = window.parent.document.getElementById('agendaZoom');
    if(el){
        let scale = 1; let lastDist = 0;
        el.addEventListener('touchstart', (e)=>{
            if(e.touches.length==2){
                lastDist = Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY);
            }
        });
        el.addEventListener('touchmove', (e)=>{
            if(e.touches.length==2){
                e.preventDefault();
                const dist = Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY);
                scale += (dist - lastDist) * 0.008;
                scale = Math.min(Math.max(0.6, scale), 3);
                el.style.transform = `scale(${scale})`;
                lastDist = dist;
            }
        }, {passive:false});
    }
    </script>
    """, height=0)

    st.divider()
    if st.button("➕ Novo Compromisso", use_container_width=True, type="primary"):
        st.session_state['show_novo_comp'] = True

    if st.session_state.get('show_novo_comp'):
        @st.dialog("Novo Compromisso", width="large")
        def novo_comp():
            data = st.date_input("Data", value=data_sel)
            hora = st.time_input("Hora início", value=datetime.now().time())
            duracao = st.number_input("Duração (min)", value=60, step=15)
            tipo = st.selectbox("Tipo", list(CORES.keys()))
            titulo = st.text_input("Título")
            clientes = get_clientes()
            cli_opcoes = {f"{c[1]}": c[0] for c in clientes}
            cli_sel = st.selectbox("Cliente (opcional)", ["Nenhum"] + list(cli_opcoes.keys()))
            if st.button("Salvar", type="primary", use_container_width=True):
                cid = None if cli_sel=="Nenhum" else cli_opcoes[cli_sel]
                add_compromisso(data.isoformat(), hora.strftime("%H:%M"), duracao, tipo, cid, titulo)
                st.session_state['show_novo_comp'] = False
                st.rerun()
            if st.button("Cancelar", use_container_width=True):
                st.session_state['show_novo_comp'] = False
                st.rerun()
        novo_comp()

def pagina_mapa():
    st.markdown("## 🗺️ Mapa de Clientes")
    st.caption("🗺️ Ruas = limpo | 🛰️ Híbrido = satélite. Use 🎯 para ir até você.")

    clientes = get_clientes()
    clientes_com_loc = [c for c in clientes if c[5] and c[6]]

    if not clientes_com_loc:
        centro = [-29.942, -50.99]
    else:
        centro = [clientes_com_loc[0][5], clientes_com_loc[0][6]]

    m = mapa_hibrido(centro, 13)

    # Adiciona pinos com lógica de cores + amanhã
    from datetime import date, timedelta
    amanha = (date.today() + timedelta(days=1)).isoformat()
    comps_amanha = get_compromissos(amanha)
    ids_amanha = {c['cliente_id'] for c in comps_amanha if c['cliente_id']}

    for cli in clientes_com_loc:
        cid, nome, end, whats, pag, lat, lng = cli[0], cli[1], cli[2], cli[3], cli[4], cli[5], cli[6]
        cor = "green" if ja_visitou_hoje(cid) else "blue"
        tem_amanha = cid in ids_amanha
        adicionar_pino(m, lat, lng, cid, nome, cor, tem_amanha)

    st_folium(m, height=600, use_container_width=True, key="mapa_principal")

# --- ROTEAMENTO ---
if st.session_state['pagina'] == 'menu':
    pagina_menu()
elif st.session_state['pagina'] == 'clientes':
    pagina_clientes()
elif st.session_state['pagina'] == 'agenda':
    pagina_agenda()
elif st.session_state['pagina'] == 'mapa':
    pagina_mapa()

# FAB Novo Cliente
if st.query_params.get("novo_cliente") == "1" or st.session_state.get('fab_trigger'):
    modal_novo_cliente()

# --- BARRA INFERIOR ---
st.markdown("""
<div class="bottom-nav">
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🏠\nMenu", use_container_width=True, type="primary" if st.session_state['pagina']=='menu' else "secondary"):
        st.session_state['pagina']='menu'; st.rerun()
with c2:
    if st.button("👥\nClientes", use_container_width=True, type="primary" if st.session_state['pagina']=='clientes' else "secondary"):
        st.session_state['pagina']='clientes'; st.rerun()
with c3:
    if st.button("📅\nAgenda", use_container_width=True, type="primary" if st.session_state['pagina']=='agenda' else "secondary"):
        st.session_state['pagina']='agenda'; st.rerun()
with c4:
    if st.button("🗺️\nMapa", use_container_width=True, type="primary" if st.session_state['pagina']=='mapa' else "secondary"):
        st.session_state['pagina']='mapa'; st.rerun()

# Botão flutuante +
st.markdown("""
<style>
.fab {
    position: fixed; bottom: 85px; right: 20px; width: 60px; height: 60px;
    background: #2563eb; color: white; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 30px; box-shadow: 0 4px 15px rgba(37,99,235,0.4);
    z-index: 99; cursor: pointer; border: none;
}
</style>
""", unsafe_allow_html=True)

if st.button("＋", key="fab", help="Novo cliente"):
    modal_novo_cliente()
