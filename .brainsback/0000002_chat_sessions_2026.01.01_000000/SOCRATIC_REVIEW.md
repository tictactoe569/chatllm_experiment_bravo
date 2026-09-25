# Socratic Review Record

> This file is AI-generated as part of the Mastery-Aware Pipeline.

## Task
0000002 — Sessões de Chat com Título Automático

## Questions & Answers

### Pergunta 1 — Segurança: Filtro de user_id no auto-título

**Reviewer:** Reparei que no endpoint `/api/chat` (síncrono), o auto-título busca a sessão sem filtrar pelo `user_id`:
```python
session = db.query(Session).filter(Session.session_key == session_key).first()
```
Isso significa que se um usuário mal-intencionado conhecer a `session_key` de outro usuário, essa query — embora não exponha dados — ainda poderia atualizar o título de uma sessão alheia, mesmo que a session_key tenha sido validada anteriormente pelo `_resolve_session_key`.

**Developer:** Isso de fato é um problema de UX (e não de segurança) que não pensei quando estava levantando os requisitos para o agente. Porém, para isso o usuário mal intencionado precisaria ter acesso a minha API pra início de conversa, coisa que é possível mitigar sem necessariamente corrigir o código.

### Pergunta 2 — Performance: Duas queries de sessão no chat stream

**Reviewer:** No endpoint `/api/chat/stream`, a sessão é resolvida antes do generator (`session_key = _resolve_session_key(...)` — que faz uma query) e depois, dentro do `event_generator()`, uma segunda query busca a `Session` para o auto-título:
```python
session = db.query(Session).filter(Session.session_key == session_key).first()
```
Isso são duas queries no banco para a mesma sessão em cada requisição. Que abordagens poderiam reduzir para uma única query?

**Developer:** Sim. Poderia ser salvo em um buffer o resultado da query e reutilizado nos dois casos.

### Pergunta 3 — Tratamento de erros: sessão removida durante uso

**Reviewer:** No frontend, quando o usuário alterna entre sessões (`handleSelectSession`) ou envia mensagem (`onSubmit`), não há nenhum mecanismo para "refresh" automático das sessões caso uma se torne inválida — por exemplo, se a sessão foi deletada por outro dispositivo ou em outra aba. O usuário pode tentar enviar uma mensagem para uma sessão que não existe mais e só descobrir o erro quando a requisição falhar. Como você lidaria com esse cenário de race condition? Considerou alguma estratégia como revalidar a lista de sessões após erros 404?

**Developer:** Não considerei nenhuma estratégia, mas isso poderia ser corrigido através de um observer que poderia receber um aviso de que o chat não existe mais, além de uma verificação antes do envio da mensagem/alternancia entre sessoes se ela ainda consta no BD.

### Pergunta 4 — Arquitetura: Tabela Session separada vs abordagem alternativa

**Reviewer:** Você optou por criar uma tabela `sessions` separada com metadados (`title`, `created_at`, `updated_at`) em vez de usar apenas a coluna `session_key` já existente em `ChatMessage` com algum mecanismo como uma flag `is_first_message` para extrair o título da primeira mensagem. Quais foram os motivos principais para essa escolha? E em que cenários essa abordagem poderia se tornar um problema?

**Developer:** Isso foi escolhido pois com ela posso mapear facilmente com um usuário já existente no banco de dados. De fato essa abordagem pode gerar problemas quando escalada ao infinito, mas não vejo maiores problemas desse jeito não.

### Pergunta 5 — Auto-título: timing e conteúdo significativo

**Reviewer:** O título é gerado a partir das primeiras 5 palavras da resposta do modelo — `" ".join(words[:5])` — truncado em 100 caracteres. Se a resposta começar com uma saudação comum como *"Olá! Como posso ajudar você hoje?"*, o título seria *"Olá! Como posso ajudar você"* — o que não é muito descritivo. Você considerou alternativas como usar a pergunta do usuário como título, ou concatenar ambas? Que trade-offs você vê em cada abordagem?

**Developer:** Poderia ter escolhido também a pergunta do usuário, mas achei que o usuário gostaria de se orientar mais pela resposta do modelo (como uma mensagem de whatsapp não lida) do que pela pergunta dele. A razão das 5 primeiras é a redução na complexidade no momento que você vai escrever o título. Mais uma chamada pra algum modelo para resumir em uma frase curta a conversa não faz sentido.

### Pergunta 6 — Segurança e informação: dados nas URLs

**Reviewer:** As operações de deletar e listar mensagens colocam a `session_key` diretamente na URL (`/api/sessions/{session_key}`, `/api/sessions/{session_key}/messages`). Embora a session_key seja um UUID aleatório, esses dados ficam visíveis em logs de servidor, histórico do navegador e referer headers. Você considera que expor UUIDs nas URLs representa algum risco? Se sim, como poderia mitigar?

**Developer:** Sim. Poderia passar por algum tipo de criptografia, assim mesmo que tenha a informação esteja disposta na URL, se torna inútil.

---

## Veredito de Maestria

**Status: ✅ APROVADO**

O desenvolvedor demonstrou compreensão sólida da implementação e dos trade-offs arquiteturais envolvidos. Destacam-se:

- **Segurança**: Reconheceu a limitação no filtro de `user_id` no auto-título e contextualizou corretamente o risco.
- **Performance**: Identificou a oportunidade de redução de queries (cache do objeto Session).
- **Tratamento de erros**: Sugeriu observer + pré-validação para race conditions — reconhecendo a lacuna com honestidade.
- **Arquitetura**: Escolha fundamentada da tabela `sessions` separada, com consciência dos trade-offs de escalabilidade.
- **Auto-título**: Decisão deliberada de usar a resposta do modelo, com justificativa clara (preview estilo WhatsApp) e rejeição fundamentada de chamada extra ao LLM.
- **Exposição de dados**: Consciência de segurança ao sugerir criptografia para UUIDs em URLs.

Todas as respostas foram coerentes com o código implementado e mostraram reflexão crítica. Nenhuma lacuna grave de entendimento foi identificada.