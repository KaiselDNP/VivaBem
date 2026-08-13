# ADR 001 — Monólito Django com PostgreSQL

## Status

Aceita em 13 de agosto de 2026.

## Contexto

O VivaBem é um MVP acadêmico com autenticação, diferentes perfis, dados relacionais,
permissões e uma área administrativa. O projeto precisa ser compreensível, seguro e
possível de manter por um estudante de ADS.

## Decisão

Usar um monólito modular em Django 5.2 LTS, páginas renderizadas no servidor e
PostgreSQL. Cada domínio será uma aplicação Django, compartilhando uma única base de
dados e um único processo de implantação.

O usuário personalizado foi criado antes da primeira migração. A autenticação usa
e-mail como identificador e o papel do usuário diferencia pessoa idosa, familiar,
profissional e administrador.

## Motivos

- O Django reúne autenticação, ORM, migrações, proteção CSRF, validação e administração.
- O PostgreSQL atende bem aos vínculos e permissões relacionais do sistema.
- Um monólito evita a complexidade operacional de microsserviços e de uma SPA separada.
- A separação por aplicações mantém os módulos explicáveis na apresentação do TCC.

## Consequências

- Toda autorização continuará sendo validada no servidor.
- Mudanças de banco serão registradas por migrações versionadas.
- O frontend começará com HTML e CSS acessíveis, adicionando JavaScript apenas quando
  uma interação realmente exigir.
- Uma API poderá ser adicionada futuramente sem ser necessária para o MVP inicial.
