import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo/edit?gid=0#gid=0"

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
        st.error("Aviso: Aba 'Historico' não encontrada.")

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

# Cálculo Financeiro
df['Valor Total'] = df['Quantidade'] * df['Valor Unit']
total_investido = df['Valor Total'].sum()
total_itens = df['Quantidade'].sum()
itens_criticos = len(df[df['Quantidade'] < 50])

st.title("📦 Gestão de Estoque Completa")

# --- DASHBOARD FINANCEIRO ---
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.metric("💰 Total Investido", f"R$ {total_investido:,.2f}")
with col_f2:
    st.metric("📦 Itens em Estoque", f"{total_itens} un")
with col_f3:
    st.metric("⚠️ Alertas Críticos", f"{itens_criticos} prod", delta_color="inverse")

st.markdown("---")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"])

if menu == "Ver Estoque":
    st.subheader("📋 Inventário Atual")
    busca = st.text_input("🔍 Buscar produto...").upper()
    df_filtrado = df[df['Produto'].str.contains(busca, na=False)] if busca else df
        
    def destacar_estoque_baixo(row):
        color = 'background-color: #ffcccc' if row['Quantidade'] < 50 else ''
        return [color] * len(row)

    if not df_filtrado.empty:
        st.dataframe(df_filtrado.style.apply(destacar_estoque_baixo, axis=1), use_container_width=True)
        st.info("💡 Linhas em vermelho: Estoque abaixo de 50 unidades.")

elif menu == "Entrada":
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        valor = st.number_input("Preço de Custo (Unidade)", min_value=0.0)
        btn = st.form_submit_button("Salvar")
        if btn:
            idx = df[df['Produto'] == nome].index
            if not idx.empty:
                df.loc[idx, 'Quantidade'] += qtd
                df.loc[idx, 'Valor Unit'] = valor
            else:
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                df = pd.concat([df, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico("ENTRADA", nome, qtd)
            st.success("Estoque Atualizado!")
            st.rerun()

elif menu == "Saída":
    if not df.empty:
        busca_saida = st.text_input("🔍 Filtrar para saída...").upper()
        prod_opcoes = [p for p in df['Produto'].unique() if busca_saida in p] if busca_saida else df['Produto'].unique()
        produto_sel = st.selectbox("Selecione o Produto", prod_opcoes)
        qtd_s = st.number_input("Quantidade Saída", min_value=1)
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == produto_sel].index
            if df.loc[idx, 'Quantidade'].values >= qtd_s:
                df.loc[idx, 'Quantidade'] -= qtd_s
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                registrar_historico("SAÍDA", produto_sel, qtd_s)
                st.warning("Saída registrada!")
                st.rerun()
            else: st.error("Estoque insuficiente!")

elif menu == "Editar/Excluir":
    if not df.empty:
        prod_edit = st.selectbox("Selecione o Produto", df['Produto'].unique())
        dados_prod = df[df['Produto'] == prod_edit]
        if not dados_prod.empty:
            col1, col2 = st.columns(2)
            with col1:
                novo_n = st.text_input("Novo Nome", value=prod_edit)
                nova_q = st.number_input("Nova Qtd", value=int(dados_prod['Quantidade'].values))
                novo_v = st.number_input("Novo Valor Unit", value=float(dados_prod['Valor Unit'].values))
                if st.button("Salvar Edição"):
                    df.loc[df['Produto'] == prod_edit, ['Produto', 'Quantidade', 'Valor Unit']] = [novo_n.upper(), nova_q, novo_v]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.success("Alterado!")
                    st.rerun()
            with col2:
                if st.button("🗑️ EXCLUIR", type="primary"):
                    df = df[df['Produto'] != prod_edit]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.rerun()

elif menu == "Histórico":
    st.subheader("📅 Log de Atividades")
    try:
        df_h = conn.read(spreadsheet=URL_PLANILHA, worksheet="Historico", ttl="0")
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)
    except: st.error("Aba 'Historico' necessária.")

elif menu == "Relatório de Compras":
    st.subheader("🛒 Itens para Reposição")
    df_compras = df[df['Quantidade'] < 50]
    if not df_compras.empty:
        st.warning(f"Existem {len(df_compras)} itens com estoque baixo!")
        st.dataframe(df_compras[['SKU', 'Produto', 'Quantidade']], use_container_width=True)
        csv = df_compras.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Lista de Compras (.CSV)", csv, "lista_compras.csv", "text/csv")
    else:
        st.success("Tudo em ordem!")
