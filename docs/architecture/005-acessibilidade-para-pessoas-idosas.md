# 005 — Acessibilidade e compreensão para pessoas idosas

## Situação

Aceita.

## Contexto

O público inicial do VivaBem inclui pessoas com mais de 60 anos que podem apresentar baixa visão,
menor precisão motora, dificuldade de concentração ou pouca familiaridade com interfaces digitais.
Também é necessário considerar pessoas com baixa alfabetização. Uma interface tecnicamente
acessível, mas organizada por termos internos do sistema, ainda pode ser difícil de compreender.

## Decisão

- Organizar o painel da pessoa idosa pelas tarefas “Pedir ajuda”, “Ver meus pedidos” e “Minha
  família”.
- Dividir o pedido de ajuda em cinco etapas, exibindo uma pergunta por vez quando JavaScript estiver
  disponível. Sem JavaScript, o formulário completo continua funcional.
- Salvar um rascunho somente no armazenamento da aba atual e removê-lo no envio.
- Exibir imagens simbólicas sempre acompanhadas por texto.
- Disponibilizar os tamanhos Pequena, Média, Grande e Super grande, usando o tamanho Grande como
  padrão inicial das contas de pessoa idosa.
- Oferecer leitura seletiva com a API de síntese de voz do navegador, sem enviar o conteúdo para um
  serviço externo. O primeiro clique seleciona e lê um item sem ativá-lo; em seguida, a navegação
  volta ao comportamento normal.
- Permitir ativar a leitura por `F2` no computador e manter um botão lateral centralizado em
  telas de celular.
- Usar botões grandes, foco visível, resumos de erro e confirmações antes de ações destrutivas.
- Explicar as permissões familiares no momento da escolha.
- Manter uma central de ajuda simples e um aviso de que a plataforma não atende emergências.

## Motivos

A solução mantém o monólito Django simples, não adiciona dependências externas e melhora a
compreensão sem alterar o modelo de dados. O comportamento progressivo preserva os fluxos quando
JavaScript, síntese de voz ou armazenamento do navegador não estiverem disponíveis.

## Limitações

- Símbolos podem ser interpretados de maneiras diferentes.
- A qualidade da voz depende do navegador e do dispositivo.
- A acessibilidade técnica não comprova usabilidade para o público real.
- A pesquisa de campo ainda deverá validar linguagem, imagens, tamanho dos controles e ordem das
  tarefas, sem inventar resultados antecipadamente.
