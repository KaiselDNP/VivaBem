# VivaBem

Plataforma web acadêmica para organizar solicitações de apoio e facilitar a comunicação
entre pessoas idosas, familiares autorizados e profissionais em Avaré-SP.

> O VivaBem não realiza diagnósticos, não prescreve tratamentos e não substitui o SUS
> nem outros serviços ou profissionais de saúde.

## Stack

- Python 3.14
- Django 5.2 LTS
- PostgreSQL 18
- HTML e CSS renderizados no servidor
- Ruff para verificação de código

## Ambiente local

1. Crie e ative um ambiente virtual Python.
2. Instale `requirements/dev.txt`.
3. Copie `.env.example` para `.env` e preencha apenas valores locais.
4. Crie o banco `vivabem` no PostgreSQL.
5. Execute as migrações e os testes antes de iniciar o servidor. Os testes usam um
   banco SQLite temporário e não alteram os dados locais do PostgreSQL.

As credenciais reais nunca devem ser adicionadas ao Git.

## Funcionalidades disponíveis

- Página inicial pública e responsiva.
- Painel da pessoa idosa organizado por tarefas, com ações grandes e linguagem direta.
- Barra global para ampliar o texto, selecionar um item para ouvir e abrir instruções de ajuda.
- Pedido de ajuda dividido em cinco etapas, com progresso e rascunho temporário na aba.
- Imagens simbólicas sempre acompanhadas de texto.
- Cadastro separado para pessoa idosa e familiar.
- Cadastro da pessoa idosa dividido em quatro etapas curtas.
- Autenticação por e-mail e senha.
- Recuperação de senha por link temporário enviado por e-mail.
- Painel protegido conforme o perfil da conta.
- Perfil pessoal editável com uma única foto privada.
- Perfil profissional com atuação, credencial, modalidade e verificação administrativa.
- Cadastro e acompanhamento de necessidades da pessoa idosa.
- Solicitações de ajuda com ciclo de status: aberta, aceita, concluída ou cancelada.
- Pedido de ajuda completo em um único passo a passo, sem cadastro prévio separado.
- Vínculo familiar dependente da autorização da pessoa idosa.
- Permissões separadas para necessidades, solicitações, interesses e notificações.
- Familiar pode criar um pedido assistido somente quando a pessoa idosa autorizar explicitamente.
- Pesquisa de profissionais por nome, profissão, especialidade, região e modalidade.
- Interesse profissional sujeito à aceitação ou recusa da pessoa idosa.
- Central de notificações privadas com indicador de itens não lidos.
- Chat privado entre pessoas vinculadas, com bloqueio, denúncia e limite de mensagens.
- Moderação do chat bloqueia ameaças, ofensas e pedidos suspeitos de dados ou dinheiro,
  preserva apenas o evento de segurança e avisa a administração.
- Envio e acompanhamento privado de denúncias.
- Painel administrativo para denúncias, profissionais e situação das contas.
- Auditoria das decisões administrativas importantes.
- Avisos internos para uma conta específica ou grupos por tipo de usuário.
- Encerramento de sessão por requisição POST protegida por CSRF.
- Limite temporário de tentativas repetidas de entrada.
- Administração de usuários pelo Django Admin.

## Acessibilidade para o público idoso

O VivaBem prioriza ações simples, botões grandes, contraste, foco de teclado, mensagens claras e
prevenção de erros. Na primeira visita, o sistema pergunta se a pessoa prefere letras bem grandes e
mantém essa escolha nas telas seguintes. A conta de pessoa idosa começa com o texto no tamanho Grande
quando nenhuma preferência anterior foi escolhida. A leitura em voz alta permite
escolher um item sem ativá-lo: o primeiro clique lê, e o próximo volta a funcionar normalmente. No
computador, `F2` ativa esse modo; no celular, o controle permanece no centro da lateral direita.
A voz usa o recurso disponível no navegador e pode variar entre dispositivos. As imagens não
substituem os textos, e nenhuma informação é compartilhada com um familiar sem autorização
explícita.

Essas decisões ainda precisam ser validadas com pessoas idosas reais durante a pesquisa de campo.
O sistema não presume que todas as pessoas com mais de 60 anos possuem as mesmas necessidades.

As senhas precisam ter pelo menos 8 caracteres, mas não exigem símbolos, números ou letras
maiúsculas. Senhas muito comuns ou formadas somente por números continuam bloqueadas. O login com
Google não está ativo porque depende de credenciais externas e configuração de consentimento OAuth.

## E-mail e recuperação de senha

No desenvolvimento local, o link de recuperação é exibido no terminal que executa o servidor.
Para envio real, configure um servidor SMTP pelas variáveis `VIVABEM_EMAIL_*` descritas em
`.env.example`. Nenhuma senha de e-mail deve ser salva no Git.

## Comandos de verificação

```powershell
python manage.py check
python manage.py test --settings=config.settings_test
ruff check .
```

## Documentação

As decisões arquiteturais ficam em `docs/architecture/` para apoiar a explicação do TCC.

- [Fluxograma geral](docs/fluxograma.md)
- [Visão geral funcional](docs/visao-geral-do-sistema.md)
- [Guia de publicação no Render](docs/publicacao-render.md)
- [Revisão final do MVP](docs/revisao-final.md)
- [Decisão de acessibilidade para pessoas idosas](docs/architecture/005-acessibilidade-para-pessoas-idosas.md)
