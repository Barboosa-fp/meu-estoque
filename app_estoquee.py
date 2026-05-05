import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

# 2. CONEXÃO E LINK DA PLANILHA (AJUSTADO)
conn = st.connection("gsheets", type=GSheetsConnection)
# Substitua o ID abaixo pelo seu ID da planilha se for diferente
ID_PLANILHA = "1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo"
URL_PLANILHA = f"https://google.com{ID_PLANILHA}/edit#gid=0"

def carregar_dados(aba="Sheet1"):
    return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl="0")

def registrar_historico(acao, produto, qtd):
    try:
        df_hist = carregar_dados("Historico")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_PLANILHA, worksheet="Historico", data=df_hist_atualizado)
    except:
        pass

# --- 3. CARREGAMENTO E DASHBOARD ---
try:
    # Lendo a aba principal (Certifique-se que o nome é Sheet1)
    df = carregar_dados("Sheet1")
    
    # Garantindo que os dados são números para não dar erro no cálculo
    df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
    df['Valor Unit'] = pd.to_numeric(df['Valor Unit'], errors='coerce').fillna(0)
    df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

    st.title("📦 Gestão de Estoque Completa")

    # Dashboard Financeiro
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("💰 Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
    col_f2.metric("📦 Itens em Estoque", f"{int(df['Quantidade'].sum())} un")
    col_f3.metric("⚠️ Alertas Críticos (<50)", len(df[df['Quantidade'] < 50]))

    st.markdown("---")

    # Menu Lateral
    menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"])

    if menu == "Ver Estoque":
        st.subheader("📋 Inventário Atual")
        busca = st.text_input("🔍 Buscar produto...").upper()
        df_filtrado = df[df['Produto'].astype(str).str.contains(busca, na=False)] if busca else df
        
        def destacar_baixo(row):
            return ['background-color: #ffcccc'] * len(row) if row['Quantidade'] < 50 else [''] * len(row)

        st.dataframe(df_filtrado.style.apply(destacar_baixo, axis=1), use_container_width=True)

    elif menu == "Entrada":
        with st.form("entrada"):
            nome = st.text_input("Produto").upper()
            qtd = st.number_input("Quantidade", min_value=1)
            valor = st.number_input("Preço de Custo (Unidade)", min_value=0.0)
            if st.form_submit_button("Salvar"):
                idx = df[df['Produto'] == nome].index
                if not idx.empty:
                    df.loc[idx, 'Quantidade'] += qtd
                    df.loc[idx, 'Valor Unit'] = valor
                else:
                    novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                    df = pd.concat([df, novo], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="Sheet1", data=df)
                registrar_historico("ENTRADA", nome, qtd)
                st.success("Estoque Atualizado!")
                st.rerun()

    elif menu == "Saída":
        if not df.empty:
            prod_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
            qtd_s = st.number_input("Quantidade Saída", min_value=1)
            if st.button("Confirmar Baixa"):
                idx = df[df['Produto'] == prod_sel].index
                if df.loc[idx, 'Quantidade'].values >= qtd_s:
                    df.loc[idx, 'Quantidade'] -= qtd_s
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="Sheet1", data=df)
                    registrar_historico("SAÍDA", prod_sel, qtd_s)
                    st.warning("Saída registrada!")
                    st.rerun()
                else: st.error("Estoque insuficiente!")

    elif menu == "Editar/Excluir":
        prod_edit = st.selectbox("Selecione o Produto", df['Produto'].unique())
        dados_prod = df[df['Produto'] == prod_edit]
        if not dados_prod.empty:
            col1, col2 = st.columns(2)
            with col1:
                novo_n = st.text_input("Novo Nome", value=prod_edit)
                nova_q = st.number_input("Nova Qtd", value=int(dados_prod['Quantidade'].values[0]))
                if st.button("Salvar Edição"):
                    df.loc[df['Produto'] == prod_edit, ['Produto', 'Quantidade']] = [novo_n.upper(), nova_q]
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="Sheet1", data=df)
                    st.rerun()
            with col2:
                if st.button("🗑️ EXCLUIR", type="primary"):
                    df = df[df['Produto'] != prod_edit]
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="Sheet1", data=df)
                    st.rerun()

    elif menu == "Histórico":
        st.dataframe(carregar_dados("Historico").sort_index(ascending=False), use_container_width=True)

    elif menu == "Relatório de Compras":
        df_compras = df[df['Quantidade'] < 50]
        st.dataframe(df_compras[['SKU', 'Produto', 'Quantidade']], use_container_width=True)
        st.download_button("Baixar Lista CSV", df_compras.to_csv(index=False), "compras.csv")

except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("Dica: Verifique se a aba principal se chama 'Sheet1' e se o link no Google está como 'Editor'.")
