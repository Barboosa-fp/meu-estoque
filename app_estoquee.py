import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    url = "https://google.com"
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
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()

# --- SISTEMA ---
df = carregar_dados()
url_planilha = "https://google.com"

st.title("📦 Controle de Estoque Online")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída"])

if menu == "Ver Estoque":
    st.subheader("📋 Inventário em Tempo Real")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("A planilha está vazia ou não foi encontrada.")

elif menu == "Entrada":
    st.subheader("➕ Registrar Nova Entrada")
    with st.form("form_entrada"):
        nome = st.text_input("Nome do Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        valor = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
        nf = st.text_input("Número da NF")
        btn_salvar = st.form_submit_button("Salvar na Planilha")
        
        if btn_salvar:
            if nome != "":
                # Criar nova linha
                novo_sku = f"PROD-{len(df) + 1:03d}"
                nova_linha = pd.DataFrame([[novo_sku, nome, qtd, valor, nf]], columns=df.columns)
                df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
                
                # Atualizar Google Sheets
                conn.update(spreadsheet=url_planilha, data=df_atualizado)
                st.success(f"Sucesso! {nome} foi adicionado.")
                st.balloons()
            else:
                st.error("Por favor, digite o nome do produto.")

elif menu == "Saída":
    st.subheader("➖ Registrar Saída")
    if not df.empty:
        produto_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
        
        if st.button("Confirmar Baixa"):
            # Encontrar índice do produto
            idx = df[df['Produto'] == produto_sel].index
            if df.loc[idx, 'Quantidade'].values[0] >= qtd_saida:
                df.loc[idx, 'Quantidade'] -= qtd_saida
                
                # Atualizar Google Sheets
                conn.update(spreadsheet=url_planilha, data=df)
                st.warning(f"Saída de {qtd_saida} unidades de {produto_sel} realizada!")
            else:
                st.error("Erro: Estoque insuficiente para essa saída.")
    else:
        st.error("Não há produtos cadastrados para dar saída.")
