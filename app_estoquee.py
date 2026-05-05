import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

# 2. CONEXÃO E CONFIGURAÇÃO DA PLANILHA
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
    except:
        pass

# --- 3. CARREGAMENTO E EXIBIÇÃO DO SISTEMA ---
try:
    df = carregar_dados("Sheet1")
    
    # Garantir que valores sejam numéricos para cálculos
    df['Valor Unit'] = pd.to_numeric(df['Valor Unit'], errors='coerce').fillna(0)
    df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
    df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

    st.title("📦 Gestão de Estoque Online")
    
    # Dashboard Financeiro no Topo
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
    c2.metric("📦 Itens Totais", f"{int(df['Quantidade'].sum())} un")
    c3.metric("⚠️ Críticos (<50)", len(df[df['Quantidade'] < 50]))
    
    st.markdown("---")

    # Menu Lateral
    menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"])

    if menu == "Ver Estoque":
        st.subheader("📋 Inventário Atual")
        busca = st.text_input("🔍 Buscar produto...").upper()
        df_f = df[df['Produto'].str.contains(busca, na=False)] if busca else df
        st.dataframe(df_f.style.apply(lambda r: ['background-color: #ffcccc']*len(r) if r['Quantidade'] < 50 else ['']*len(r), axis=1), use_container_width=True)

    elif menu == "Entrada":
        st.subheader("➕ Registrar Entrada")
        with st.form("entrada"):
            nome = st.text_input("Nome do Produto").upper()
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            valor = st.number_input("Valor Unitário", min_value=0.0)
            if st.form_submit_button("Salvar Entrada"):
                idx = df[df['Produto'] == nome].index
                if not idx.empty:
                    df.loc[idx, 'Quantidade'] += qtd
                    df.loc[idx, 'Valor Unit'] = valor
                else:
                    novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                    df = pd.concat([df, novo], ignore_index=True)
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                registrar_historico("ENTRADA", nome, qtd)
                st.success(f"Estoque de {nome} atualizado!")
                st.rerun()

    elif menu == "Saída":
        st.subheader("➖ Registrar Saída")
        prod_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
        qtd_s = st.number_input("Quantidade Saída", min_value=1, step=1)
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == prod_sel].index
            if df.loc[idx, 'Quantidade'].values >= qtd_s:
                df.loc[idx, 'Quantidade'] -= qtd_s
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                registrar_historico("SAÍDA", prod_sel, qtd_s)
                st.warning(f"Saída de {prod_sel} registrada!")
                st.rerun()
            else: st.error("Estoque insuficiente!")

    elif menu == "Editar/Excluir":
        st.subheader("🛠️ Editar ou Remover Produto")
        prod_edit = st.selectbox("Selecione o Produto", df['Produto'].unique())
        dados_prod = df[df['Produto'] == prod_edit]
        if not dados_prod.empty:
            col1, col2 = st.columns(2)
            with col1:
                novo_n = st.text_input("Novo Nome", value=prod_edit)
                nova_q = st.number_input("Nova Qtd", value=int(dados_prod['Quantidade'].values))
                if st.button("Salvar Alterações"):
                    df.loc[df['Produto'] == prod_edit, ['Produto', 'Quantidade']] = [novo_n.upper(), nova_q]
                    conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                    st.success("Produto editado!")
                    st.rerun()
            with col2:
                if st.button("🗑️ EXCLUIR PRODUTO", type="primary"):
                    df = df[df['Produto'] != prod_edit]
                    conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                    st.rerun()

    elif menu == "Histórico":
        st.subheader("📅 Log de Atividades")
        df_h = carregar_dados("Historico")
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)

    elif menu == "Relatório de Compras":
        st.subheader("🛒 Itens Necessitando Reposição")
        df_c = df[df['Quantidade'] < 50]
        if not df_c.empty:
            st.dataframe(df_c[['SKU', 'Produto', 'Quantidade']], use_container_width=True)
            st.download_button("Baixar Lista CSV", df_c.to_csv(index=False), "compras.csv")
        else:
            st.success("Nenhum item abaixo de 50 unidades.")

except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
