import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- COLOQUE APENAS A ID DA PLANILHA AQUI ---
ID_PLANILHA = "1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo"
URL_BASE = f"https://google.com{ID_PLANILHA}/edit#gid="

def carregar_dados(aba="Sheet1"):
    # Se sua aba principal tiver outro nome (ex: 'Página1'), mude 'Sheet1' acima
    return conn.read(spreadsheet=URL_BASE, worksheet=aba, ttl="0")

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    try:
        df_usuarios = carregar_dados("Logins")
        user_i = st.text_input("Usuário")
        pass_i = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            validacao = df_usuarios[(df_usuarios['Usuario'] == user_i) & (df_usuarios['Senha'].astype(str) == pass_i)]
            if not validacao.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = user_i
                st.rerun()
            else: st.error("Usuário ou senha incorretos")
    except:
        st.error("Erro técnico: Verifique se a aba 'Logins' existe e se o compartilhamento está como 'Editor'.")
    st.stop()

# --- SISTEMA APÓS LOGIN ---
df = carregar_dados("Sheet1") # Mude para o nome da sua aba principal se necessário
st.title("📦 Gestão de Estoque")
st.write(f"Usuário: {st.session_state.usuario_atual}")

# Adicione aqui o restante do código (Menus, Entradas, Saídas...)
