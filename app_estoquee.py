import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from fpdf import FPDF

# Configurações da página
st.set_page_config(page_title="Gestão de Estoque Pro", layout="wide")

# Banco de dados simples (CSV)
ARQUIVO = "estoque_web.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO):
        return pd.read_csv(ARQUIVO)
    return pd.DataFrame(columns=['SKU', 'Produto', 'Quantidade', 'Valor Unit', 'NF'])

def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

# --- LOGIN SIMPLES ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()

# --- SISTEMA APÓS LOGIN ---
df = carregar_dados()

st.title("📦 Sistema de Gestão de Estoque")

# Sidebar - Menu
menu = st.sidebar.selectbox("Menu", ["Visualizar Estoque", "Nova Entrada", "Dar Saída", "Relatórios"])

if menu == "Visualizar Estoque":
    st.subheader("📋 Inventário Atual")
    if not df.empty:
        # Cálculos extras
        df['Valor Total'] = df['Quantidade'] * df['Valor Unit']
        df['Status'] = df['Quantidade'].apply(lambda x: "⚠️ BAIXO" if x < 5 else "✅ OK")
        st.dataframe(df, use_container_width=True)
        
        # Gráfico
        st.subheader("📊 Nível de Estoque")
        fig, ax = plt.subplots()
        ax.bar(df['Produto'], df['Quantidade'], color='skyblue')
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Estoque vazio.")

elif menu == "Nova Entrada":
    st.subheader("➕ Registrar Entrada")
    with st.form("form_entrada"):
        nome = st.text_input("Nome do Produto").upper()
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        valor = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
        nf = st.text_input("Número da NF")
        btn = st.form_submit_button("Salvar Entrada")
        
        if btn:
            if nome in df['Produto'].values:
                df.loc[df['Produto'] == nome, 'Quantidade'] += qtd
                df.loc[df['Produto'] == nome, 'Valor Unit', 'NF'] = [valor, nf]
            else:
                novo_sku = f"PROD-{len(df)+1:03d}"
                nova_linha = pd.DataFrame([[novo_sku, nome, qtd, valor, nf]], columns=df.columns)
                df = pd.concat([df, nova_linha], ignore_index=True)
            salvar_dados(df)
            st.success(f"Entrada de {nome} registrada!")

elif menu == "Dar Saída":
    st.subheader("➖ Registrar Saída")
    produto_sel = st.selectbox("Selecione o Produto", df['Produto'].unique())
    qtd_saida = st.number_input("Quantidade de Saída", min_value=1, step=1)
    if st.button("Confirmar Saída"):
        estoque_atual = df.loc[df['Produto'] == produto_sel, 'Quantidade'].values[0]
        if estoque_atual >= qtd_saida:
            df.loc[df['Produto'] == produto_sel, 'Quantidade'] -= qtd_saida
            salvar_dados(df)
            st.warning(f"Saída de {qtd_saida} un de {produto_sel} realizada.")
        else:
            st.error("Estoque insuficiente!")

elif menu == "Relatórios":
    st.subheader("📑 Exportar Dados")
    if st.button("Gerar Relatório PDF"):
        st.write("Função de PDF pronta para exportação.")
        # Aqui você pode implementar o download do CSV também:
        st.download_button("Baixar Planilha Excel (CSV)", df.to_csv(index=False), "estoque.csv", "text/csv")

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()
    