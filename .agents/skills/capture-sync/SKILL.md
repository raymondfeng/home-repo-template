---
name: capture-sync
description: 'Use when a meeting, a call or a chat must become a record in this repo — "fetch today''s meeting transcript", a pasted "<name>: …" message, comments on a shared document, or notes from a call with an advisor, a partner or a customer.'
---

# Capture a sync

A sync doc is the record of what was said. Chat is not canon until it is in the doc, word for word. A change is a
ruling only when a person with the authority asked for it in words. Anything the discussion only implies is a
proposal.

## The chain

1. **Read the source in full.** For a meeting tool: the meeting itself, then the transcript. A search snippet or a
   meeting list is never the source. For a pasted message: the paste is the source, and you keep it as written.
2. **Write the sync doc.** If a doc for the same day and thread exists (`ls docs/syncs/*<date>*`), add a section to
   it. Otherwise write `docs/syncs/<who>-sync-<topic>-<date>.md`. Lead with the decisions. Then the quotes, the open
   questions, and the todos with one owner each. Leave out any personal section the person asked to exclude, and say
   in the provenance line that you excluded it. Never invent a number: write `**[FILL]**`.
3. **Sweep the session** for every table, frame and one-line statement it produced, and check that each one is in the
   doc word for word.
4. **Todos into issues.** List each todo with the repo it belongs to (`AGENTS.md` → Other Repos), and offer to file
   them. File them when the owner says so.
5. **Rulings and proposals.** Record a change that was asked for in words as a ruling, with a number and the words.
   List a change that was only implied as a proposal, with the current text and the proposed text, and stop.
6. **Commit** the doc and any archive by explicit paths. Reply with the decisions, the todo list, and the doc's path.
