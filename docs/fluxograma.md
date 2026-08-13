# Fluxograma geral do VivaBem

```mermaid
flowchart TD
    A[Acesso ao VivaBem] --> B{Possui conta?}
    B -- Não --> C[Escolher perfil e realizar cadastro]
    B -- Sim --> D[Entrar com e-mail e senha]
    C --> D
    D --> E{Perfil de acesso}

    E -- Pessoa idosa --> S1[Atualizar perfil]
    S1 --> S2[Registrar necessidade]
    S2 --> S3[Publicar solicitação de ajuda]
    S3 --> P2
    S3 --> F4

    E -- Familiar --> F1[Solicitar vínculo por e-mail]
    F1 --> F2{Pessoa idosa autoriza?}
    F2 -- Não --> F3[Acesso não liberado]
    F2 -- Sim --> F4[Pessoa idosa define permissões]
    F4 --> F5[Familiar visualiza somente dados autorizados]

    E -- Profissional --> P1[Completar perfil profissional]
    P1 --> P2[Consultar solicitações compatíveis sem identidade do idoso]
    P2 --> P3[Demonstrar interesse]
    P3 --> S4{Pessoa idosa decide}
    S4 -- Recusar --> P4[Profissional recebe a resposta]
    S4 -- Aceitar --> S5[Solicitação vinculada ao profissional]
    S5 --> S6[Concluir ou cancelar solicitação]
    S6 --> N[Notificações aos usuários autorizados]

    E -- Administrador --> G1[Central de gestão]
    G1 --> G2[Analisar profissionais]
    G1 --> G3[Analisar denúncias]
    G1 --> G4[Gerenciar situação das contas]
    G1 --> G5[Enviar avisos]
    G2 --> G6[Registrar auditoria]
    G3 --> G6
    G4 --> G6
    G5 --> G6

    S1 --> R[Registrar denúncia ou solicitação de privacidade]
    F5 --> R
    P1 --> R
    R --> G3
```

## Leitura do fluxo

O acesso começa pelo cadastro ou login. Depois da autenticação, cada pessoa segue apenas as
ações permitidas ao seu perfil. Vínculos familiares dependem de autorização e permissões
específicas. O profissional visualiza a solicitação sem receber a identidade da pessoa idosa
antes do interesse ser aceito. Decisões administrativas importantes geram auditoria.
