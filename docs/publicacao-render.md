# Publicação do VivaBem no Render

## Preparação incluída

O repositório possui um `render.yaml` que cria uma aplicação Django e um banco PostgreSQL, além
de um script de construção que instala dependências, coleta arquivos estáticos, aplica migrações
e cria a primeira conta administrativa quando as variáveis necessárias estiverem configuradas.

## Como publicar

1. Envie a versão atualizada para o GitHub.
2. Entre no Render e escolha **New > Blueprint**.
3. Conecte o repositório `KaiselDNP/VivaBem`.
4. Confirme o arquivo `render.yaml`.
5. Informe `VIVABEM_ADMIN_EMAIL` e uma senha forte em `VIVABEM_ADMIN_PASSWORD`.
6. Aplique o Blueprint e aguarde o endereço terminado em `.onrender.com`.
7. Abra `/status/`, a página inicial, o login, o painel e `/admin/`.

Não use a senha normal do seu e-mail e não salve a senha administrativa no Git.

## Limites da opção gratuita

- O banco PostgreSQL gratuito expira após 30 dias.
- O serviço pode ficar inativo e demorar para responder no primeiro acesso.
- Arquivos enviados, como fotos de perfil, podem desaparecer após reinícios ou novas publicações,
  pois o disco da aplicação é temporário.
- O SMTP fica desativado por enquanto.

Para uma demonstração temporária, esses limites são aceitáveis. Para manter o sistema por prazo
maior e preservar fotos, será necessário escolher armazenamento persistente e um banco durável
antes de inserir dados reais.

## Pesquisa de campo

A pesquisa de campo não faz parte desta publicação. Requisitos obtidos futuramente devem ser
avaliados antes de alterar o escopo ou o modelo de dados.
