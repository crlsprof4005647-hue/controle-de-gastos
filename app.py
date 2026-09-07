import streamlit as st
import pandas as pd
import datetime  # Não podemos esquecer o datetime para a data de hoje!
from streamlit_gsheets import GSheetsConnection

# 1. Configuração inicial da página (SEMPRE o primeiro comando do Streamlit)
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# 2. Customização do fundo (Seu verde escuro ficou ótimo!)
cor_de_fundo = """
<style>
    .stApp {
        background-color: #FFFFFF; 
    }
</style>
"""
st.markdown(cor_de_fundo, unsafe_allow_html=True)

# 3. Título do App
st.title("💲 Meu Controle Financeiro")
st.write("Bem-vindo ao seu aplicativo. Aqui vamos construir o painel.")

# 4. Criando a Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# 5. O Formulário (Onde as informações nascem)
st.subheader("📝 Adicionar Nova Transação")

with st.form(key="form_nova_transacao", clear_on_submit=True):
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        data_input = st.date_input("Data", datetime.date.today())
        descricao_input = st.text_input(
            "Descrição", placeholder="Ex: Compra no Mercado..."
        )
        valor_input = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        tipo_input = st.selectbox("Tipo", ["Saída", "Entrada"])

    with coluna2:
        categoria_input = st.selectbox(
            "Categoria",
            [
                "Alimentação",
                "Luz",
                "Água",
                "Internet",
                "Financiamento Casa",
                "Salário",
                "Lazer",
                "Outros",
            ],
        )
        conta_input = st.selectbox(
            "Conta_Origem",
            ["Cartão Nubank Carlos", "Cartão Nubank Regiane", "Dinheiro/Débito ou PIX"],
        )
        status_input = st.selectbox("Status", ["Pago", "Pendente"])
        recorrencia_input = st.selectbox(
            "Recorrência", ["Único", "Fixo Mensal", "Parcelado"]
        )

    # O botão nasce AQUI
    botao_salvar = st.form_submit_button("Salvar Transação")

# 6. A Lógica de Envio (Agora sim, o Python sabe quem é o 'botao_salvar' e as variáveis)
if botao_salvar:
    # Passo A: Ler o que já existe
    dados_existentes = conn.read(worksheet="Transacoes", usecols=list(range(10)))

    # Passo B: Criar o ID
    novo_id = len(dados_existentes) + 1

    # Passo C: Empacotar os dados digitados
    nova_linha = pd.DataFrame(
        [
            {
                "ID": novo_id,
                "Data": data_input.strftime("%d/%m/%Y"),
                "Descricao": descricao_input,
                "Valor": valor_input,
                "Tipo": tipo_input,
                "Categoria": categoria_input,
                "Conta_Origem": conta_input,
                "Status": status_input,
                "Recorrencia": recorrencia_input,
                "Data_Baixa": (
                    datetime.date.today().strftime("%d/%m/%Y")
                    if status_input == "Pago"
                    else ""
                ),
            }
        ]
    )

    # Passo D: Juntar antigo com novo
    dados_atualizados = pd.concat([dados_existentes, nova_linha], ignore_index=True)

    # Passo E: Atualizar no Google Sheets
    conn.update(worksheet="Transacoes", data=dados_atualizados)

    st.success(f"Transação '{descricao_input}' salva com sucesso no banco de dados!")


# --- DIVISOR VISUAL ---
st.divider()

st.subheader("📊 Histórico de Transações")

# O ttl=0 garante que os dados sejam sempre os mais recentes
dados_atuais = conn.read(worksheet="Transacoes", usecols=list(range(10)), ttl=0)

# ==========================================
# NOVO PAINEL: DAR BAIXA EM PAGAMENTOS
# ==========================================
st.subheader("✅ Dar Baixa em Pagamentos Pendentes")

# 1. Filtramos a tabela original para pegar SÓ as linhas onde o Status é "Pendente"
pendentes = dados_atuais[dados_atuais["Status"] == "Pendente"]

# 2. Se a tabela de pendentes não estiver vazia, mostramos o painel
if not pendentes.empty:

    # 3. Criamos uma lista de texto amigável. Ex: "1 - Mercado (R$ 150.0)"
    # Antes
    # Depois
    opcoes = (
        pendentes["ID"].astype(int).astype(str)  # <-- A MÁGICA ESTÁ AQUI
        + " - "
        + pendentes["Descricao"]
        + " (R$ "
        + pendentes["Valor"].astype(str)
        + ")"
    )

    # 4. Dividimos a tela para o Selectbox e o Botão ficarem lado a lado
    col_baixa1, col_baixa2 = st.columns([3, 1])  # A coluna 1 é 3x maior que a coluna 2

    with col_baixa1:
        transacao_escolhida = st.selectbox("Selecione a transação:", opcoes)

    with col_baixa2:
        st.write("")  # Pula uma linha fantasma...
        st.write(
            ""
        )  # ...para empurrar o botão para baixo e alinhar com a caixa de texto
        botao_baixa = st.button("Dar Baixa")

    # 5. O que acontece quando clica no botão?
    if botao_baixa:
        # Depois (adicionamos o float no meio)
        id_escolhido = int(float(transacao_escolhida.split(" - ")[0]))

        # B. Encontramos qual é a posição (índice) exata desse ID dentro da tabela inteira do Google Sheets
        indice = dados_atuais.index[dados_atuais["ID"] == id_escolhido][0]

        # C. Alteramos a célula do Status e a célula da Data da Baixa
        dados_atuais.at[indice, "Status"] = "Pago"
        dados_atuais.at[indice, "Data_Baixa"] = datetime.date.today().strftime(
            "%d/%m/%Y"
        )

        # D. Substituímos a planilha pela nossa versão alterada
        conn.update(worksheet="Transacoes", data=dados_atuais)
        st.success("Pagamento baixado com sucesso!")
        st.rerun()
else:
    # Se a tabela de pendentes estiver vazia (tudo pago):
    st.info("Nenhum pagamento pendente! Tudo em dia. 🎉")

st.divider()
# AQUI EMBAIXO CONTINUA O SEU CÓDIGO DA TABELA (st.data_editor...)

st.write(
    "💡 Dê um duplo clique em qualquer célula para editar (ex: mude o Status para Pago)."
)

# 8. O Editor de Dados (Substitui o st.dataframe antigo)
dados_editados = st.data_editor(
    dados_atuais, use_container_width=True, hide_index=True, key="editor_tabela"
)

# 9. A Lógica de Atualização no Banco de Dados
if not dados_atuais.equals(dados_editados):
    st.warning("⚠️ Você fez alterações na tabela. Clique abaixo para confirmar.")

    if st.button("💾 Salvar Alterações no Banco"):
        conn.update(worksheet="Transacoes", data=dados_editados)
        st.success("Alterações salvas com sucesso!")
        st.rerun()  # Recarrega a tela para limpar o aviso
