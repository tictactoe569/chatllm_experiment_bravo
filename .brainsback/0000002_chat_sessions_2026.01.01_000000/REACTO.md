# Proof of Mastery (REACTO)

> Explain it to prove you own it.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## R — Repeat (The Problem)
Adicionar uma barra lateral contendo o histórico de sessões de um usuário. Cada usuário deve ter acesso somente às suas sessões. O título de cada uma delas precisa ser preenchido por default.

## E — Examples

- **Happy Path Input**: Usuário faz login 
  **Output**: Ao lado esquerdo aparece a barra com o histórico de sessões anteriores

- **Edge Case Input**: Usuário faz login pela primeira vez
  **Output**: Histórico de sessões vazio

## A — Approach
Salvar as conversas no banco de dados e recuperá-las no login

## C — Code
O salvamento das sessões é a parte mais crítica. Altas chances de quebrar (como aconteceu e não tive tempo de tentar arrumar)

## T — Tests
Criar novos chats e ver se os títulos são preenchidos a cada resposta

## O — Optimize
Fazer com que os chats fossem de fato salvos no banco de dados.
