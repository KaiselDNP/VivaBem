# Visão geral funcional do VivaBem

## Objetivo

O VivaBem é uma plataforma web acadêmica voltada inicialmente à população idosa de Avaré-SP.
Seu objetivo é organizar necessidades e solicitações de apoio, aproximar profissionais e permitir
o acompanhamento de familiares autorizados. O sistema não realiza diagnósticos, não prescreve
tratamentos e não substitui o SUS ou profissionais de saúde.

## Perfis de acesso

### Pessoa idosa

- Cria a conta e mantém o próprio perfil, inclusive uma foto privada.
- Registra, edita e encerra necessidades.
- Publica solicitações de ajuda vinculadas às próprias necessidades.
- Analisa interesses enviados por profissionais e decide aceitar ou recusar.
- Autoriza vínculos familiares e controla cada permissão individualmente.
- Acompanha notificações, solicitações e denúncias criadas pela própria conta.

### Familiar

- Cria a conta e solicita vínculo usando o e-mail da pessoa idosa.
- Aguarda a autorização antes de visualizar qualquer informação.
- Acessa somente as categorias liberadas: necessidades, solicitações ou interesses profissionais.
- Recebe atualizações apenas quando a permissão de notificação estiver ativa.
- Não altera necessidades, solicitações nem permissões da pessoa idosa.

### Profissional

- Cria a conta e informa profissão, especialidade, região, modalidade e credencial aplicável.
- Pesquisa solicitações abertas compatíveis sem visualizar a identidade da pessoa idosa.
- Envia uma apresentação de interesse e aguarda a decisão da pessoa idosa.
- Recebe o resultado por notificação.
- Exibe um status de verificação administrativa do protótipo, sem representar fiscalização oficial
  de conselho profissional.

### Administrador

- Consulta indicadores de usuários, denúncias e profissionais.
- Analisa denúncias e envia retorno a quem registrou.
- Analisa cadastros profissionais e altera seu status de verificação.
- Ativa ou desativa contas comuns, sem alterar outras contas administrativas.
- Envia avisos individuais ou por perfil.
- Consulta o histórico de decisões administrativas relevantes.

## Módulos disponíveis

1. Cadastro, login, logout e recuperação de senha por link temporário.
2. Perfil pessoal e perfil profissional.
3. Necessidades e solicitações de ajuda.
4. Vínculos familiares e permissões específicas.
5. Diretório de profissionais e busca por atuação, região e modalidade.
6. Interesses profissionais e resposta da pessoa idosa.
7. Notificações privadas.
8. Denúncias e solicitações relacionadas à privacidade.
9. Central de gestão e Django Admin.
10. Auditoria administrativa.

## Regras centrais

- Toda área privada exige autenticação.
- O perfil da conta define quais módulos podem ser acessados.
- Objetos privados são filtrados pelo proprietário ou pelo vínculo autorizado.
- Um familiar começa sem permissões, mesmo depois da aprovação do vínculo.
- Uma solicitação aceita pode possuir somente um interesse profissional aceito.
- Operações sensíveis usam POST e proteção CSRF.
- Senhas são armazenadas por hash; nunca em texto puro.
- Páginas autenticadas não são armazenadas no cache do navegador.
- O login recebe limitação temporária após tentativas repetidas.

## Arquitetura

O sistema é um monólito Django 5.2 com páginas HTML renderizadas no servidor e CSS próprio. O
banco principal é PostgreSQL. A autenticação utiliza o modelo de usuário do Django adaptado para
e-mail e perfil. Os módulos são separados em aplicações Django para contas, perfis,
profissionais, necessidades, vínculos, notificações, moderação e páginas institucionais.

Em publicação, Gunicorn executa a aplicação, WhiteNoise entrega os arquivos estáticos e uma URL
de conexão configura o PostgreSQL. Segredos e credenciais permanecem em variáveis de ambiente.

## Dados principais

- Usuário e perfil pessoal.
- Perfil e credencial profissional.
- Necessidade, solicitação de ajuda e interesse profissional.
- Vínculo familiar e permissões.
- Notificação.
- Denúncia, aviso administrativo e registro de auditoria.

## Privacidade e limites

O sistema aplica minimização de dados, autorização explícita para familiares e separação por
perfil. Solicitações de acesso, correção ou exclusão podem ser registradas pela categoria de
privacidade na área de denúncias. Como se trata de um protótipo acadêmico, não devem ser
armazenados prontuários, documentos, diagnósticos ou dados médicos detalhados.

## Validação atual

A suíte automatizada verifica autenticação, recuperação de senha, perfis, propriedade de dados,
permissões familiares, solicitações, interesses profissionais, notificações, denúncias,
administração, CSRF e cabeçalhos de segurança. A pesquisa de campo ainda será realizada e seus
resultados não fazem parte desta documentação.
