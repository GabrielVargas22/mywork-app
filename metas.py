import sqlite3
from datetime import date, timedelta
import streamlit as st

DB = 'banco.db'

def init_metas():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visitas
                 (id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, valor REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_diaria_clientes', '15')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_diaria_vendas', '500')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_semanal_clientes', '80')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_semanal_vendas', '2500')")
    conn.commit()
    conn.close()

def get_config(chave):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE chave=?", (chave,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else "0"

def set_config(chave, valor):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?,?)", (chave, str(valor)))
    conn.commit()
    conn.close()

def registrar_visita(cliente_id, valor=0):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    existe = c.fetchone()
    if existe:
        conn.execute("UPDATE visitas SET valor=? WHERE cliente_id=? AND data=?", (valor, cliente_id, hoje))
    else:
        conn.execute("INSERT INTO visitas (cliente_id, data, valor) VALUES (?,?,?)", (cliente_id, hoje, valor))
    conn.commit()
    conn.close()

def deletar_visita_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    conn.commit()
    conn.close()

def get_visitas_hoje():
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM visitas WHERE data=?", (hoje,))
    qtd, total = c.fetchone()
    conn.close()
    return qtd or 0, total or 0

def get_visitas_semana():
    hoje = date.today()
    inicio = (hoje - timedelta(days=hoje.weekday())).isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM visitas WHERE data>=?", (inicio,))
    qtd, total = c.fetchone()
    conn.close()
    return qtd or 0, total or 0

def ja_visitou_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    r = c.fetchone()[0]
    conn.close()
    return r > 0

def get_valor_visita_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valor FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    r = c.fetchone()
    conn.close()
    return r[0] if r else 0.0

# === NOVO VISUAL COM ARRASTE ===
def tela_metas_completa():
    st.markdown("""
    <style>
   .planejar-btn button { border-radius: 12px; height: 48px; font-weight: 700; }
   .swipe-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        gap: 12px;
        padding: 8px 2px 20px 2px;
    }
   .swipe-container::-webkit-scrollbar { display: none; }
   .swipe-page {
        min-width: 100%;
        scroll-snap-align: center;
        background: #ffffff;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
    }
   .swipe-dica { text-align:center; color:#999; font-size:13px; margin: 4px 0 10px 0; }
    </style>
    """, unsafe_allow_html=True)

    # Botão Planejar em cima
    st.markdown('<div class="planejar-btn">', unsafe_allow_html=True)
    if st.button("🛠️ Planejar", use_container_width=True, type="primary"):
        st.session_state['abrir_planejar'] = not st.session_state.get('abrir_planejar', False)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('abrir_planejar'):
        st.markdown("### Configurar Metas")
        c1, c2 = st.columns(2)
        with c1:
            md_cli = st.number_input("Meta diária clientes", value=int(get_config('meta_diaria_clientes')))
            ms_cli = st.number_input("Meta semanal clientes", value=int(get_config('meta_semanal_clientes')))
        with c2:
            md_v = st.number_input("Meta diária vendas R$", value=float(get_config('meta_diaria_vendas')))
            ms_v = st.number_input("Meta semanal vendas R$", value=float(get_config('meta_semanal_vendas')))
        if st.button("Salvar metas", use_container_width=True):
            set_config('meta_diaria_clientes', md_cli)
            set_config('meta_semanal_clientes', ms_cli)
            set_config('meta_diaria_vendas', md_v)
            set_config('meta_semanal_vendas', ms_v)
            st.success("Metas salvas!")
            st.session_state['abrir_planejar'] = False
            st.rerun()

    st.markdown('<div class="swipe-dica">👉 Arraste para o lado 👉</div>', unsafe_allow_html=True)

    qtd_hoje, total_hoje = get_visitas_hoje()
    qtd_sem, total_sem = get_visitas_semana()
    meta_d_c = int(get_config('meta_diaria_clientes'))
    meta_d_v = float(get_config('meta_diaria_vendas'))
    meta_s_c = int(get_config('meta_semanal_clientes'))
    meta_s_v = float(get_config('meta_semanal_vendas'))

    # O TRUQUE DO ARRASTE
    st.markdown('<div class="swipe-container">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    # Página 1 - Diária
    with col1:
        st.markdown('<div class="swipe-page">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center;">🎯 Metas Diárias</h3>', unsafe_allow_html=True)
        st.metric("Clientes hoje", f"{qtd_hoje}/{meta_d_c}", f"{qtd_hoje - meta_d_c}")
        st.progress(min(qtd_hoje/meta_d_c if meta_d_c else 0, 1.0))
        st.metric("Vendas hoje", f"R$ {total_hoje:.2f} / R$ {meta_d_v:.2f}")
        st.progress(min(total_hoje/meta_d_v if meta_d_v else 0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)

    # Página 2 - Semanal
    with col2:
        st.markdown('<div class="swipe-page">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center;">📅 Metas Semanais</h3>', unsafe_allow_html=True)
        st.metric("Clientes semana", f"{qtd_sem}/{meta_s_c}", f"{qtd_sem - meta_s_c}")
        st.progress(min(qtd_sem/meta_s_c if meta_s_c else 0, 1.0))
        st.metric("Vendas semana", f"R$ {total_sem:.2f} / R$ {meta_s_v:.2f}")
        st.progress(min(total_sem/meta_s_v if meta_s_v else 0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
