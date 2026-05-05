import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Estoque Nuvem Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1lJFMSmzV213au5Xw4qtnxX3LjeEmQ9dJbVWtqAexnlo/edit?gid=186801340#gid=186801340"

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

# --- SISTEMA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = ""

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    df_usuarios = carregar_dados("Logins")
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        validacao = df_usuarios[(df_usuarios['Usuario'] == user_input) & (df_usuarios['Senha'].astype(str) == pass_input)]
        if not validacao.empty:
            st.session_state.logado = True
            st.session_state.usuario_atual = user_input
            st.rerun()
        else: st.error("Usuário ou senha incorretos")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
df = carregar_dados()
df['Valor Total'] = df['Quantidade'] * df['Valor Unit']

st.title("📦 Gestão de Estoque Completa")
c1, c2, c3 = st.columns(3)
c1.metric("💰 Total Investido", f"R$ {df['Valor Total'].sum():,.2f}")
c2.metric("📦 Itens Totais", f"{df['Quantidade'].sum()} un")
c3.metric("👤 Logado como", st.session_state.usuario_atual)
st.markdown("---")

opcoes_menu = ["Ver Estoque", "Entrada", "Saída", "Editar/Excluir", "Histórico", "Relatório de Compras"]
if st.session_state.usuario_atual == "admin":
    opcoes_menu.append("Gestão de Acessos")
menu = st.sidebar.selectbox("Menu", opcoes_menu)

# --- TELAS ---
if menu == "Ver Estoque":
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
            st.rerun()

elif menu == "Saída":
    prod_sel = st.selectbox("Produto", df['Produto'].unique())
    qtd_s = st.number_input("Qtd Saída", min_value=1)
    if st.button("Confirmar Baixa"):
        idx = df[df['Produto'] == prod_sel].index
        if df.loc[idx, 'Quantidade'].values >= qtd_s:
            df.loc[idx, 'Quantidade'] -= qtd_s
            conn.update(spreadsheet=URL_PLANILHA, data=df)
            registrar_historico(f"SAÍDA ({st.session_state.usuario_atual})", prod_sel, qtd_s)
            st.rerun()

elif menu == "Gestão de Acessos":
    st.subheader("👥 Controle de Usuários")
    df_logins = carregar_dados("Logins")
    
    col_cad, col_rem = st.columns(2)
    with col_cad:
        st.write("**Cadastrar Novo**")
        n_u = st.text_input("Nome")
        n_s = st.text_input("Senha", type="password")
        if st.button("Salvar Usuário"):
            if n_u not in df_logins['Usuario'].values:
                novo_row = pd.DataFrame([[n_u, n_s]], columns=['Usuario', 'Senha'])
                df_up = pd.concat([df_logins, novo_row], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="Logins", data=df_up)
                st.success("Cadastrado!")
                st.rerun()
    
    with col_rem:
        st.write("**Remover Usuário**")
        u_rem = st.selectbox("Selecione para excluir", df_logins[df_logins['Usuario'] != 'admin']['Usuario'].unique())
        if st.button("🗑️ Excluir Acesso", type="primary"):
            df_up = df_logins[df_logins['Usuario'] != u_rem]
            conn.update(spreadsheet=URL_PLANILHA, worksheet="Logins", data=df_up)
            st.error(f"Usuário {u_rem} removido.")
            st.rerun()

elif menu == "Histórico":
    st.subheader("📅 Log de Atividades")
    df_h = carregar_dados("Historico")
    st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)

# ... (Manter código de Editar/Excluir e Relatórios conforme versões anteriores)
