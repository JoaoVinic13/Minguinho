# Plano de Implementação: Minguinho (chatbot)

## Visão Geral

Este plano converte o design do Minguinho em passos incrementais de implementação para um projeto Flask mínimo e didático, composto por exatamente três arquivos: `app.py` (na raiz), `templates/index.html` e `requirements.txt`. Cada passo constrói sobre o anterior e termina com a integração das partes, sem deixar código órfão.

Observações importantes sobre verificação:

- O steering do projeto **proíbe testes automatizados**. Portanto, este plano **não contém nenhuma tarefa de escrita de testes** (sem testes unitários, de integração ou de propriedade).
- A verificação é feita por **inspeção de código e testes exploratórios manuais**, conforme o "Plano de verificação manual" do design.
- Todo o código é comentado em português e as credenciais AWS vêm apenas de variáveis de ambiente.

## Tarefas

- [x] 1. Criar o arquivo de dependências do projeto
  - Criar `requirements.txt` na raiz declarando exatamente `flask` e `boto3`.
  - Garantir que não há outras dependências (sem FastAPI, Django, LangChain, SDKs de outras IAs).
  - _Requisitos: 9.3_

- [x] 2. Estruturar o `app.py` com configuração base do Flask e integração Bedrock
  - [x] 2.1 Criar o esqueleto do `app.py` e a configuração JSON/UTF-8
    - Criar `app.py` na raiz com a instância Flask (`app = Flask(__name__)`).
    - Definir `app.json.ensure_ascii = False` para preservar acentos nas respostas JSON.
    - Importar módulos necessários (`os`, `json`, `boto3`, `Flask`, `render_template`, `request`, `jsonify`).
    - Comentar o código em português.
    - _Requisitos: 7.1, 7.2, 7.3, 9.1_

  - [x] 2.2 Definir a constante SYSTEM_PROMPT com a personalidade do Minguinho
    - Adicionar a constante `SYSTEM_PROMPT` em `app.py` como texto em português.
    - Incluir: identidade e nome "Minguinho"; tom fofinho, bonitinho, caloroso e acolhedor, doce sem ser enjoativo nem exagerado; curiosidade e amigabilidade com perguntas de acompanhamento.
    - Restringir o escopo exclusivamente aos cinco temas: jogos, séries de TV, livros, animes e artistas, demonstrando conhecimento amplo e profundo de cultura pop.
    - Instruir a responder sempre em português e a usar emojis e palavras confortantes de forma equilibrada (máximo de 3 emojis por resposta).
    - Instruir o redirecionamento gentil quando o assunto estiver fora dos cinco temas, propondo retomar em pelo menos um tema suportado.
    - Instruir o reconhecimento gentil e acolhedor de que esportes não é um tema dominado, propondo retomar em pelo menos um dos cinco temas.
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [x] 2.3 Criar o cliente `bedrock-runtime` e a constante do Model ID
    - Instanciar o cliente boto3 uma vez na inicialização: `boto3.client("bedrock-runtime", region_name="us-east-1")`.
    - Definir constante com o Model ID exatamente `us.anthropic.claude-haiku-4-5-20251001-v1:0`.
    - Garantir que nenhuma chave de acesso AWS literal apareça no código (credenciais resolvidas pelo boto3 via variáveis de ambiente).
    - _Requisitos: 4.1, 4.2, 6.1, 6.2_

- [x] 3. Implementar a função de invocação do Bedrock e extração do texto
  - [x] 3.1 Montar o corpo de invocação e chamar `invoke_model`
    - Escrever função que monta o corpo JSON no formato da Anthropic Messages API: `anthropic_version`, `max_tokens`, `system` (recebendo o SYSTEM_PROMPT) e `messages` (com a Mensagem_Usuario como bloco de texto do papel `user`).
    - Serializar o corpo e chamar `invoke_model` com o Model ID correto.
    - _Requisitos: 4.1, 4.2, 4.3_

  - [x] 3.2 Extrair o texto gerado da resposta do modelo
    - Ler o `body` da resposta, percorrer os blocos de `content` do tipo `text` e extrair o texto gerado.
    - Retornar o texto extraído para a rota; sinalizar quando o texto estiver ausente ou vazio para posterior tratamento como falha.
    - _Requisitos: 4.4, 4.5_

- [x] 4. Implementar a rota raiz `GET /`
  - [x] 4.1 Renderizar a página de chat com tratamento de erro
    - Criar a rota `GET /` que renderiza `templates/index.html` via `render_template`.
    - Envolver a renderização em tratamento de erro: se o template não puder ser carregado/renderizado, responder HTTP 500 com mensagem indicando que a página não pôde ser exibida, sem derrubar o processo.
    - _Requisitos: 1.1, 1.2_

- [x] 5. Implementar a rota `POST /chat`
  - [x] 5.1 Implementar a validação de entrada (400 sem chamar o Bedrock)
    - Ler o corpo JSON de forma tolerante (`silent`); se o corpo estiver ausente ou não for JSON válido, responder 400 com `{ "error": ... }` em português indicando corpo inválido.
    - Se o campo `message` estiver ausente, responder 400 com erro em português indicando que a mensagem é obrigatória.
    - Aplicar `strip()` ao `message`; se o texto resultante tiver comprimento 0, responder 400 com a mesma mensagem.
    - Garantir que em qualquer caso de 400 nenhuma invocação ao Bedrock é feita.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.2 Encaminhar mensagem válida ao Bedrock e responder sucesso/falha
    - Para mensagem válida (não-vazia após `strip()`), chamar a função de invocação do Bedrock com o texto.
    - Em caso de sucesso com texto não-vazio, responder HTTP 200 com corpo JSON `{ "reply": <texto> }` (via `jsonify`).
    - Se a resposta do modelo não contiver texto ou vier vazia, responder HTTP 502 com `{ "error": ... }` descritivo em português.
    - Envolver a invocação em `try/except`: em qualquer exceção, responder HTTP 502 com erro em português genérico, sem expor detalhes internos da exceção nem valores de credenciais AWS, mantendo o servidor em execução.
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 4.5, 6.4, 8.1, 8.2, 8.3_

- [x] 6. Implementar a inicialização e o bloco de execução em `app.py`
  - [x] 6.1 Verificar credenciais AWS no startup
    - Antes de iniciar o servidor, checar a presença das variáveis de ambiente essenciais (`AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`).
    - Se ausentes, registrar mensagem clara em português indicando a ausência de credenciais e interromper a inicialização (encerrar com código de erro), sem iniciar o servidor.
    - _Requisitos: 6.1, 6.3_

  - [x] 6.2 Iniciar o servidor em localhost:5000 com tratamento de porta ocupada
    - No bloco `if __name__ == "__main__":`, iniciar o servidor escutando em `localhost` na porta `5000`.
    - Capturar o erro de bind (ex.: `OSError`/"Address already in use") e, se a porta 5000 estiver ocupada, exibir mensagem de erro indicando que a porta está indisponível e encerrar o processo de inicialização.
    - _Requisitos: 9.4, 9.5_

- [x] 7. Implementar a interface de chat em `templates/index.html`
  - [x] 7.1 Criar a estrutura e os controles da página de chat
    - Criar `templates/index.html` com um campo de entrada de texto que aceita de 1 a 2000 caracteres para a Mensagem_Usuario e um controle de envio.
    - Incluir uma área visível para o histórico de mensagens.
    - _Requisitos: 1.3, 9.2_

  - [x] 7.2 Implementar o envio via fetch e o histórico cronológico em memória
    - Adicionar JavaScript que faz `POST /chat` com `Content-Type: application/json` e corpo `{ "message": ... }` e lê o campo `reply` da resposta.
    - Ao enviar uma Mensagem_Usuario e ao receber uma Resposta_Bot, anexar cada mensagem ao histórico exibido na ordem cronológica.
    - Manter o histórico apenas em memória da página (array em JS), sem `localStorage`, cookies ou qualquer persistência, de modo que seja descartado ao recarregar ou fechar a página.
    - Exibir mensagens de erro retornadas pelo servidor (400/502) de forma legível no histórico/UI.
    - _Requisitos: 1.4, 1.5_

- [x] 8. Verificação manual final do fluxo completo
  - Seguir o "Plano de verificação manual" do design para confirmar o comportamento do sistema integrado (sem testes automatizados):
  - Validação de entrada: via `curl`/navegador, enviar (a) corpo não-JSON, (b) JSON sem `message`, (c) `message` só com espaços; esperar 400 com `error` em português e confirmar, pelos logs, que o Bedrock não foi chamado. _(Reqs 3.1–3.5)_
  - Fluxo de sucesso: enviar pergunta válida sobre um tema suportado e esperar 200 com `reply` não-vazio; inspecionar o código para confirmar Model ID e corpo (`system` + `messages`). _(Reqs 2.1, 2.2, 4.1–4.4)_
  - Falhas do modelo: observar resposta 502 com `error` em português, sem detalhes internos, e confirmar que o servidor segue respondendo. _(Reqs 4.5, 8.1–8.3)_
  - Não-vazamento de credenciais: inspecionar respostas de erro para garantir ausência de valores de credenciais. _(Req 6.4)_
  - Acentuação JSON: confirmar que não há sequências `\uXXXX` e que o `Content-Type` traz `charset=utf-8`. _(Reqs 7.1–7.3)_
  - Histórico do navegador: trocar várias mensagens, verificar ordem cronológica e confirmar descarte ao recarregar a página. _(Reqs 1.4, 1.5)_
  - Inicialização: verificar startup com e sem credenciais e com a porta 5000 ocupada. _(Reqs 6.3, 9.4, 9.5)_
  - Personalidade: inspecionar o `SYSTEM_PROMPT` e validar com amostras de conversa exploratórias (nome, tom, temas, limite de emojis, redirecionamentos de fora de escopo e esportes, idioma). _(Req 5.1–5.9)_

## Notas

- O projeto usa exatamente três arquivos: `app.py`, `templates/index.html` e `requirements.txt`.
- Não há tarefas de testes automatizados porque o steering os proíbe; a verificação é manual.
- Cada tarefa referencia os requisitos específicos que implementa, para rastreabilidade.
- As tarefas são incrementais: cada passo constrói sobre o anterior e termina com a integração das partes.
- Credenciais AWS somente por variáveis de ambiente; nenhuma chave literal no código.
- Código comentado em português, mantendo o caráter mínimo e didático.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "7.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2"] },
    { "id": 6, "tasks": ["4.1"] },
    { "id": 7, "tasks": ["5.1"] },
    { "id": 8, "tasks": ["5.2"] },
    { "id": 9, "tasks": ["6.1"] },
    { "id": 10, "tasks": ["6.2", "7.2"] }
  ]
}
```
