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

try:
    df = carregar_dados("Sheet1")
    
    # Padroniza os nomes das colunas para evitar erros de maiúsculo/minúsculo
    df.columns = [c.strip() for c in df.columns]

    st.title("📦 Gestão de Estoque Online")
    
    # Dashboard com trava de erro para colunas ausentes
    c1, c2 = st.columns(2)
    if 'Quantidade' in df.columns:
        qtd_total = pd.to_numeric(df['Quantidade'], errors='coerce').sum()
        c1.metric("📦 Itens Totais", f"{int(qtd_total)} un")
        c2.metric("⚠️ Críticos (<50)", len(df[pd.to_numeric(df['Quantidade'], errors='coerce') < 50]))
    else:
        st.error("Erro: A coluna 'Quantidade' não foi encontrada na planilha.")

    st.markdown("---")
    menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico"])

    if menu == "Ver Estoque":
        st.subheader("📋 Inventário")
        busca = st.text_input("🔍 Buscar...").upper()
        if 'Produto' in df.columns:
            df_f = df[df['Produto'].astype(str).str.contains(busca, na=False)] if busca else df
            st.dataframe(df_f, use_container_width=True)
        else:
            st.dataframe(df)

    elif menu == "Entrada":
        with st.form("entrada"):
            nome = st.text_input("Produto").upper()
            qtd = st.number_input("Quantidade", min_value=1)
            if st.form_submit_button("Salvar"):
                # Lógica simples de inserção
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": 0, "NF": "-"}])
                df_novo = pd.concat([df, novo], ignore_index=True)
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df_novo)
                st.success("Salvo com sucesso!")
                st.rerun()

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
