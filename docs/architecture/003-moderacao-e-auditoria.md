# ADR 003 — Moderação e auditoria administrativa

## Decisão

Denúncias e gestão administrativa ficam no módulo `moderation`. Uma denúncia pertence ao
usuário que a enviou e pode, opcionalmente, apontar para outra conta. O usuário consulta
somente as próprias denúncias; o conteúdo não é mostrado à conta denunciada.

O painel de gestão exige simultaneamente uma conta do tipo administrador e a permissão
interna de equipe. Superusuários também têm acesso. As mudanças de status de denúncias,
verificação profissional e ativação de contas criam registros de auditoria.

## Motivo

Separar o envio da análise evita expor informações de moderação. Exigir perfil e permissão
administrativos reduz o risco de uma conta comum obter acesso apenas por alteração isolada
de um campo. A auditoria deixa as decisões demonstráveis durante a apresentação do TCC.

## Regras principais

- Denúncias finalizadas exigem um retorno da administração.
- Somente perfis profissionais completos podem receber o indicador de verificado.
- A verificação é administrativa e acadêmica, não oficial de conselho profissional.
- O painel não permite desativar a própria conta nem outras contas administrativas.
- Todas as operações de mudança usam requisições POST protegidas por CSRF.
- Dados exibidos em listagens são limitados ao necessário para cada perfil.

## Avisos administrativos

A administração pode enviar um aviso interno para uma conta específica, para todas as
contas ativas de um perfil ou para todos os usuários não administrativos. Cada envio gera
notificações somente para o público selecionado e registra quantidade, autor e público-alvo
no histórico de avisos e na auditoria. Contas administrativas não participam dos envios em
grupo para reduzir comunicações indevidas.
