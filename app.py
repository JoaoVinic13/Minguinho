# -*- coding: utf-8 -*-
# Minguinho - chatbot web fofinho sobre cultura pop.
# Aplicacao Flask minima e didatica. As partes seguintes (SYSTEM_PROMPT,
# cliente Bedrock, funcoes de invocacao, rotas e inicializacao) serao
# adicionadas incrementalmente nas proximas tarefas.

# Importacoes necessarias:
# - os: leitura de variaveis de ambiente (credenciais AWS no startup).
# - json: serializacao/deserializacao do corpo trocado com o Bedrock.
# - boto3: cliente para invocar o modelo via Amazon Bedrock.
# - Flask e utilitarios: criacao do app, renderizacao da pagina e JSON.
import os
import sys
import json

import boto3
from flask import Flask, render_template, request, jsonify

# Instancia principal da aplicacao Flask.
app = Flask(__name__)

# Preserva acentos do portugues nas respostas JSON (ex.: a, e, c), evitando
# que sejam convertidos em sequencias de escape ASCII (\uXXXX). O jsonify ja
# define o Content-Type como application/json; charset=utf-8.
app.json.ensure_ascii = False

# ---------------------------------------------------------------------------
# SYSTEM_PROMPT: personalidade, tom e limites do Minguinho (Requisitos 5.1-5.9).
# Esta constante e enviada ao modelo no campo "system" a cada invocacao e
# define quem o Minguinho e, como ele fala e sobre o que ele conversa.
# O texto e escrito em portugues e organizado em secoes curtas e diretas
# para que o modelo siga as regras de forma consistente.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Você é o Minguinho, um chatbot docinho, fofinho, bonitinho, caloroso e muito acolhedor. (Req 5.1, 5.6)

# Identidade e tom
- Seu nome é Minguinho e você sempre se apresenta assim quando fizer sentido, com um carinho especial. (Req 5.1)
- Seu tom é bem docinho, meigo, afetuoso e aconchegante, como um abraço gostoso: trate a pessoa com ternura e delicadeza, usando palavrinhas gentis e apelidos fofos de leve, mas NUNCA de forma enjoativa ou exagerada: doçura na medida certa. (Req 5.6)
- Você é curioso e amigável: demonstre interesse genuíno e cheio de carinho pelo que a pessoa gosta, com atenção doce aos temas que vocês estão conversando. (Req 5.1)

# Idioma
- Responda SEMPRE em português. (Req 5.3)

# Temas que você domina (seu escopo)
- Você conversa EXCLUSIVAMENTE sobre estes cinco temas: jogos, séries de TV, livros, animes e artistas. (Req 5.2)
- Nesses cinco temas você tem conhecimento amplo e profundo de cultura pop: recomende títulos, comente histórias, personagens, autores, estúdios, trilhas, lançamentos e curiosidades com segurança e carinho. (Req 5.8)

# Uso de emojis e palavras confortantes
- Use emojis e palavras confortantes de forma equilibrada e moderada, para deixar a conversa aconchegante sem poluir o texto. (Req 5.7)
- Use no MÁXIMO 3 emojis por resposta. (Req 5.7)

# Formato das respostas
- Responda sempre em parágrafos curtos, cada um com no máximo 3 linhas.
- Nunca use bullet points nem listas: escreva em texto corrido.
- Quando for relevante explicar algo, conte uma analogia curta e carinhosa em vez de listar definições.

# Perguntas de volta
- NUNCA faça perguntas de volta ao usuário. Apenas responda ao que foi dito e aguarde a próxima mensagem dele, sem devolver perguntas nem pedir que ele continue.

# Quando o assunto estiver fora dos cinco temas
- Se a pessoa falar de algo que não seja jogos, séries de TV, livros, animes ou artistas, avise gentilmente que esse assunto está fora do seu escopinho e proponha, de forma acolhedora, retomar a conversa em pelo menos um dos cinco temas que você ama (jogos, séries de TV, livros, animes ou artistas). (Req 5.5)

# Quando o assunto for esportes
- Se a pessoa falar de esportes, reconheça de forma gentil e acolhedora que esportes não é um tema que você domina bem, sem deixar a pessoa sem graça, e proponha carinhosamente retomar a conversa em pelo menos um dos cinco temas que você conhece de verdade (jogos, séries de TV, livros, animes ou artistas). (Req 5.9)
"""
# ---------------------------------------------------------------------------
# Memoria de conversa (historico).
# HISTORICO_CONVERSA guarda, em ordem, todas as mensagens trocadas na conversa
# no formato da Anthropic Messages API: cada item e um dicionario com "role"
# ("user" ou "assistant") e "content" (lista de blocos de texto). A cada nova
# pergunta, a mensagem do usuario e adicionada aqui e a lista INTEIRA e enviada
# ao Bedrock, dando ao Minguinho memoria do que ja foi conversado. A resposta
# gerada tambem e guardada, para servir de contexto nas proximas perguntas.
#
# Observacao didatica: por ser uma lista global em memoria, o historico e unico
# para o processo e some quando o servidor e reiniciado (sem banco de dados).
# ---------------------------------------------------------------------------
HISTORICO_CONVERSA = []

# ---------------------------------------------------------------------------
# Integracao com o Amazon Bedrock (Requisitos 4.1, 4.2, 6.1, 6.2).
# ---------------------------------------------------------------------------

# MODEL_ID: identificador do perfil de inferencia do modelo Claude Hauku usado
# em todas as invocacoes. Deve ser exatamente este valor. (Req 4.2)
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Cliente bedrock-runtime criado uma unica vez na inicializacao do app e
# reaproveitado em todas as chamadas, evitando recriar o cliente a cada
# requisicao. A operacao de invocacao (invoke_model) e feita na regiao
# us-east-1. (Req 4.1)
#
# As credenciais AWS NAO sao escritas no codigo: o proprio boto3 as resolve a
# partir das variaveis de ambiente (ex.: AWS_ACCESS_KEY_ID,
# AWS_SECRET_ACCESS_KEY e, se aplicavel, AWS_SESSION_TOKEN). Assim, nenhuma
# chave de acesso literal aparece no codigo-fonte. (Req 6.1, 6.2)
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Invocacao do modelo via Bedrock (Requisitos 4.1, 4.2, 4.3, 4.4, 4.5).
# ---------------------------------------------------------------------------


def invocar_bedrock(mensagens):
    """Monta o corpo no formato da Anthropic Messages API, invoca o modelo e
    extrai o texto gerado.

    Recebe a lista "mensagens" com TODO o historico da conversa (cada item no
    formato { "role": ..., "content": [...] }, terminando na mensagem atual do
    usuario) e chama o cliente bedrock-runtime via invoke_model usando o
    MODEL_ID correto. Enviar o historico inteiro a cada pergunta e o que da ao
    Minguinho memoria da conversa. Em seguida le o campo "body" da resposta,
    percorre os blocos de "content" do tipo "text" e extrai o texto gerado.
    (Req 4.4)

    Retorna:
      - o texto gerado (string nao-vazia) em caso de sucesso; ou
      - None quando a resposta nao contiver texto ou o texto estiver vazio,
        sinalizando para a rota (tarefa 5.2) tratar a situacao como falha de
        invocacao (HTTP 502). (Req 4.5)

    O corpo enviado ao modelo segue a forma esperada pela API de mensagens
    Anthropic no Bedrock (Req 4.3):
      - anthropic_version: versao do contrato Anthropic no Bedrock.
      - max_tokens: limite de tokens da resposta gerada.
      - system: recebe o SYSTEM_PROMPT, que define a personalidade do
        Minguinho. (Req 4.3)
      - messages: a lista completa do historico da conversa. (Req 4.3)
    """
    # Monta o dicionario do corpo da requisicao ao modelo.
    corpo = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        # O SYSTEM_PROMPT vai no campo "system", instruindo o modelo sobre a
        # identidade, o tom e os limites de assunto do Minguinho. (Req 4.3)
        "system": SYSTEM_PROMPT,
        # Envia TODO o historico da conversa, para que o modelo responda com
        # memoria do que ja foi dito nas mensagens anteriores.
        "messages": mensagens,
    }

    # Serializa o corpo para JSON e invoca o modelo via invoke_model, usando o
    # MODEL_ID correto na regiao us-east-1 (cliente ja configurado). (Req 4.1, 4.2)
    resposta = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(corpo),
    )

    # ---- Extracao do texto gerado (Req 4.4) --------------------------------
    # O campo "body" da resposta e um stream; le-se e deserializa-se o JSON
    # retornado pelo modelo. A forma esperada e:
    #   { "content": [ { "type": "text", "text": "<texto gerado>" }, ... ] }
    corpo_resposta = json.loads(resposta["body"].read())

    # Percorre os blocos de "content", concatenando o texto de todos os blocos
    # cujo "type" seja "text". Assim, se o modelo devolver o texto em mais de
    # um bloco, nenhuma parte e perdida. (Req 4.4)
    blocos = corpo_resposta.get("content", []) or []
    partes = [
        bloco.get("text", "")
        for bloco in blocos
        if isinstance(bloco, dict) and bloco.get("type") == "text"
    ]
    texto_gerado = "".join(partes).strip()

    # Sinaliza falha quando nao ha texto gerado ou o texto resultante esta
    # vazio: retorna None para que a rota trate a situacao como HTTP 502.
    # (Req 4.5)
    if not texto_gerado:
        return None

    # Caso de sucesso: devolve o texto extraido para a rota. (Req 4.4)
    return texto_gerado

# ---------------------------------------------------------------------------
# Rota raiz: exibe a pagina de chat do Minguinho (Requisitos 1.1, 1.2).
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def pagina_chat():
    """Renderiza a pagina de chat a partir de templates/index.html.

    Em caso de sucesso, devolve o HTML da pagina renderizada por
    render_template. (Req 1.1)

    A renderizacao e envolvida em tratamento de erro: se o template nao puder
    ser carregado ou renderizado (por exemplo, arquivo ausente ou falha na
    renderizacao), capturamos a excecao e respondemos com HTTP 500 e uma
    mensagem indicando que a pagina nao pode ser exibida, sem derrubar o
    processo do servidor. Assim, a aplicacao continua em execucao e apta a
    atender novas requisicoes. (Req 1.2)
    """
    try:
        # Renderiza a pagina de chat. (Req 1.1)
        return render_template("index.html")
    except Exception:
        # Falha ao carregar/renderizar o template: responde 500 com mensagem
        # amigavel em portugues, sem expor detalhes internos da excecao e sem
        # encerrar a aplicacao. (Req 1.2)
        return "Não foi possível exibir a página de chat no momento.", 500

# ---------------------------------------------------------------------------
# Rota de chat: recebe a Mensagem_Usuario e devolvera a Resposta_Bot.
# Esta tarefa (5.1) implementa APENAS a validacao de entrada, que rejeita
# requisicoes invalidas com HTTP 400 sem nunca chamar o Bedrock. A invocacao
# do modelo e o tratamento de sucesso/falha (200/502) serao adicionados na
# tarefa 5.2, reaproveitando o texto ja validado (variavel "texto").
# (Requisitos 3.1, 3.2, 3.3, 3.4, 3.5)
# ---------------------------------------------------------------------------


@app.route("/chat", methods=["POST"])
def rota_chat():
    """Valida a entrada da Rota_Chat antes de qualquer chamada ao Bedrock.

    A validacao acontece em tres etapas e, em qualquer caso de rejeicao,
    responde HTTP 400 com um corpo JSON { "error": ... } em portugues. Como
    todas as rejeicoes ocorrem ANTES de invocar o modelo, nenhuma chamada ao
    Servico_Bedrock e feita para requisicoes invalidas. (Req 3.5)
    """
    # 1. Leitura tolerante do corpo JSON (silent=True): se o corpo estiver
    #    ausente ou nao for um JSON valido, get_json devolve None em vez de o
    #    Flask lancar um erro padrao. Nesse caso respondemos 400 indicando que
    #    o corpo da requisicao e invalido. (Req 3.4)
    dados = request.get_json(silent=True)
    if dados is None:
        return (
            jsonify(
                {
                    "error": 'O corpo da requisição é inválido. Envie um JSON com o campo "message".'
                }
            ),
            400,
        )

    # 2. Campo "message" ausente: se o JSON nao contiver a chave "message",
    #    respondemos 400 informando que a mensagem e obrigatoria. (Req 3.1, 3.3)
    if "message" not in dados:
        return (
            jsonify({"error": "A mensagem é obrigatória e não pode estar vazia."}),
            400,
        )

    # 3. Mensagem vazia apos strip(): remove espacos, tabulacoes e quebras de
    #    linha nas extremidades. Se o texto resultante tiver comprimento 0,
    #    respondemos 400 com a mesma mensagem. (Req 3.2, 3.3)
    #    str(...) protege contra valores que nao sejam string (ex.: numero),
    #    garantindo que strip() possa ser aplicado com seguranca.
    texto = str(dados["message"]).strip()
    if len(texto) == 0:
        return (
            jsonify({"error": "A mensagem é obrigatória e não pode estar vazia."}),
            400,
        )

    # A partir daqui, "texto" contem a Mensagem_Usuario ja validada (nao-vazia
    # apos strip()) e pronta para ser encaminhada ao Bedrock. (Req 2.1)

    # Adiciona a pergunta atual ao historico da conversa, no formato da
    # Anthropic Messages API. Assim, a mensagem fica preservada entre as
    # requisicoes e sera reenviada ao modelo nas proximas perguntas.
    HISTORICO_CONVERSA.append(
        {
            "role": "user",
            "content": [{"type": "text", "text": texto}],
        }
    )

    # 4. Encaminha o historico completo ao Bedrock, envolvendo a invocacao em
    #    try/except. Qualquer excecao durante a chamada ao modelo (incluindo
    #    falha de autenticacao por credenciais AWS invalidas) e capturada e
    #    convertida em uma resposta HTTP 502 generica em portugues, sem expor
    #    detalhes internos da excecao nem valores de credenciais AWS. Como a
    #    excecao e tratada aqui dentro, o servidor permanece em execucao e
    #    continua aceitando novas requisicoes. (Req 8.1, 8.2, 8.3, 6.4)
    try:
        texto_gerado = invocar_bedrock(HISTORICO_CONVERSA)
    except Exception:
        # Falha na invocacao: remove a pergunta recem-adicionada para nao
        # deixar o historico com uma mensagem de usuario sem resposta, o que
        # poderia confundir o modelo nas proximas chamadas.
        HISTORICO_CONVERSA.pop()
        # Falha na invocacao do modelo: responde 502 com mensagem generica em
        # portugues, sem vazar detalhes internos nem credenciais. (Req 8.1, 8.2, 6.4)
        return (
            jsonify(
                {"error": "O serviço de IA falhou. Tente novamente em instantes."}
            ),
            502,
        )

    # 5. Resposta do modelo sem texto ou com texto vazio: invocar_bedrock
    #    devolve None nesse caso. Tratamos como falha de invocacao, respondendo
    #    HTTP 502 com mensagem descritiva em portugues. (Req 4.5)
    if texto_gerado is None:
        # Sem resposta util: remove a pergunta recem-adicionada para manter o
        # historico coerente (sem mensagem de usuario orfã).
        HISTORICO_CONVERSA.pop()
        return (
            jsonify(
                {
                    "error": "O serviço de IA não retornou uma resposta. Tente novamente em instantes."
                }
            ),
            502,
        )

    # Sucesso: guarda a resposta do Minguinho no historico, no papel
    # "assistant". Assim, nas proximas perguntas o modelo recebe tanto as
    # perguntas quanto as respostas anteriores e mantem o fio da conversa.
    HISTORICO_CONVERSA.append(
        {
            "role": "assistant",
            "content": [{"type": "text", "text": texto_gerado}],
        }
    )

    # 6. Sucesso: devolve o texto gerado no campo "reply" de um corpo JSON com
    #    HTTP 200. O jsonify preserva os acentos (ensure_ascii = False) e define
    #    o Content-Type como application/json; charset=utf-8. (Req 2.2, 2.4)
    return jsonify({"reply": texto_gerado}), 200

# ---------------------------------------------------------------------------
# Inicializacao: verificacao de credenciais AWS no startup (Requisitos 6.1, 6.3).
# ---------------------------------------------------------------------------


def verificar_credenciais_aws():
    """Verifica a presenca das credenciais AWS essenciais antes de iniciar o
    servidor.

    As credenciais AWS vem EXCLUSIVAMENTE de variaveis de ambiente (nenhuma
    chave literal no codigo). Esta funcao checa, via os.environ, a presenca das
    duas variaveis essenciais usadas pelo boto3 para autenticar no Bedrock:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY

    Se qualquer uma delas estiver ausente (ou vazia apos remover espacos),
    registramos uma mensagem clara em portugues indicando a ausencia das
    credenciais e interrompemos a inicializacao, encerrando o processo com um
    codigo de erro diferente de zero (sys.exit), sem iniciar o servidor. Isso
    evita subir um servidor que falharia em toda chamada ao Bedrock por falta
    de credenciais. (Req 6.1, 6.3)
    """
    # Lista das variaveis de ambiente essenciais que precisam estar definidas.
    variaveis_essenciais = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

    # Identifica quais variaveis essenciais estao ausentes ou vazias. Usamos
    # os.environ.get(...) e strip() para tratar valores vazios ou so com
    # espacos como ausentes.
    ausentes = [
        nome
        for nome in variaveis_essenciais
        if not os.environ.get(nome, "").strip()
    ]

    # Se houver variaveis ausentes, registra mensagem clara em portugues e
    # interrompe a inicializacao com codigo de erro (sem iniciar o servidor).
    # A mensagem cita apenas os NOMES das variaveis ausentes, nunca valores de
    # credenciais. (Req 6.3)
    if ausentes:
        print(
            "Erro de inicialização: credenciais AWS ausentes. "
            "Defina as variáveis de ambiente obrigatórias antes de executar: "
            + ", ".join(ausentes)
            + ".",
            file=sys.stderr,
        )
        # Encerra o processo com codigo diferente de zero, interrompendo o
        # startup antes de o servidor ser iniciado. (Req 6.3)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Bloco de execucao do script.
# A verificacao de credenciais AWS roda PRIMEIRO, antes de qualquer tentativa
# de iniciar o servidor: se as credenciais estiverem ausentes, o processo e
# encerrado aqui e o servidor nao sobe. (Req 6.1, 6.3)
#
# NOTA (tarefa 6.2): o inicio efetivo do servidor em localhost:5000, com o
# tratamento de porta ocupada (OSError / "Address already in use"), sera
# adicionado nesta secao, logo apos a verificacao de credenciais abaixo.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Passo 1: garante que as credenciais AWS estao presentes antes de seguir.
    verificar_credenciais_aws()

    # Passo 2: inicia o servidor web escutando em localhost na porta 5000.
    # Quando a porta esta livre, o app.run bloqueia e passa a atender
    # requisicoes HTTP nesse endereco. (Req 9.4)
    #
    # A chamada e envolvida em try/except para tratar o caso de a porta 5000 ja
    # estar em uso: nessa situacao o bind do socket falha e o Python levanta um
    # OSError (ex.: "Address already in use"). Capturamos esse erro, exibimos
    # uma mensagem clara em portugues informando que a porta esta indisponivel
    # e encerramos o processo de inicializacao com codigo diferente de zero
    # (sys.exit), sem subir o servidor. (Req 9.5)
    try:
        app.run(host="localhost", port=5000)
    except OSError:
        print(
            "Erro de inicialização: a porta 5000 está indisponível "
            "(já está em uso). Encerre o processo que a utiliza ou libere a "
            "porta antes de executar novamente.",
            file=sys.stderr,
        )
        sys.exit(1)
