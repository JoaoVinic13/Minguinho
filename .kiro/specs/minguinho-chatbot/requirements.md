# Documento de Requisitos

## Introdução

O Minguinho é um chatbot web fofinho, curioso e amigável, especializado em conversar sobre jogos, séries de TV, livros, animes e artistas. O Minguinho tem um tom doce e acolhedor, usa emojis e palavras confortantes de forma equilibrada (nunca enjoativa) e possui conhecimento amplo e profundo sobre cultura pop, embora reconheça que esportes não é um tema que domina bem. A aplicação é um projeto Flask mínimo e didático: uma página de chat em `templates/index.html` servida pela rota `/`, e uma rota `/chat` (POST) que recebe a mensagem do usuário e devolve a resposta gerada pelo modelo Claude Haiku da Amazon via Amazon Bedrock. A personalidade, o tom e os limites de assunto do bot são definidos por uma constante `SYSTEM_PROMPT` dentro de `app.py`. O projeto não usa banco de dados, autenticação nem testes automatizados, priorizando poucos arquivos e código simples comentado em português.

## Glossário

- **Minguinho**: O assistente de chat (o bot), com personalidade fofinha, curiosa, acolhedora e calorosa; usa emojis e palavras confortantes de forma equilibrada (sem exagero ou tom enjoativo), tem conhecimento amplo e profundo sobre cultura pop (jogos, séries de TV, livros, animes e artistas) e reconhece que esportes não é um tema que domina bem.
- **Aplicacao_Flask**: O servidor web em Python construído com Flask, com `app.py` na raiz do projeto.
- **Pagina_Chat**: A interface de chat renderizada a partir de `templates/index.html`.
- **Rota_Chat**: O endpoint HTTP `/chat`, que aceita requisições POST com o corpo JSON `{"message": "..."}`.
- **Rota_Raiz**: O endpoint HTTP `/`, que exibe a Pagina_Chat.
- **Servico_Bedrock**: O cliente `bedrock-runtime` do boto3 que invoca o modelo via `invoke_model` na região `us-east-1`.
- **Model_ID**: O identificador do perfil de inferência do modelo: `us.anthropic.claude-haiku-4-5-20251001-v1:0`.
- **SYSTEM_PROMPT**: A constante em `app.py` que define a personalidade, o tom e os limites de assunto do Minguinho.
- **Mensagem_Usuario**: O texto enviado pelo usuário no campo `message` do corpo JSON da Rota_Chat.
- **Resposta_Bot**: O texto devolvido pela Rota_Chat no campo `reply` do corpo JSON.
- **Variaveis_Ambiente**: As variáveis de ambiente do sistema operacional usadas para fornecer as credenciais AWS.

## Requisitos

### Requisito 1: Exibição da página de chat

**História de Usuário:** Como visitante, eu quero acessar a página inicial da aplicação, para que eu possa ver a interface de chat do Minguinho.

#### Critérios de Aceitação

1. WHEN uma requisição GET é recebida na Rota_Raiz, THE Aplicacao_Flask SHALL renderizar a Pagina_Chat a partir de `templates/index.html`.
2. IF o arquivo `templates/index.html` não puder ser carregado durante a renderização da Pagina_Chat, THEN THE Aplicacao_Flask SHALL retornar uma resposta de erro indicando que a página não pôde ser exibida, sem encerrar a Aplicacao_Flask.
3. THE Pagina_Chat SHALL apresentar um campo de entrada de texto que aceita de 1 a 2000 caracteres para a Mensagem_Usuario e um controle para enviar a Mensagem_Usuario.
4. WHEN uma Mensagem_Usuario é enviada ou uma Resposta_Bot é recebida, THE Pagina_Chat SHALL anexar a mensagem correspondente ao histórico exibido no navegador, mantendo a ordem cronológica das mensagens.
5. THE Pagina_Chat SHALL exibir o histórico de mensagens trocadas na sessão corrente do navegador, armazenado apenas em memória do navegador e descartado ao recarregar ou fechar a página.

### Requisito 2: Processamento de mensagem do usuário

**História de Usuário:** Como usuário, eu quero enviar uma mensagem ao Minguinho, para que eu receba uma resposta sobre jogos, séries, livros, animes ou artistas.

#### Critérios de Aceitação

1. WHEN uma requisição POST com cabeçalho `Content-Type: application/json` e corpo JSON contendo um campo `message` cujo texto, após remoção de espaços em branco nas extremidades, não está vazio é recebida na Rota_Chat, THE Aplicacao_Flask SHALL encaminhar o texto da Mensagem_Usuario ao Servico_Bedrock.
2. WHEN o Servico_Bedrock retorna a Resposta_Bot para a Rota_Chat, THE Aplicacao_Flask SHALL devolver o texto da Resposta_Bot no campo `reply` de um corpo JSON com o código de status HTTP 200.
3. THE Rota_Chat SHALL aceitar o corpo da requisição no formato JSON `{"message": "..."}` com cabeçalho `Content-Type: application/json`.
4. THE Rota_Chat SHALL devolver o corpo da resposta no formato JSON `{"reply": "..."}`.

### Requisito 3: Validação de mensagem vazia

**História de Usuário:** Como mantenedor, eu quero rejeitar mensagens vazias, para que a aplicação não faça chamadas desnecessárias ao modelo.

#### Critérios de Aceitação

1. IF uma requisição POST na Rota_Chat não contém o campo `message`, THEN THE Aplicacao_Flask SHALL responder com o código de status HTTP 400.
2. IF uma requisição POST na Rota_Chat contém o campo `message` cujo conteúdo, após a remoção de espaços, tabulações e quebras de linha no início e no fim, resulta em texto com comprimento igual a 0, THEN THE Aplicacao_Flask SHALL responder com o código de status HTTP 400.
3. WHEN a Rota_Chat responde com o código de status HTTP 400 por mensagem ausente ou vazia, THE Aplicacao_Flask SHALL incluir no corpo JSON um campo de erro contendo texto em português que identifique que a mensagem é obrigatória e não pode estar vazia.
4. IF uma requisição POST na Rota_Chat possui corpo ausente ou que não seja um JSON válido, THEN THE Aplicacao_Flask SHALL responder com o código de status HTTP 400 e incluir no corpo JSON um campo de erro em português indicando que o corpo da requisição é inválido.
5. WHEN uma requisição POST na Rota_Chat é rejeitada com o código de status HTTP 400 por mensagem ausente, vazia ou corpo inválido, THE Aplicacao_Flask SHALL não realizar nenhuma chamada ao Servico_Bedrock.

### Requisito 4: Geração de resposta pelo Amazon Bedrock

**História de Usuário:** Como usuário, eu quero que as respostas sejam geradas por um modelo de linguagem da Amazon Bedrock, para que a conversa seja fluida e contextualizada.

#### Critérios de Aceitação

1. WHEN a Rota_Chat precisa gerar a Resposta_Bot, THE Servico_Bedrock SHALL invocar o modelo por meio do cliente `bedrock-runtime` do boto3 usando a operação `invoke_model` na região `us-east-1`.
2. THE Servico_Bedrock SHALL utilizar o Model_ID `us.anthropic.claude-haiku-4-5-20251001-v1:0` em todas as invocações.
3. WHEN o Servico_Bedrock invoca o modelo, THE Aplicacao_Flask SHALL incluir, na requisição ao modelo, o conteúdo da constante SYSTEM_PROMPT e o texto da Mensagem_Usuario recebida na Rota_Chat.
4. WHEN o Servico_Bedrock retorna a resposta do modelo, THE Aplicacao_Flask SHALL extrair o texto gerado pelo modelo e atribuí-lo ao campo `reply` da Resposta_Bot.
5. IF o Servico_Bedrock retorna uma resposta sem texto gerado ou com texto vazio, THEN THE Aplicacao_Flask SHALL tratar a situação como falha de invocação, respondendo com o código de status HTTP 502 e incluindo no corpo JSON uma mensagem de erro descritiva em português.

### Requisito 5: Personalidade e limites do Minguinho

**História de Usuário:** Como usuário, eu quero conversar com um assistente fofinho, acolhedor e focado em cultura pop, para que a experiência seja temática, calorosa e consistente.

#### Critérios de Aceitação

1. THE SYSTEM_PROMPT SHALL definir a identidade do bot com o nome "Minguinho" e com tom curioso e amigável, instruindo-o a fazer perguntas de acompanhamento sobre os temas suportados.
2. THE SYSTEM_PROMPT SHALL instruir o Minguinho a conversar exclusivamente sobre os cinco temas suportados: jogos, séries de TV, livros, animes e artistas.
3. THE SYSTEM_PROMPT SHALL instruir o Minguinho a redigir a Resposta_Bot em português.
4. THE SYSTEM_PROMPT SHALL residir como uma constante em `app.py`.
5. WHEN a Mensagem_Usuario trata de um assunto fora dos cinco temas suportados (jogos, séries de TV, livros, animes e artistas), THE Minguinho SHALL, conforme instruído pelo SYSTEM_PROMPT, indicar na Resposta_Bot que o assunto está fora do seu escopo e propor ao usuário a retomada da conversa em pelo menos um dos temas suportados.
6. THE SYSTEM_PROMPT SHALL definir a identidade do Minguinho como fofinho, bonitinho, caloroso e acolhedor, com tom doce que não seja enjoativo nem exagerado.
7. THE SYSTEM_PROMPT SHALL instruir o Minguinho a usar emojis e palavras confortantes na Resposta_Bot de forma equilibrada, limitando o uso de emojis a no máximo 3 por Resposta_Bot.
8. THE SYSTEM_PROMPT SHALL instruir o Minguinho a demonstrar conhecimento amplo e profundo sobre cultura pop, abrangendo jogos, séries de TV, livros, animes e artistas.
9. WHEN a Mensagem_Usuario trata de esportes, THE Minguinho SHALL, conforme instruído pelo SYSTEM_PROMPT, reconhecer de forma gentil e acolhedora na Resposta_Bot que esportes não é um tema que domina bem e propor ao usuário a retomada da conversa em pelo menos um dos cinco temas suportados.

### Requisito 6: Gestão de credenciais AWS

**História de Usuário:** Como mantenedor, eu quero que as credenciais AWS venham apenas de variáveis de ambiente, para que nenhuma chave fique exposta no código-fonte.

#### Critérios de Aceitação

1. THE Aplicacao_Flask SHALL obter as credenciais AWS exclusivamente a partir das Variaveis_Ambiente.
2. THE Aplicacao_Flask SHALL manter o código-fonte livre de chaves de acesso AWS literais.
3. IF as Variaveis_Ambiente com as credenciais AWS não estiverem definidas no início da execução, THEN THE Aplicacao_Flask SHALL interromper a inicialização e registrar uma mensagem indicando a ausência das credenciais.
4. IF uma requisição ao Servico_Bedrock falhar por credenciais AWS inválidas, THEN THE Aplicacao_Flask SHALL responder na Rota_Chat com uma mensagem indicando falha de autenticação com a AWS, sem expor os valores das credenciais.

### Requisito 7: Formatação de respostas JSON com acentuação

**História de Usuário:** Como usuário de língua portuguesa, eu quero que as respostas JSON preservem os acentos, para que o texto seja legível.

#### Critérios de Aceitação

1. THE Aplicacao_Flask SHALL configurar `app.json.ensure_ascii = False`.
2. WHEN a Aplicacao_Flask devolve qualquer corpo JSON (incluindo a Resposta_Bot e as mensagens de erro em português), THE Aplicacao_Flask SHALL preservar os caracteres acentuados do português (incluindo á, â, ã, à, é, ê, í, ó, ô, õ, ú, ç e suas maiúsculas) codificados em UTF-8, sem convertê-los em sequências de escape ASCII (`\uXXXX`).
3. WHEN a Aplicacao_Flask devolve qualquer corpo JSON, THE Aplicacao_Flask SHALL indicar a codificação UTF-8 no cabeçalho `Content-Type` da resposta.

### Requisito 8: Tratamento de falhas na invocação do modelo

**História de Usuário:** Como usuário, eu quero receber uma indicação clara quando o serviço de IA falhar, para que eu entenda que ocorreu um problema em vez de ver a aplicação travar.

#### Critérios de Aceitação

1. IF o Servico_Bedrock levanta uma exceção durante a invocação do modelo, THEN THE Aplicacao_Flask SHALL responder com o código de status HTTP 502.
2. WHEN a Aplicacao_Flask responde com o código de status HTTP 502, THE Aplicacao_Flask SHALL incluir no corpo JSON um campo de erro em português que indique que o serviço de IA falhou, sem expor detalhes internos da exceção.
3. WHEN o Servico_Bedrock levanta uma exceção durante a invocação do modelo, THE Aplicacao_Flask SHALL permanecer em execução e continuar aceitando novas requisições na Rota_Chat.

### Requisito 9: Estrutura e dependências do projeto

**História de Usuário:** Como mantenedor, eu quero um projeto mínimo com dependências declaradas, para que a aplicação seja fácil de instalar e executar.

#### Critérios de Aceitação

1. THE Aplicacao_Flask SHALL ter o arquivo `app.py` na raiz do projeto.
2. THE Aplicacao_Flask SHALL ter a Pagina_Chat no arquivo `templates/index.html`.
3. THE Aplicacao_Flask SHALL declarar as dependências `flask` e `boto3` no arquivo `requirements.txt`.
4. WHEN o comando `python app.py` é executado e a porta `5000` está disponível, THE Aplicacao_Flask SHALL iniciar o servidor web escutando em `localhost` na porta `5000` e passar a responder a requisições HTTP nesse endereço em até 10 segundos.
5. IF a porta `5000` já está em uso no momento da inicialização, THEN THE Aplicacao_Flask SHALL encerrar o processo de inicialização e exibir uma mensagem de erro indicando que a porta está indisponível.
