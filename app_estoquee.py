import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

# 2. CONEXÃO E CONFIGURAÇÃO DA PLANILHA (ORDEM CORRETA)
conn = st.connection("gsheets", type=GSheetsConnection)

# Substitua apenas o ID se necessário, o link agora está no formato correto
ID_PLANILHA = "1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo"
URL_BASE = f"https://google.com{ID_PLANILHA}/edit#gid="

def carregar_dados(aba="Sheet1"):
    return conn.read(spreadsheet=URL_BASE, worksheet=aba, ttl="0")

def registrar_historico(acao, produto, qtd, usuario):
    try:
        df_hist = carregar_dados("Historico")
        nova_venda = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), acao, produto, qtd, usuario]], 
                                  columns=['Data/Hora', 'Ação', 'Produto', 'Quantidade', 'Usuário'])
        df_hist_atualizado = pd.concat([df_hist, nova_venda], ignore_index=True)
        conn.update(spreadsheet=URL_BASE, worksheet="Historico", data=df_hist_atualizado)
    except:
        st.error("Erro ao gravar histórico. Verifique a aba 'Historico'.")

# --- 3. SISTEMA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = ""

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    try:
        df_usuarios = carregar_dados("Logins")
        user_input = st.text_input("Usuário")
        pass_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Validação na planilha aba Logins
            validacao = df_usuarios[(df_usuarios['Usuario'] == user_input) & (df_usuarios['Senha'].astype(str) == pass_input)]
            
            if not validacao.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = user_input
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    except Exception as e:
        st.error("⚠️ Erro de Conexão: Verifique se a aba 'Logins' existe e se o compartilhamento está como 'Editor'.")
    st.stop()

# --- 4. SISTEMA APÓS LOGIN ---
try:
    # Carregar dados principais
    df = carregar_dados("Sheet1")
    df['Valor Unit'] = pd.to_numeric(df['Valor Unit'], errors='coerce').fillna(0)
    df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
    df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

    st.title("📦 Gestão de Estoque Online")
    
    # Dashboard Financeiro
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
    c2.metric("📦 Itens Totais", f"{int(df['Quantidade'].sum())} un")
    c3.metric("⚠️ Críticos (<50)", len(df[df['Quantidade'] < 50]))
    
    st.markdown("---")

    # Menu Lateral
    opcoes = ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"]
    if st.session_state.usuario_atual == "admin":
        opcoes.append("Gestão de Usuários")
    
    menu = st.sidebar.selectbox("Menu", opcoes)
    st.sidebar.write(f"👤 Logado: **{st.session_state.usuario_atual}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- TELAS ---
    if menu == "Ver Estoque":
        busca = st.text_input("🔍 Buscar produto...").upper()
        df_f = df[df['Produto'].str.contains(busca, na=False)] if busca else df
        # Estilo para destacar estoque baixo
        st.dataframe(df_f.style.apply(lambda r: ['background-color: #ffcccc']*len(r) if r['Quantidade'] < 50 else ['']*len(r), axis=1), use_container_width=True)

    elif menu == "Entrada":
        with st.form("entrada"):
            nome = st.text_input("Nome do Produto").upper()
            qtd = st.number_input("Quantidade", min_value=1)
            valor = st.number_input("Valor Unitário (Custo)", min_value=0.0)
            if st.form_submit_button("Salvar Entrada"):
                idx = df[df['Produto'] == nome].index
                if not idx.empty:
                    df.loc[idx, 'Quantidade'] += qtd
                    df.loc[idx, 'Valor Unit'] = valor
                else:
                    novo = pd.DataFrame([{"SKU": f"PROD-{len(df)+1:03d}", "Produto": nome, "Quantidade": qtd, "Valor Unit": valor, "NF": "-"}])
                    df = pd.concat([df, novo], ignore_index=True)
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                registrar_historico("ENTRADA", nome, qtd, st.session_state.usuario_atual)
                st.success("Estoque Atualizado!")
                st.rerun()

    elif menu == "Saída":
        prod_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
        qtd_s = st.number_input("Quantidade Saída", min_value=1)
        if st.button("Confirmar Baixa"):
            idx = df[df['Produto'] == prod_sel].index
            if df.loc[idx, 'Quantidade'].values[0] >= qtd_s:
                df.loc[idx, 'Quantidade'] -= qtd_s
                conn.update(spreadsheet=URL_BASE, worksheet="Sheet1", data=df)
                registrar_historico("SAÍDA", prod_sel, qtd_s, st.session_state.usuario_atual)
                st.warning("Saída registrada!")
                st.rerun()
            else: st.error("Estoque insuficiente!")

    elif menu == "Gestão de Usuários":
        st.subheader("👥 Controle de Acessos")
        df_users = carregar_dados("Logins")
        col1, col2 = st.columns(2)
        with col1:
            u_nome = st.text_input("Novo Usuário")
            u_pass = st.text_input("Senha", type="password")
            if st.button("Cadastrar"):
                novo_u = pd.DataFrame([[u_nome, u_pass]], columns=['Usuario', 'Senha'])
                df_up = pd.concat([df_users, novo_u], ignore_index=True)
                conn.update(spreadsheet=URL_BASE, worksheet="Logins", data=df_up)
                st.success("Usuário criado!")
                st.rerun()
        with col2:
            st.write("Usuários Atuais:")
            st.dataframe(df_users['Usuario'])

    elif menu == "Histórico":
        st.subheader("📅 Histórico de Movimentações")
        df_h = carregar_dados("Historico")
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)

    elif menu == "Relatório de Compras":
        st.subheader("🛒 Lista de Reposição (<50 un)")
        df_c = df[df['Quantidade'] < 50]
        st.dataframe(df_c[['SKU', 'Produto', 'Quantidade']])
        st.download_button("Baixar Lista CSV", df_c.to_csv(index=False), "compras.csv")

except Exception as e:
    st.error(f"Erro ao carregar sistema: {e}")

