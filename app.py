import streamlit as st
import os
import requests
import base64
import json

def main():
    if 'conversa' not in st.session_state:
        st.session_state.conversa = []

    escreve_chat()
    scrooling_page()


def reload_page():
    st.session_state.conversa = []
    st.experimental_rerun()


def scrooling_page():
    # JavaScript para rolar a página para o final
    scroll_js = """
    <script>
    window.scrollTo(0, document.body.scrollHeight);
    </script>
    """

    # Executa o JavaScript
    st.markdown(scroll_js, unsafe_allow_html=True)

def escreve_chat():
    if len(st.session_state.conversa) > 0:
        for i in range(len(st.session_state.conversa)):
            if st.session_state.conversa[i]['role'] == "user":
                with st.chat_message("human"):
                    if 'content' in st.session_state.conversa[i]:
                        st.write(st.session_state.conversa[i]['content'])
            else:
                with st.chat_message("ai"):
                    if 'content' in st.session_state.conversa[i]:
                        st.write(st.session_state.conversa[i]['content'])

def call_prompt():
    if token_acesso:
        #contexto e historico
        st.session_state.conversa.append({"role" : "user", "content" : prompt_user})
        
        if (token_acesso == "JYORXq1Uqo0M=" or "Y8m0ZgVH4YU7=") and modelo == "GPT-4o" :
            call_chatGPTPreventIa_GPT4o()
        else:
            call_api_Fusion_GPT4()

    else:
        st.warning("Por favor, digite seu token de acesso")

# Função para carregar a persona a partir de um arquivo
def carregar_persona(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        persona = f.read()
    return persona

def encodar_imagem(caminho_imagem):
    with open(caminho_imagem, "rb") as arquivo_imagem:
        return base64.b64encode(arquivo_imagem.read()).decode('utf-8')


def call_chatGPTPreventIa_GPT4o():

    chave_api = ""
    modelo="gpt-3.5-turbo"   #"gpt-4o"   #"gpt-3.5-turbo"    #"gpt-4"
    temperatura=0.7
    max_tokens=150


    contexto = ', '.join(map(str, st.session_state.conversa))
    strcontexto = ""
    # Loop através do array contexto
    for elemento in st.session_state.conversa:
        # Verifica se a chave "content" está presente no elemento
        if "content" in elemento:
            # Adiciona o conteúdo à strcontexto, seguido por ponto e vírgula
            strcontexto +=  "role: " + elemento["role"]  + " content:" + elemento["content"] + "; "

    #st.write("processando contexto")
    #st.write(strcontexto)


    # Endpoint da API ChatGPT4o
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {chave_api}"
    }
    data = { 
        "model": f"{modelo}", 
        "messages": [ 
            { 
                "role": "user", 
                "content": f"{prompt_user}"    #prompt_user
            } ] 
    }

    try:
        response = requests.post(url, headers=headers, json=data)  #   data=json.dumps(data))

        if response.status_code == 200:
            resposta = response.json()

            textoResposta = resposta.get("choices")[0].get("message").get("content")

            total_tokens = resposta.get("usage").get("total_tokens")
            st.write("Tokens Gerados: " + str(total_tokens))

            #Adiciona a resposta na conversa
            #st.session_state.conversa.append(textoResposta.json())
            st.session_state.conversa.append({"role": "assistant", "content": textoResposta})

        else:
            st.write(f"Erro na requisição: {response.status_code}")
            st.write(response.json())


    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.write("Falha ao chamar a API:", response.status_code)
        st.error(f"Other error occurred: {err}")




def call_api_Fusion_GPT4():
    # URL da API
    url = 'https://brq-openai.azurewebsites.net/brq/gpt4o'

    #testeimagem = encodar_imagem('images/casa_rosada.jpg')
    #st.session_state.conversa.append({"role" : "user", "image" : testeimagem})
    
    contexto = ', '.join(map(str, st.session_state.conversa))
    
    # Dados da solicitação em formato JSON
    data = {
        "prompt": contexto,
        "max_tokens": max_tokens,
        "temperature": temperatura
    }

    # Cabeçalhos da solicitação
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token_acesso}',
        'Content-Type': 'application/json'
    }
    # Fazendo a solicitação POST para a API com os dados JSON
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "Resposta não encontrada.")
        st.session_state.conversa.append({"role" : "assistant", "content" : answer})
    else:
        st.write("Falha ao chamar a API:", response.status_code)



st.set_page_config(page_title="Bem vindo ao PreventionIA", page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

#, page_icon = favicon, layout = 'wide', initial_sidebar_state = 'auto'
# favicon being an object of the same kind as the one you should provide st.image() with (ie. a PIL array for example) or a string (url or local file path)


# Sidebar inicio
st.sidebar.title("Configurações")
token_acesso = st.sidebar.text_input("Digite o seu token", type="password")
modelo = "GPT-4o"

                #st.sidebar.selectbox(
                #                "Selecione o modelo",
                #                ("fu-GPT-4o", "fu-Claude 2 AWS"))

max_tokens = st.sidebar.number_input("Max tokens", 100, 5000, 2000)
temperatura = st.sidebar.slider("Temperatura", 0.00, 1.00, 0.90)
st.markdown(
    """
    <style>
    .stButton > button {
        display: block;
        margin-left: auto;
        margin-right: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)
btnNewChat = st.sidebar.button("Novo Chat")

if btnNewChat:
    reload_page()

# Sidebar Fim

# Principal Inicio
col1, col2 = st.columns([1, 10])
with col1:
    st.image("images/bot.png", width=60)

with col2:
    st.subheader("Olá, sou o PreventIA, como posso te ajudar hoje?") 

prompt_user = st.chat_input("Digite o que você precisa, sendo o mais detalhista possível")
if(prompt_user):
    if 'modelo_atual' not in st.session_state:
        st.session_state.modelo_atual = modelo
    else:
        if st.session_state.modelo_atual != modelo:
            st.session_state.modelo_atual = modelo
            st.session_state.conversa = []

    call_prompt()

if __name__ == "__main__":
    main()
#Principal Fim