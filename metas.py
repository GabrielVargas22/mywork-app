import streamlit as st

def tela_metas():
    # CSS pro efeito de arrastar pro lado
    st.markdown("""
    <style>
    .metas-wrapper {
        overflow-x: auto;
        display: flex;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
        gap: 16px;
        padding-bottom: 10px;
    }
    .metas-wrapper::-webkit-scrollbar { display: none; }
    .meta-page {
        min-width: 100%;
        scroll-snap-align: start;
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .titulo-meta {
        text-align: center;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 12px;
    }
    .dica-arraste {
        text-align: center;
        font-size: 12px;
        color: #888;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # BOTÃO PLANEJAR EM CIMA
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("📋 Planejar", use_container_width=True, type="primary"):
            st.session_state['mostrar_config_metas'] = True

    if st.session_state.get('mostrar_config_metas'):
        st.info("Aqui vai sua tela de configuração de metas")
        if st.button("Fechar"):
            st.session_state['mostrar_config_metas'] = False
            st.rerun()

    st.markdown('<div class="dica-arraste">👉 Arraste para o lado para trocar</div>', unsafe_allow_html=True)

    # CONTAINER DESLIZÁVEL
    st.markdown("""
    <div class="metas-wrapper" id="metasWrapper">
        <div class="meta-page">
            <div class="titulo-meta">🎯 Metas Diárias</div>
    """, unsafe_allow_html=True)

    # --- CONTEÚDO DIÁRIA (seu código antigo de diária entra aqui) ---
    # Exemplo:
    st.metric("Vendas Hoje", f"R$ {st.session_state.get('venda_hoje', 0)}")
    st.progress(50)
    
    st.markdown("</div><div class='meta-page'><div class='titulo-meta'>📅 Metas Semanais</div>", unsafe_allow_html=True)
    
    # --- CONTEÚDO SEMANAL (seu código antigo de semanal entra aqui) ---
    st.metric("Vendas Semana", f"R$ {st.session_state.get('venda_semana', 0)}")
    st.progress(70)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # JS pra mudar o título quando arrasta (opcional)
    st.markdown("""
    <script>
    const wrapper = document.getElementById('metasWrapper');
    </script>
    """, unsafe_allow_html=True)
