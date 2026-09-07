import streamlit as st
import pandas as pd
import datetime 
import altair as alt  # A biblioteca mágica de gráficos
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# ==========================================
# 2. CUSTOMIZAÇÃO DE LAYOUT (Fundo e Cores)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    cor_de_fundo = """
    <style>
        .stApp { background-color: #0F172A; }
        h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #1D4ED8 !important;
        }
    </style>
    """
else:
    cor_de_fundo = """
    <style>
        .stApp { background-color: #1E293B; }
        h1, h2, h3, p, label, .stMarkdown, .stTab { color: #FFFFFF !important; }
    </style>
    """
st.markdown(cor_de_fundo, unsafe_allow_html=True)

# ==========================================
# 3. O SISTEMA DE LOGIN 
# ==========================================
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito")
    
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password") 
        botao_entrar = st.form_submit_button("Entrar")

    if botao_entrar:
        senhas_salvas = st.secrets["senhas"]
        if email in senhas_salvas and senhas_salvas[email] == senha:
            st.session_state["autenticado"] = True 
            st.session_state["aba_usuario"] = st.secrets["ambientes"][email]
            st.rerun() 
        else:
            st.error("E-mail ou senha incorretos!")
    
    st.stop() 


# ==========================================
# 4. ÁREA LOGADA (O APLICATIVO FINANCEIRO)
# ==========================================
st.title("💲 Meu Controle Financeiro")
st.write(f"Bem-vindo(a)! Base de dados ativa: **{st.session_state['aba_usuario']}**")

conn = st.connection("gsheets", type=GSheetsConnection)

# Lemos os dados uma única vez aqui no topo para usar no app todo
dados_atuais = conn.read(worksheet=st.session_state["aba_usuario"], usecols=list(range(10)), ttl=0)

# ==========================================
# 5. CRIANDO AS ABAS DE NAVEGAÇÃO
# ==========================================
aba_lancamentos, aba_relatorios = st.tabs(["📝 Lançamentos", "📊 Gráficos e Relatórios"])

# ------------------------------------------
# ABA 1: LANÇAMENTOS (Onde entra o dinheiro)
# ------------------------------------------
with aba_lancamentos:
    if st.session_state["aba_usuario"] == "Transacao":
        lista_de_contas = ["Cartão Nubank Carlos", "Cartão Nubank Regiane", "Dinheiro/Débito ou PIX"]
    else:
        lista_de_contas = ["Cartão de Crédito", "Conta Corrente", "Dinheiro/PIX"]

    st.subheader("📝 Adicionar Nova Transação")

    with st.form(key="form_nova_transacao", clear_on_submit=True):
        coluna1, coluna2 = st.columns(2)

        with coluna1:
            data_input = st.date_input("Data", datetime.date.today())
            descricao_input = st.text_input("Descrição", placeholder="Ex: Compra no Mercado...")
            valor_input = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            tipo_input = st.selectbox("Tipo", ["Saída", "Entrada"])

        with coluna2:
            categoria_input = st.selectbox("Categoria", ["Alimentação", "Luz", "Água", "Internet", "Financiamento Casa", "Salário", "Lazer", "Outros"])
            conta_input = st.selectbox("Conta_Origem", lista_de_contas)
            status_input = st.selectbox("Status", ["Pago", "Pendente"])
            recorrencia_input = st.selectbox("Recorrência", ["Único", "Fixo Mensal", "Parcelado"])

        botao_salvar = st.form_submit_button("Salvar Transação")

    if botao_salvar:
        novo_id = len(dados_atuais) + 1
        nova_linha = pd.DataFrame([{
            "ID": novo_id,
            "Data": data_input.strftime("%d/%m/%Y"),
            "Descricao": descricao_input,
            "Valor": valor_input,
            "Tipo": tipo_input,
            "Categoria": categoria_input,
            "Conta_Origem": conta_input,
            "Status": status_input,
            "Recorrencia": recorrencia_input,
            "Data_Baixa": datetime.date.today().strftime("%d/%m/%Y") if status_input == "Pago" else "",
        }])
        dados_atualizados = pd.concat([dados_atuais, nova_linha], ignore_index=True)
        conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atualizados)
        st.success(f"Transação '{descricao_input}' salva com sucesso!")
        st.rerun()

    st.divider()

    # --- PAINEL DE DAR BAIXA ---
    st.subheader("✅ Dar Baixa em Pagamentos Pendentes")
    pendentes = dados_atuais[dados_atuais["Status"] == "Pendente"]

    if not pendentes.empty:
        opcoes = (pendentes["ID"].astype(int).astype(str) + " - " + pendentes["Descricao"] + " (R$ " + pendentes["Valor"].astype(str) + ")")
        col_baixa1, col_baixa2 = st.columns([3, 1]) 
        with col_baixa1:
            transacao_escolhida = st.selectbox("Selecione a transação:", opcoes)
        with col_baixa2:
            st.write(""); st.write("") 
            botao_baixa = st.button("Dar Baixa")

        if botao_baixa:
            id_escolhido = int(float(transacao_escolhida.split(" - ")[0]))
            indice = dados_atuais.index[dados_atuais["ID"] == id_escolhido][0]
            dados_atuais.at[indice, "Status"] = "Pago"
            dados_atuais.at[indice, "Data_Baixa"] = datetime.date.today().strftime("%d/%m/%Y")
            conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atuais)
            st.success("Pagamento baixado com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum pagamento pendente! Tudo em dia. 🎉")

    st.divider()

    # --- TABELA DE EDIÇÃO LIVRE ---
    st.subheader("📊 Histórico de Transações")
    st.write("💡 Dê um duplo clique em qualquer célula para editar.")
    dados_editados = st.data_editor(dados_atuais, use_container_width=True, hide_index=True, key="editor_tabela")

    if not dados_atuais.equals(dados_editados):
        st.warning("⚠️ Você fez alterações na tabela. Clique abaixo para confirmar.")
        if st.button("💾 Salvar Alterações no Banco"):
            conn.update(worksheet=st.session_state["aba_usuario"], data=dados_editados)
            st.success("Alterações salvas com sucesso!")
            st.rerun() 


# ------------------------------------------
# ABA 2: GRÁFICOS E RELATÓRIOS (A Inteligência)
# ------------------------------------------
with aba_relatorios:
    st.subheader("📊 Painel de Inteligência Financeira")
    
    # Prepara os dados matematicamente para evitar erros
    dados_graficos = dados_atuais.copy()
    dados_graficos["Valor"] = pd.to_numeric(dados_graficos["Valor"], errors="coerce").fillna(0)
    
    # Converte a data para o formato Ano-Mês (ex: 2026-09) para ordenar corretamente no gráfico
    dados_graficos["Data_Real"] = pd.to_datetime(dados_graficos["Data"], format="%d/%m/%Y", errors="coerce")
    dados_graficos["Mes_Ano"] = dados_graficos["Data_Real"].dt.strftime("%Y-%m")
    
    if not dados_graficos.empty and not dados_graficos["Data_Real"].isnull().all():
        
        # --- GRÁFICO 1: Entradas x Saídas x Diferença (Mês a Mês) ---
        st.markdown("#### ⚖️ Balanço Mensal (Entradas x Saídas x Diferença)")
        
        # Agrupa os dados
        resumo_mes = dados_graficos.groupby(["Mes_Ano", "Tipo"])["Valor"].sum().unstack(fill_value=0)
        
        # Garante que as colunas existam mesmo se não houver registros em um mês
        if "Entrada" not in resumo_mes.columns: resumo_mes["Entrada"] = 0
        if "Saída" not in resumo_mes.columns: resumo_mes["Saída"] = 0
            
        resumo_mes["Diferença (Saldo)"] = resumo_mes["Entrada"] - resumo_mes["Saída"]
        
        # Desenha o gráfico de barras (O Streamlit escolhe cores automáticas lindas pra isso)
        st.bar_chart(resumo_mes[["Entrada", "Saída", "Diferença (Saldo)"]])
        
        st.divider()

        # Isolar apenas os gastos (Saídas) para os próximos gráficos
        saidas = dados_graficos[dados_graficos["Tipo"] == "Saída"]
        
        if not saidas.empty:
            # --- GRÁFICOS 2 e 3: Gráficos de Rosca Lado a Lado ---
            st.markdown("#### 🍩 Distribuição de Despesas")
            col_rosca1, col_rosca2 = st.columns(2)
            
            with col_rosca1:
                st.markdown("**Por Categoria (Onde gastei?)**")
                gastos_cat = saidas.groupby("Categoria")["Valor"].sum().reset_index()
                rosca_cat = alt.Chart(gastos_cat).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Categoria", type="nominal"),
                    tooltip=["Categoria", "Valor"]
                ).properties(height=300)
                # theme="streamlit" faz as letras ficarem brancas no fundo escuro automaticamente
                st.altair_chart(rosca_cat, use_container_width=True, theme="streamlit")
                
            with col_rosca2:
                st.markdown("**Por Conta (Como paguei?)**")
                gastos_conta_rosca = saidas.groupby("Conta_Origem")["Valor"].sum().reset_index()
                rosca_conta = alt.Chart(gastos_conta_rosca).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Conta_Origem", type="nominal"),
                    tooltip=["Conta_Origem", "Valor"]
                ).properties(height=300)
                st.altair_chart(rosca_conta, use_container_width=True, theme="streamlit")
                
            st.divider()
            
            # --- GRÁFICO 4: Formas de Pagamento Mês a Mês ---
            st.markdown("#### 💳 Evolução das Formas de Pagamento (Mês a Mês)")
            
            # Agrupa Mês x Conta_Origem
            evolucao_contas = saidas.groupby(["Mes_Ano", "Conta_Origem"])["Valor"].sum().unstack(fill_value=0)
            
            # O gráfico de barras nativo empilha e separa automaticamente
            st.bar_chart(evolucao_contas)
            
        else:
            st.info("Nenhuma despesa (Saída) registrada para gerar os relatórios detalhados.")
            
    else:
        st.info("Adicione transações para ver os gráficos!")
