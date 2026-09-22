# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
O ChatLLM atual tem apenas uma única sessão de chat fixa (chamada "default"). Todas as mensagens de todos os usuários são misturadas nessa mesma sessão. Não há como um usuário organizar conversas diferentes, alternar entre elas ou identificar cada conversa por um título.

## Steps
Backend

- [ ] Modelo ChatSession + FK em ChatMessage
- [ ] Schemas de sessão
- [ ] Router sessions.py (CRUD)
- [ ] Título automático na primeira resposta
- [ ] Chat router aceitar session_id

Frontend

- [ ] Sidebar.jsx (lista, criar, alternar, deletar)
- [ ] App.jsx integrar sidebar + estado de sessão
- [ ] api.js funções de sessão
- [ ] Estilos CSS da sidebar

Testes

- [ ] CRUD de sessões
- [ ] Mensagens por sessão
- [ ] Título automático

## Success Looks Like
- [ ] Usuário autenticado pode criar múltiplas sessões de chat
- [ ] Barra lateral lista todas as sessões do usuário
- [ ] Usuário pode alternar entre sessões clicando na barra lateral
- [ ] Ao alternar, o histórico da sessão selecionada é carregado
- [ ] Usuário pode deletar uma sessão
- [ ] Sessão nova sem título ganha título automático na primeira resposta do modelo
- [ ] Mensagens são persistidas na sessão correta
- [ ] Sessão ativa fica destacada na barra lateral
- [ ] Botão "Nova conversa" limpa o chat e cria uma sessão vazia
- [ ] Testes automatizados passam (CRUD de sessões + título automático)
- [ ] Toda string visível ao usuário está em português

## Notes
- [ ] Banco SQLite será resetado (mudança estrutural no ChatMessage)
- [ ] Título automático: primeiros ~60 caracteres da 1ª mensagem do usuário
- [ ] Toda operação de sessão verifica ownership do usuário autenticado
- [ ] Ao alternar sessão no frontend, chat limpa e carrega histórico correto
- [ ] session_id é obrigatório no payload do chat

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
