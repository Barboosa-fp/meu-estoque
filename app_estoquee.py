import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
  https://docs.google.com/spreadsheets/d/1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo/edit?gid=0#gid=0
    url = "SEU_LINK_DA_PLANILHA_AQUI"
    return conn.read(spreadsheet=url, ttl="0")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login Administrativo")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- SISTEMA ---
df = carregar_dados()
st.title("📦 Controle de Estoque Online")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída"])

if menu == "Ver Estoque":
    st.subheader("Planilha em Tempo Real")
    st.dataframe(df, use_container_width=True)

elif menu == "Entrada":
    st.subheader("➕ Nova Entrada")
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        valor = st.number_input("Valor Unitário", min_value=0.0)
        nf = st.text_input("Nota Fiscal")
        btn = st.form_submit_button("Salvar na Planilha")
        
        if btn:
            # Lógica para adicionar nova linha
            novo_sku = f"PROD-{len(df) + 1:03d}"
            nova_linha = pd.DataFrame([[novo_sku, nome, qtd, valor, nf]], columns=df.columns)
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            
            # Atualiza no Google Sheets
            conn.update(spreadsheet="SEU_LINK_DA_PLANILHA_AQUI", data=df_atualizado)
            st.success(f"Produto {nome} salvo com sucesso!")
            st.balloons()

elif menu == "Saída":
    st.subheader("➖ Dar Saída")
    if not df.empty:
        produto_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1)
        
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == produto_sel].index
            if df.loc[idx, 'Quantidade'].values[0] >= qtd_saida:
                df.loc[idx, 'Quantidade'] -= qtd_saida
                conn.update(spreadsheet="SEU_LINK_DA_PLANILHA_AQUI", data=df)
                st.warning(f"Saída de {qtd_saida} unidades de {produto_sel} realizada!")
            else:
                st.error("Erro: Estoque insuficiente!")
