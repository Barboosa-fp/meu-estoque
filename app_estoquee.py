import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- LINK CORRIGIDO PARA EVITAR HTTP ERROR ---
ID_PLANILHA = "1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo"
URL_PLANILHA = f"https://google.com{ID_PLANILHA}/export?format=csv"
URL_EDIT = f"https://google.com{ID_PLANILHA}/edit#gid=0"

def carregar_dados():
    # Usamos o link de exportação para leitura estável
    return pd.read_csv(URL_PLANILHA)

def registrar_historico(acao, produto, qtd):
    try:
        # Para gravar, ainda usamos a conexão gsheets original
        df_hist = conn.read(spreadsheet=URL_EDIT, worksheet="Historico", ttl="0")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_EDIT, worksheet="Historico", data=df_hist_atualizado)
    except: pass

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

# Limpeza e Cálculos Financeiros
df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
df['Valor Unit'] = pd.to_numeric(df['Valor Unit'], errors='coerce').fillna(0)
df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

st.title("📦 Gestão de Estoque Completa")

# --- DASHBOARD FINANCEIRO ---
c1, c2, c3 = st.columns(3)
c1.metric("💰 Valor Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
c2.metric("📦 Total de Itens", f"{int(df['Quantidade'].sum())} un")
c3.metric("⚠️ Críticos (<50)", len(df[df['Quantidade'] < 50]))

st.markdown("---")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Gráfico Financeiro", "Histórico"])

if menu == "Ver Estoque":
    st.subheader("📋 Inventário Atual")
    busca = st.text_input("🔍 Buscar...").upper()
    df_f = df[df['Produto'].astype(str).str.contains(busca, na=False)] if busca else df
    st.dataframe(df_f.style.apply(lambda r: ['background-color: #ffcccc']*len(r) if r['Quantidade'] < 50 else ['']*len(r), axis=1), use_container_width=True)

elif menu == "Gráfico Financeiro":
    st.subheader("🍕 Distribuição do Investimento")
    if df['Valor Total'].sum() > 0:
        fig, ax = plt.subplots()
        # Filtra apenas itens com valor para o gráfico não ficar poluído
        df_plot = df[df['Valor Total'] > 0]
        ax.pie(df_plot['Valor Total'], labels=df_plot['Produto'], autopct='%1.1f%%', startangle=90)
        ax.axis('equal') 
        st.pyplot(fig)
    else:
        st.info("Adicione valores unitários aos produtos para ver o gráfico.")

elif menu == "Entrada":
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        valor = st.number_input("Valor Unitário", min_value=0.0)
        if st.form_submit_button("Salvar"):
            # Atualiza o DF localmente primeiro
            idx = df[df['Produto'] == nome].index
            if not idx.empty:
                df.loc[idx, 'Quantidade'] += qtd
                df.loc[idx, 'Valor Unit'] = valor
            else:
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                df = pd.concat([df, novo], ignore_index=True)
            
            # Salva na planilha principal (Sheet1)
            conn.update(spreadsheet=URL_EDIT, worksheet="Sheet1", data=df.drop(columns=['Valor Total']))
            registrar_historico("ENTRADA", nome, qtd)
            st.success("Atualizado!")
            st.rerun()
# (Os menus de Saída e Histórico seguem a mesma lógica de atualização usando URL_EDIT)
