# 004 — Segurança, recuperação de acesso e acessibilidade

## Decisão

O VivaBem usa os recursos nativos do Django para gerar tokens temporários de recuperação de
senha e mantém o envio de e-mail configurável por variáveis de ambiente. O sistema também
limita tentativas repetidas de login por combinação de endereço de rede e e-mail, sem guardar
o e-mail diretamente na chave de controle.

Para reduzir a barreira de entrada do público idoso, a senha possui mínimo de 8 caracteres e não
exige composição artificial com símbolos, números ou letras maiúsculas. Senhas comuns e senhas
somente numéricas continuam bloqueadas, o login mantém limitação de tentativas e as senhas são
armazenadas pelo mecanismo de hash do Django. O cadastro da pessoa idosa é apresentado em quatro
etapas curtas.

O login por Google não faz parte desta etapa porque exige credenciais OAuth, tela de consentimento,
domínio e endereços de retorno configurados em uma conta externa. Nenhum botão sem funcionamento é
exibido no protótipo.

As rotas continuam protegidas por autenticação, perfil e propriedade do registro. Mudanças de
estado usam POST e CSRF. Em produção, cookies seguros, HTTPS e HSTS são ativados pelas
configurações documentadas no `.env.example`.

Páginas autenticadas recebem uma política que impede armazenamento no cache do navegador, e
recursos de câmera, microfone e geolocalização permanecem desabilitados porque não fazem parte
do escopo do MVP.

O sistema registra somente o horário aproximado da última atividade autenticada, limitado a uma
gravação a cada dois minutos. O indicador “Online agora” considera os últimos cinco minutos, é
visível apenas para administradores e não armazena páginas visitadas, cliques ou conteúdo.

## Motivo

Essa solução evita criar um mecanismo próprio de tokens e aproveita componentes testados do
Django. As variáveis de ambiente permitem usar o servidor local sem HTTPS e endurecer a
configuração quando o protótipo for publicado.

## Interface e privacidade

O menu autenticado permanece disponível por rolagem horizontal em telas pequenas. Controles
possuem áreas de toque adequadas, foco visível, suporte a alto contraste e redução de movimento.
O aviso de privacidade explica minimização, compartilhamento, conservação e o canal existente
para solicitações relacionadas aos dados pessoais.

## Verificação

Os testes automatizados cobrem recuperação de senha, limitação de tentativas, cabeçalhos de
segurança, CSRF, separação entre perfis, propriedade de registros, revogação de vínculo e uso de
POST nas operações sensíveis.
