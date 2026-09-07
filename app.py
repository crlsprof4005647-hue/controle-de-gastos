import streamlit as st
import pandas as pd
import datetime 
from streamlit_gsheets import GSheetsConnection

# 1. Configuração inicial da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# ==========================================
# 2. CUSTOMIZAÇÃO DE LAYOUT (Fundo e Cores)
# ==========================================

# Primeiro, precisamos iniciar a memória ANTES de pintar a tela
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Se a pessoa NÃO estiver logada (Tela de Login):
if not st.session_state["autenticado"]:
    cor_de_fundo = """
    <style>
        /* Pinta o fundo da tela com o azul escuro que você escolheu */
        .stApp {
            background-color: #0F172A; 
        }
        /* Força todos os textos (títulos, parágrafos e nomes dos campos) a ficarem brancos */
        h1, h2, h3, p, label, .stMarkdown {
            color: #FFFFFF !important;
        }
    </style>
    """
# Se a pessoa JÁ estiver logada (Dentro do App):
else:
    cor_de_fundo = """
    <style>
        .stApp {
            background-color: #FFFFFF; /* Fundo branco para a tabela e formulário */
        }
    </style>
    """

# Aplica a pintura na tela
st.markdown(cor_de_fundo, unsafe_allow_html=True)


# ==========================================
# O SISTEMA DE LOGIN (O Leão de Chácara)
# ==========================================

# A Tela da Barreira (só aparece se não estiver logado)
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito")
    # ... (o restante do código do login continua igualzinho a partir daqui)


# ==========================================
# O SISTEMA DE LOGIN (O Leão de Chácara)
# ==========================================

# Iniciando a memória do usuário
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# A Tela da Barreira (só aparece se não estiver logado)
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito")
    
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password") 
        botao_entrar = st.form_submit_button("Entrar")

    if botao_entrar:
        senhas_salvas = st.secrets["senhas"]
        
        # Checa se o email existe e se a senha está correta
        if email in senhas_salvas and senhas_salvas[email] == senha:
            st.session_state["autenticado"] = True 
            
            # Busca no cofre qual é a aba desse usuário e salva na memória!
            st.session_state["aba_usuario"] = st.secrets["ambientes"][email]
            
            st.rerun() # Recarrega a página para sumir o login
        else:
            st.error("E-mail ou senha incorretos!")
    
    st.stop() # Bloqueia o carregamento do resto do site!


# ==========================================
# ÁREA LOGADA (O APLICATIVO FINANCEIRO)
# ==========================================

st.title("💲 Meu Controle Financeiro")
st.write(f"Bem-vindo(a)! Você está acessando a base de dados: **{st.session_state['aba_usuario']}**")

# Criando a Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. O FORMULÁRIO DE ENTRADA ---
st.subheader("📝 Adicionar Nova Transação")

with st.form(key="form_nova_transacao", clear_on_submit=True):
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        data_input = st.date_input("Data", datetime.date.today())
        descricao_input = st.text_input("Descrição", placeholder="Ex: Compra no Mercado...")
        valor_input = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        tipo_input = st.selectbox("Tipo", ["Saída", "Entrada"])

    with coluna2:
        categoria_input = st.selectbox(
            "Categoria",
            ["Alimentação", "Luz", "Água", "Internet", "Financiamento Casa", "Salário", "Lazer", "Outros"]
        )
        conta_input = st.selectbox(
            "Conta_Origem",
            ["Cartão Nubank Carlos", "Cartão Nubank Regiane", "Dinheiro/Débito ou PIX"]
        )
        status_input = st.selectbox("Status", ["Pago", "Pendente"])
        recorrencia_input = st.selectbox("Recorrência", ["Único", "Fixo Mensal", "Parcelado"])

    botao_salvar = st.form_submit_button("Salvar Transação")

# Lógica de Salvar a Transação
if botao_salvar:
    # LUGAR 1: Lê a aba dinâmica do usuário logado
    dados_existentes = conn.read(worksheet=st.session_state["aba_usuario"], usecols=list(range(10)))

    novo_id = len(dados_existentes) + 1

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

    dados_atualizados = pd.concat([dados_existentes, nova_linha], ignore_index=True)

    # LUGAR 2: Salva na aba dinâmica do usuário logado
    conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atualizados)
    st.success(f"Transação '{descricao_input}' salva com sucesso!")


st.divider()

# --- 2. PAINEL DE DAR BAIXA ---
# LUGAR 3: Lê os dados atualizados da aba dinâmica do usuário
dados_atuais = conn.read(worksheet=st.session_state["aba_usuario"], usecols=list(range(10)), ttl=0)

st.subheader("✅ Dar Baixa em Pagamentos Pendentes")

pendentes = dados_atuais[dados_atuais["Status"] == "Pendente"]

if not pendentes.empty:
    # A correção mágica do astype duplo para evitar o erro do Pandas
    opcoes = (
        pendentes["ID"].astype(int).astype(str)
        + " - "
        + pendentes["Descricao"]
        + " (R$ "
        + pendentes["Valor"].astype(str)
        + ")"
    )

    col_baixa1, col_baixa2 = st.columns([3, 1]) 

    with col_baixa1:
        transacao_escolhida = st.selectbox("Selecione a transação:", opcoes)

    with col_baixa2:
        st.write("") 
        st.write("") 
        botao_baixa = st.button("Dar Baixa")

    if botao_baixa:
        # A correção com o float para aceitar '1.0' caso venha assim do Sheets
        id_escolhido = int(float(transacao_escolhida.split(" - ")[0]))

        indice = dados_atuais.index[dados_atuais["ID"] == id_escolhido][0]

        dados_atuais.at[indice, "Status"] = "Pago"
        dados_atuais.at[indice, "Data_Baixa"] = datetime.date.today().strftime("%d/%m/%Y")

        # LUGAR 4: Atualiza a aba dinâmica
        conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atuais)
        st.success("Pagamento baixado com sucesso!")
        st.rerun()
else:
    st.info("Nenhum pagamento pendente! Tudo em dia. 🎉")


st.divider()


# --- 3. TABELA DE EDIÇÃO LIVRE ---
st.subheader("📊 Histórico de Transações")
st.write("💡 Dê um duplo clique em qualquer célula para editar.")

dados_editados = st.data_editor(
    dados_atuais, use_container_width=True, hide_index=True, key="editor_tabela"
)

if not dados_atuais.equals(dados_editados):
    st.warning("⚠️ Você fez alterações na tabela. Clique abaixo para confirmar.")

    if st.button("💾 Salvar Alterações no Banco"):
        # LUGAR 5: Atualiza a aba dinâmica se o usuário editar algo solto
        conn.update(worksheet=st.session_state["aba_usuario"], data=dados_editados)
        st.success("Alterações salvas com sucesso!")
        st.rerun()
