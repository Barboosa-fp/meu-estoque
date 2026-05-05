import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
# --- COLOQUE SEU LINK ABAIXO ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo/edit?gid=1378246990#gid=1378246990"

def carregar_dados():
    return conn.read(spreadsheet=URL_PLANILHA, ttl="0")

def registrar_historico(acao, produto, qtd):
    try:
        df_hist = conn.read(spreadsheet=URL_PLANILHA, worksheet="Historico", ttl="0")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_PLANILHA, worksheet="Historico", data=df_hist_atualizado)
    except:
        st.error("Aviso: Aba 'Historico' não encontrada na planilha. Crie uma aba com o nome 'Historico'.")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- SISTEMA ---
df = carregar_dados()
st.title("📦 Gestão de Estoque Completa")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico"])

if menu == "Ver Estoque":
    st.subheader("📋 Inventário Atual")
    st.dataframe(df, use_container_width=True)

elif menu == "Entrada":
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        btn = st.form_submit_button("Salvar")
        if btn:
            idx = df[df['Produto'] == nome].index
            if not idx.empty:
                df.loc[idx, 'Quantidade'] += qtd
            else:
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": 0, "NF": "-"}])
                df = pd.concat([df, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico("ENTRADA", nome, qtd)
            st.success("Estoque Atualizado!")
            st.rerun()

elif menu == "Saída":
    if not df.empty:
        produto_sel = st.selectbox("Produto", df['Produto'].unique())
        qtd_s = st.number_input("Quantidade Saída", min_value=1)
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == produto_sel].index
            if df.loc[idx, 'Quantidade'].values[0] >= qtd_s:
                df.loc[idx, 'Quantidade'] -= qtd_s
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                registrar_historico("SAÍDA", produto_sel, qtd_s)
                st.warning("Saída registrada!")
                st.rerun()
            else:
                st.error("Estoque insuficiente!")
    else:
        st.info("Nenhum produto cadastrado.")

elif menu == "Editar/Excluir":
    st.subheader("🛠️ Gerenciar Produtos")
    if not df.empty:
        prod_edit = st.selectbox("Selecione o Produto", df['Produto'].unique())
        
        # Correção do Erro de Index (Linha 83)
        dados_prod = df[df['Produto'] == prod_edit]
        if not dados_prod.empty:
            valor_qtd = int(dados_prod['Quantidade'].values[0])
            
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Novo Nome", value=prod_edit)
                nova_qtd = st.number_input("Nova Quantidade", value=valor_qtd)
                if st.button("Salvar Edição"):
                    idx = df[df['Produto'] == prod_edit].index
                    df.loc[idx, ['Produto', 'Quantidade']] = [novo_nome.upper(), nova_qtd]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.success("Alterado com sucesso!")
                    st.rerun()

            with col2:
                st.write("Cuidado: Ação definitiva.")
                if st.button("🗑️ EXCLUIR", type="primary"):
                    df = df[df['Produto'] != prod_edit]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.error(f"{prod_edit} excluído.")
                    st.rerun()
    else:
        st.info("Estoque vazio.")

elif menu == "Histórico":
    st.subheader("📅 Log de Atividades")
    try:
        df_h = conn.read(spreadsheet=URL_PLANILHA, worksheet="Historico", ttl="0")
        st.dataframe(df_h.tail(20), use_container_width=True)
    except:
        st.error("Crie uma aba chamada 'Historico' na sua planilha.")
