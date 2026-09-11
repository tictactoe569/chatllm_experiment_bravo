# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Implementar sessoes de chat e titulo automatico em uma barra lateral.

Requisitos minimos:
1. Usuario pode criar e alternar sessoes atraves de uma barra lateral (similar a ChatGPT e Gemini).
2. Cada sessao guarda seu historico.
3. Se a sessao ainda nao tiver titulo, o titulo deve ser definido automaticamente com base no contexto **possivel ja na primeira resposta do modelo**.

## Steps
- [ ] Identifique como o HTML divide cada pedaço da página
- [ ] Garanta que a implementação da barra lateral redimensione os outros componentes propriamente
- [ ] De alguma forma deve haver um histórico de sessões
- [ ] Título default deve ser um breve resumo de até 5 palavras do que a sessão se tratava

## Success Looks Like
- [ ] Barra lateral funcional, listando sessões anteriores e a atual do usuário
- [ ] Novas sessões assumem o título default assim que o primeiro prompt for respondido
- [ ] Cada usuário deve ter acesso somente às suas seções, nunca de outros usuários
- [ ] Deve ser possível para o usuário alternar entre sessões através do histórico disponibilizado na barra lateral

## Notes
- [ ] _Any specific edge cases, libraries to consider, or potential pitfalls._

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
