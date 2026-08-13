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
- Cadastro separado para pessoa idosa e familiar.
- Autenticação por e-mail e senha.
- Painel protegido conforme o perfil da conta.
- Perfil pessoal editável com uma única foto privada.
- Perfil profissional com atuação, credencial, modalidade e verificação administrativa.
- Cadastro e acompanhamento de necessidades da pessoa idosa.
- Solicitações de ajuda com ciclo de status: aberta, aceita, concluída ou cancelada.
- Vínculo familiar dependente da autorização da pessoa idosa.
- Permissões separadas para necessidades, solicitações, interesses e notificações.
- Pesquisa de profissionais por nome, profissão, especialidade, região e modalidade.
- Interesse profissional sujeito à aceitação ou recusa da pessoa idosa.
- Central de notificações privadas com indicador de itens não lidos.
- Envio e acompanhamento privado de denúncias.
- Painel administrativo para denúncias, profissionais e situação das contas.
- Auditoria das decisões administrativas importantes.
- Avisos internos para uma conta específica ou grupos por tipo de usuário.
- Encerramento de sessão por requisição POST protegida por CSRF.
- Administração de usuários pelo Django Admin.

## Comandos de verificação

```powershell
python manage.py check
python manage.py test --settings=config.settings_test
ruff check .
```

## Documentação

As decisões arquiteturais ficam em `docs/architecture/` para apoiar a explicação do TCC.
