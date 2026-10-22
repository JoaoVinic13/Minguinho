# Minguinho

O Minguinho é um chatbot web fofinho e acolhedor sobre cultura pop. Ele conversa
exclusivamente sobre cinco temas: jogos, séries de TV, livros, animes e artistas.
O projeto é mínimo e didático, feito com Flask no backend e uma interface de chat
delicada, em estilo kawaii, com paleta de tons de rosa pastel.

As respostas são geradas pelo Amazon Bedrock usando o modelo Claude Haiku, e o bot
mantém a memória da conversa enquanto o servidor está no ar.

## Funcionalidades

- Interface de chat única, centralizada, com design delicado e minimalista.
- Mascote original do Minguinho desenhado em SVG (sem imagens externas).
- Respostas geradas pelo Amazon Bedrock (Claude Haiku) via boto3.
- Memória de conversa: o histórico é guardado em memória e enviado inteiro ao
  modelo a cada pergunta, dando continuidade ao papo.
- Personalidade docinha e regras de estilo definidas na constante `SYSTEM_PROMPT`.
- Validação de entrada e tratamento de erros com mensagens claras em português.

## Tecnologias

- Python com Flask
- Amazon Bedrock (bedrock-runtime) via boto3
- HTML, CSS e JavaScript puro no frontend

## Estrutura do projeto

```
.
├── app.py              # Aplicação Flask: rotas, SYSTEM_PROMPT, integração com o Bedrock
├── requirements.txt    # Dependências (flask, boto3)
└── templates/
    └── index.html      # Interface de chat (HTML, CSS e JS)
```

## Pré-requisitos

- Python 3
- Uma conta AWS com acesso ao Amazon Bedrock na região `us-east-1` e permissão
  para o modelo Claude Haiku.
- Credenciais AWS configuradas por variáveis de ambiente (nunca no código).

## Configuração das credenciais

As credenciais são lidas apenas de variáveis de ambiente. Antes de rodar, exporte:

```bash
export AWS_ACCESS_KEY_ID="sua-access-key"
export AWS_SECRET_ACCESS_KEY="sua-secret-key"
# Opcional, se você usa credenciais temporárias:
export AWS_SESSION_TOKEN="seu-session-token"
```

Se `AWS_ACCESS_KEY_ID` ou `AWS_SECRET_ACCESS_KEY` não estiverem definidas, o app
avisa e não inicia.

## Instalação

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
python app.py
```

O servidor sobe em `http://localhost:5000`. Abra esse endereço no navegador para
conversar com o Minguinho.

## Como funciona

- A rota `/` exibe a página de chat (`templates/index.html`).
- A rota `/chat` (POST) recebe um JSON no formato `{"message": "..."}` e devolve
  `{"reply": "..."}`. Mensagem vazia retorna erro 400.
- As respostas vêm do Amazon Bedrock pela operação `invoke_model`, na região
  `us-east-1`, usando o perfil de inferência do Claude Haiku.
- O histórico da conversa fica em uma lista em memória no `app.py`. Ele é enviado
  por inteiro ao modelo a cada pergunta e é descartado quando o servidor reinicia
  (não há banco de dados).

## Sobre o Minguinho

A personalidade do bot vive na constante `SYSTEM_PROMPT`, dentro do `app.py`. Em
resumo, o Minguinho:

- Fala sempre em português, com tom docinho, meigo e acolhedor.
- Responde em parágrafos curtos, sem listas, preferindo analogias curtas.
- Conversa só sobre jogos, séries de TV, livros, animes e artistas, e redireciona
  com carinho quando o assunto foge desses temas.
