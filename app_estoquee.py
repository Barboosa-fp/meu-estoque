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
st.title("📦 Gestão de Estoque Completa")

menu = st.sidebar.selectbox("Menu", ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico"])

if menu == "Ver Estoque":
    st.subheader("📋 Inventário Atual")
    
    busca = st.text_input("🔍 Buscar produto pelo nome...").upper()
    df_filtrado = df[df['Produto'].str.contains(busca, na=False)] if busca else df
        
    # --- FUNÇÃO DE ALERTA VISUAL (< 50 UNIDADES) ---
    def destacar_estoque_baixo(row):
        color = 'background-color: #ffcccc' if row['Quantidade'] < 50 else ''
        return [color] * len(row)

    if not df_filtrado.empty:
        st.dataframe(df_filtrado.style.apply(destarcar_estoque_baixo, axis=1), use_container_width=True)
        st.info("💡 Linhas em vermelho indicam estoque abaixo de 50 unidades.")
    else:
        st.info("Nenhum produto encontrado.")

elif menu == "Entrada":
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        btn = st.form_submit_button("Salvar")
        if btn:
            idx = df[df['Produto'] == nome].index
            if not idx.empty:
                df.loc[idx, 'Quantidade'] += qtd
            else:
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": 0, "NF": "-"}])
                df = pd.concat([df, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico("ENTRADA", nome, qtd)
            st.success("Estoque Atualizado!")
            st.rerun()

elif menu == "Saída":
    if not df.empty:
        busca_saida = st.text_input("🔍 Filtrar produto para saída...").upper()
        produtos_opcoes = df['Produto'].unique()
        if busca_saida:
            produtos_opcoes = [p for p in produtos_opcoes if busca_saida in p]
            
        produto_sel = st.selectbox("Selecione o Produto", produtos_opcoes)
        qtd_s = st.number_input("Quantidade Saída", min_value=1)
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == produto_sel].index
            if df.loc[idx, 'Quantidade'].values >= qtd_s:
                df.loc[idx, 'Quantidade'] -= qtd_s
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                registrar_historico("SAÍDA", produto_sel, qtd_s)
                st.warning("Saída registrada!")
                st.rerun()
            else:
                st.error("Estoque insuficiente!")
    else:
        st.info("Nenhum produto cadastrado.")

elif menu == "Editar/Excluir":
    st.subheader("🛠️ Gerenciar Produtos")
    if not df.empty:
        busca_edit = st.text_input("🔍 Filtrar produto para editar...").upper()
        prod_opcoes = df['Produto'].unique()
        if busca_edit:
            prod_opcoes = [p for p in prod_opcoes if busca_edit in p]
            
        prod_edit = st.selectbox("Selecione o Produto", prod_opcoes)
        dados_prod = df[df['Produto'] == prod_edit]
        
        if not dados_prod.empty:
            valor_qtd = int(dados_prod['Quantidade'].values)
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Novo Nome", value=prod_edit)
                nova_qtd = st.number_input("Nova Quantidade", value=valor_qtd)
                if st.button("Salvar Edição"):
                    idx = df[df['Produto'] == prod_edit].index
                    df.loc[idx, ['Produto', 'Quantidade']] = [novo_nome.upper(), nova_qtd]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.success("Alterado!")
                    st.rerun()
            with col2:
                if st.button("🗑️ EXCLUIR", type="primary"):
                    df = df[df['Produto'] != prod_edit]
                    conn.update(spreadsheet=URL_PLANILHA, data=df)
                    st.error(f"{prod_edit} removido.")
                    st.rerun()

elif menu == "Histórico":
    st.subheader("📅 Log de Atividades")
    try:
        df_h = conn.read(spreadsheet=URL_PLANILHA, worksheet="Historico", ttl="0")
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)
    except:
        st.error("Aba 'Historico' necessária.")
