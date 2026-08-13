# ADR 002 — Vínculos, permissões e notificações

## Decisão

O vínculo entre uma pessoa idosa e um familiar possui status próprio e só libera acesso
depois da aprovação da pessoa idosa. As autorizações ficam em um registro separado, com
uma opção para cada grupo de informação. Todas começam desativadas.

Interesses profissionais pertencem a uma solicitação de ajuda. Somente a pessoa idosa
dona da solicitação pode aceitar ou recusar, e o banco permite apenas um interesse aceito
por solicitação.

As notificações são persistidas no banco e sempre possuem um destinatário. A consulta e
a ação de marcar como lida são filtradas pelo usuário autenticado.

## Motivo

Essa estrutura aplica o princípio do menor privilégio, deixa o consentimento demonstrável
no TCC e evita concentrar permissões em um único campo genérico. Ela também mantém um
histórico simples das respostas sem criar um prontuário médico.

## Limites do MVP

- Não existe diagnóstico, prescrição ou integração com serviços de saúde.
- O selo profissional indica somente análise administrativa do protótipo.
- Notificações ficam dentro da plataforma; não há envio real por SMS ou aplicativo.
- Dados de contato pessoais não aparecem na lista pública de profissionais ou nas
  oportunidades.
