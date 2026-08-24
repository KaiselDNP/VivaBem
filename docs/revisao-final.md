# Revisão final do MVP

## Verificações automatizadas

- Cadastro, login, logout, recuperação de senha e limitação de tentativas.
- Separação entre pessoa idosa, familiar, profissional e administrador.
- Propriedade de necessidades, solicitações, notificações e denúncias.
- Vínculos, revogação e permissões familiares específicas.
- Interesse profissional, aceitação, recusa e conclusão de solicitação.
- Operações sensíveis por POST e proteção CSRF.
- Cabeçalhos de segurança e bloqueio de cache privado.
- Criação segura da primeira conta administrativa na publicação.
- Compilação dos templates, migrações e arquivos estáticos de produção.

## Responsividade e acessibilidade

- Painel da pessoa idosa prioriza três tarefas concretas em vez de nomes técnicos dos módulos.
- Pedido de ajuda apresenta uma pergunta por etapa e mantém alternativa funcional sem JavaScript.
- Barra global permite ampliar o texto, ouvir o conteúdo e abrir a central de ajuda.
- Imagens simbólicas permanecem acompanhadas por texto e ocultas de leitores de tela quando são
  apenas decorativas.
- Formulários apresentam resumo dos erros e preservam as respostas durante a correção.
- Ações de cancelamento, recusa e retirada de acesso pedem confirmação explícita.
- Conteúdo limitado por largura máxima, sem impedir o uso em telas grandes.
- Grades passam para uma coluna em telas menores.
- Tabelas administrativas permitem rolagem horizontal.
- Menu autenticado permanece disponível por rolagem horizontal no celular.
- Botões e campos possuem tamanho adequado para toque.
- Foco de teclado visível, link para pular ao conteúdo e regiões com nomes acessíveis.
- Modo escuro, alto contraste forçado e redução de movimento são respeitados.

## Conferência manual antes da apresentação

Como etapa final de qualquer publicação, abrir em computador e celular:

1. Página inicial, cadastro, login e recuperação de senha.
2. Painel e edição de perfil de cada tipo de usuário.
3. Necessidades, solicitações, vínculos e oportunidades.
4. Notificações e denúncias.
5. Central de gestão e Django Admin em modo claro e escuro.

Confirmar que não há textos cortados, rolagem horizontal fora das tabelas, botões sobrepostos ou
campos difíceis de tocar. Esta conferência deve ser repetida após mudanças vindas da pesquisa de
campo.
