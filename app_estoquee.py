import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
ID_PLANILHA = "1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo"
URL_BASE = f"https://google.com{ID_PLANILHA}/edit#gid="

def carregar_dados(aba="Sheet1"):
    return conn.read(spreadsheet=URL_BASE, worksheet=aba, ttl="0")

def registrar_historico(acao, produto, qtd):
    try:
        df_hist = carregar_dados("Historico")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_BASE, worksheet="Historico", data=df_hist_atualizado)
    except: pass

# --- SISTEMA DIRETO (SEM LOGIN) ---
try:
    df = carregar_dados("Sheet1")
    st.title("📦 Gestão de Estoque Online")
    
    # Resumo rápido
    c1, c2 = st.columns(2)
    c1.metric("📦 Itens Totais", f"{int(pd.to_numeric(df['Quantidade'], errors='coerce').sum())} un")
    c2.metric("⚠️ Críticos (<50)", len(df[pd.to_numeric(df['Quantidade'], errors='coerce') < 50]))
    
    st.markdown("---")
    menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico"])

    if menu == "Ver Estoque":
        st.subheader("📋 Inventário")
        busca = st.text_input("🔍 Buscar...").upper()
        df_f = df[df['Produto'].str.contains(busca, na=False)] if busca else df
        st.dataframe(df_f, use_container_width=True)

    elif menu == "Entrada":
        with st.form("entrada"):
            nome = st.text_input("Produto").upper()
            qtd = st.number_input("Quantidade", min_value=1)
            if st.form_submit_button("Salvar"):
                idx = df[df['Produto'] == nome].index
                if not idx.empty:
                    df.loc[idx, 'Quantidade'] = pd.to_numeric(df.loc[idx, 'Quantidade']) + qtd
                else:
                    novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": 0, "NF": "-"}])
                    df = pd.concat([df, novo], ignore_index=True)
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                registrar_historico("ENTRADA", nome, qtd)
                st.success("Atualizado!")
                st.rerun()

    elif menu == "Saída":
        sel = st.selectbox("Produto", df['Produto'].unique())
        qtd_s = st.number_input("Qtd", min_value=1)
        if st.button("Baixar"):
            idx = df[df['Produto'] == sel].index
            df.loc[idx, 'Quantidade'] = pd.to_numeric(df.loc[idx, 'Quantidade']) - qtd_s
            conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
            registrar_historico("SAÍDA", sel, qtd_s)
            st.rerun()

    elif menu == "Histórico":
        st.dataframe(carregar_dados("Historico").sort_index(ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao conectar: {e}. Verifique se a aba principal se chama 'Sheet1' e se o link está como 'Editor'.")
