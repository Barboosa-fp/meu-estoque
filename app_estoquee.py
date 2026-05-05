import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo/edit?gid=1378246990#gid=1378246990"

def carregar_dados(aba="Sheet1"):
    return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl="0")

def registrar_historico(acao, produto, qtd):
    try:
        df_hist = carregar_dados("Historico")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_PLANILHA, worksheet="Historico", data=df_hist_atualizado)
    except: pass

# --- SISTEMA DE LOGIN DINÂMICO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = ""

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    df_usuarios = carregar_dados("Logins")
    
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Verifica se o usuário e senha existem na aba Logins
        validacao = df_usuarios[(df_usuarios['Usuario'] == user_input) & (df_usuarios['Senha'].astype(str) == pass_input)]
        
        if not validacao.empty:
            st.session_state.logado = True
            st.session_state.usuario_atual = user_input
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()

# --- CARREGAMENTO DE DADOS APÓS LOGIN ---
df = carregar_dados()
df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

# Dashboard
st.title("📦 Gestão de Estoque Completa")
c1, c2, c3 = st.columns(3)
c1.metric("💰 Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
c2.metric("📦 Itens Totais", f"{df['Quantidade'].sum()} un")
c3.metric("👤 Logado como", st.session_state.usuario_atual)
st.markdown("---")

# Menu
opcoes_menu = ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"]
if st.session_state.usuario_atual == "admin":
    opcoes_menu.append("Gestão de Acessos")

menu = st.sidebar.selectbox("Menu", opcoes_menu)

# --- TELAS DO SISTEMA ---

if menu == "Ver Estoque":
    st.subheader("📋 Inventário Atual")
    busca = st.text_input("🔍 Buscar produto...").upper()
    df_f = df[df['Produto'].str.contains(busca, na=False)] if busca else df
    st.dataframe(df_f.style.apply(lambda r: ['background-color: #ffcccc']*len(r) if r['Quantidade'] < 50 else ['']*len(r), axis=1), use_container_width=True)

elif menu == "Entrada":
    with st.form("entrada"):
        nome = st.text_input("Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1)
        valor = st.number_input("Valor Unitário", min_value=0.0)
        if st.form_submit_button("Salvar"):
            idx = df[df['Produto'] == nome].index
            if not idx.empty:
                df.loc[idx, 'Quantidade'] += qtd
                df.loc[idx, 'Valor Unit'] = valor
            else:
                novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                df = pd.concat([df, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico(f"ENTRADA ({st.session_state.usuario_atual})", nome, qtd)
            st.success("Estoque Atualizado!")
            st.rerun()

elif menu == "Saída":
    prod_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
    qtd_s = st.number_input("Quantidade Saída", min_value=1)
    if st.button("Confirmar Baixa"):
        idx = df[df['Produto'] == prod_sel].index
        if df.loc[idx, 'Quantidade'].values >= qtd_s:
            df.loc[idx, 'Quantidade'] -= qtd_s
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico(f"SAÍDA ({st.session_state.usuario_atual})", prod_sel, qtd_s)
            st.warning("Saída registrada!")
            st.rerun()
        else: st.error("Estoque insuficiente!")

elif menu == "Gestão de Acessos":
    st.subheader("👥 Cadastrar Novo Usuário")
    df_logins = carregar_dados("Logins")
    
    with st.form("novo_user"):
        novo_u = st.text_input("Nome do Usuário")
        nova_s = st.text_input("Senha", type="password")
        if st.form_submit_button("Cadastrar Usuário"):
            if novo_u not in df_logins['Usuario'].values:
                novo_row = pd.DataFrame([[novo_u, nova_s]], columns=['Usuario', 'Senha'])
                df_atualizado = pd.concat([df_logins, novo_row], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="Logins", data=df_atualizado)
                st.success(f"Usuário {novo_u} cadastrado com sucesso!")
            else: st.error("Usuário já existe!")
    
    st.write("---")
    st.write("Usuários Atuais:")
    st.dataframe(df_logins[['Usuario']], use_container_width=True)

elif menu == "Histórico":
    st.subheader("📅 Log de Atividades")
    df_h = carregar_dados("Historico")
    st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)

# Demais menus (Editar/Excluir e Relatórios) permanecem iguais...
