import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURAÇÃO DA PLANILHA ---
URL_BASE = f"https://google.com{ID_PLANILHA}/edit#gid="
# CORREÇÃO AQUI: Adicionado /://google.com
URL_BASE = f"https://://google.com{ID_PLANILHA}/edit#gid="

def carregar_dados(aba="Sheet1"):
    return conn.read(spreadsheet=URL_BASE, worksheet=aba, ttl="0")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    try:
        # Tenta ler a aba 'Logins'
        df_usuarios = carregar_dados("Logins")
        user_i = st.text_input("Usuário")
        pass_i = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Valida na planilha
            validacao = df_usuarios[(df_usuarios['Usuario'] == user_i) & (df_usuarios['Senha'].astype(str) == pass_i)]
            if not validacao.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = user_i
                st.rerun()
            else: 
                st.error("Usuário ou senha incorretos")
    except Exception as e:
        st.error("⚠️ Erro de Conexão: Verifique se a aba 'Logins' existe, se o link está como 'Editor' e se os títulos são 'Usuario' e 'Senha'.")
    st.stop()

# --- SISTEMA APÓS LOGIN ---
try:
    df = carregar_dados("Sheet1") # Verifique se sua aba principal chama 'Sheet1'
    st.title("📦 Gestão de Estoque")
    st.sidebar.write(f"👤 Usuário: {st.session_state.usuario_atual}")
    
    # Aqui você continua com os menus de Entrada, Saída, etc.
    st.success("Conectado com sucesso à base de dados!")
    st.dataframe(df)

except:
    st.error("Erro ao carregar aba principal 'Sheet1'. Verifique o nome da aba na sua planilha.")
