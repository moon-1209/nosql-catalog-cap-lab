# DECISION_LOG_CONVENTION.md — Decision Log Convention

- **Motivation/Background**: During AI-assisted coding, recording why the code is the way it is prevents silent architectural drift and provides an undeniable provenance record for future contributors and academic reviewers.
- **Purpose**: Define authoritative rules for capturing, attributing, formatting, and confirming architectural decisions during AI-assisted development.
- **Overview Pipeline**: Codified rules requiring human confirmation, strict attribution (`human`, `agent-proposed, human-approved`, `agent-default`), and standardized 12-line maximum entry blocks.
- **Detailed Plan**: §0 Purpose; §1 What to Log; §2 Workflow (Agent Drafts, Human Confirms); §3 Attribution; §4 Entry Template; §5 Field Rules; §6 Linking to Git; §7 Changing History; §8 Index; §9 Milestone Review; §10 Agent Self-Check.
- **References**: [agents/rules/MD_CONVENTION.md](MD_CONVENTION.md), [agents/rules/AGENT_AI.md](AGENT_AI.md), [docs/agent_logs/Vuong_DECISION_LOG.md](../../docs/agent_logs/Vuong_DECISION_LOG.md).
- **Created**: 2026-10-20T06:27:00+07:00
- **Last Updated**: 2026-10-20T06:27:00+07:00

[STATUS: ACTIVE]

---

# Decision Log Convention

Rules for recording **why the code is the way it is** during AI-assisted (vibe) coding.
Applies to every AI agent working in this repository. Log file: `docs/agent_logs/Vuong_DECISION_LOG.md`.

> If `MD_CONVENTION.md` requires a metadata header, put it above the title of the log
> file. This convention adds no header fields of its own.

## 0. Purpose

The log has two readers:

- **(a) Future me**, who finds odd code a month later and asks *"why is it like this, and what else was considered?"*
- **(b) A reviewer** (supervisor, lecturer) who asks *"whose decision was this: yours or the AI's?"*

Log **decisions, not activity**. Git already records what changed; chat history is
not a log. A log entry exists only to answer **why this, not the alternative, and who chose it**.

**Delete test:** if removing an entry would not stop someone from explaining why the
code looks the way it does, the entry should not exist.

## 1. What to log

Write an entry when at least one is true:

1. A real choice was made between two or more viable options (library, model, schema, API shape, architecture, algorithm, parameter that affects behavior).
2. The human redirected, overrode, or narrowed what the agent proposed.
3. The agent deviated from an approved plan, or filled a gap the plan left open.
4. Something was tried for real and abandoned (a **dead end**), so nobody repeats it.
5. An earlier decision was reversed.
6. A verification result changed the course of work.

**Never log:**

- Lists of tool calls, commands run, or files opened.
- Slash-command text, settings changes, or tool boilerplate.
- Restated plans or summaries of what was done (the diff and commit message cover that).
- Routine edits with no alternative (renames, formatting, obvious fixes).
- Step-by-step debugging. Log the *outcome* of a dead end, not the journey.

## 2. Workflow: agent drafts, human confirms

1. **During work:** the agent notes candidate decisions silently. It does not interrupt for logging.
2. **End of each task, before the final summary:** the agent drafts entries with `Status: proposed`.
3. **Confirmation step (mandatory):** the agent shows the drafts in chat in compact form and asks the human, per entry, to **confirm / edit / drop**. Entries marked `agent-default` are listed **first** and called out explicitly.
4. **Only after explicit confirmation** does the agent set `Status: accepted` and write the final text to `docs/agent_logs/Vuong_DECISION_LOG.md`.
5. If the human does not answer, entries stay `proposed`. The agent never promotes them on its own. Silence is not approval.
6. Code work and commits are not blocked by an unconfirmed log. Unconfirmed entries are simply visible as `proposed`.

## 3. Attribution: `Decided by`

This field is what makes the log usable as evidence. Be strict.

| Value | Use only when |
|---|---|
| `human` | The human stated the choice in their own words. A verbatim **Trigger** quote is required. |
| `agent-proposed, human-approved` | The agent presented the option and the human explicitly approved it. Approving a plan covers **only decisions written in that plan's text**, not choices made later during execution. |
| `agent-default` | The agent chose without presenting it, or filled in a detail the plan or request did not specify (thresholds, weights, defaults, naming, library versions). |

Rules:

- If unsure, use `agent-default`. Never upgrade attribution to look better.
- Never write `human` without a quote. Never invent or paraphrase a quote.
- A human choice can contain agent-defaults. Example: the human says "run on GPU" (`human`); the agent picks the layer count (separate `agent-default` entry or a note inside the entry).

## 4. Entry template

Copy this block. One decision per entry. **Maximum 12 lines.**

```md
### D-NNN — <imperative title, ≤ 80 chars>
- **Status:** proposed | accepted | superseded by D-MMM | abandoned
- **When:** <ISO 8601 with offset, e.g. 2026-10-14T16:09:41+07:00>
- **Decided by:** human | agent-proposed, human-approved | agent-default
- **Trigger:** "<verbatim human words, ≤ 40 words>" (turn or file ref) — or `none (agent initiative)`
- **Decision:** <1–2 sentences: what is now true of the codebase>
- **Why:** <the reason that tipped it; for a dead end: why it failed>
- **Rejected:** <option> — <why not>; ... — or `not considered` / `not recorded`
- **Touches:** <paths, or `git branches`, `config`, ...>
- **Evidence:** <exact command + observed result> — or `not verified`
- **Revisit if:** <optional: condition that should reopen this>
```

## 5. Field rules

- **Rejected** lists only alternatives that were actually on the table (in the plan, the chat, or genuinely considered). Never invent options to fill the field. `not considered` is valid and informative.
- **Why** states the real reason. If none was given or known, write `not recorded`. Do not reverse-engineer a rationale.
- **Evidence** records only what was **actually run** in this session, with the observed result (command, pass/fail, counts, timings). Never write "tests pass" without command and count. If the figure comes from an earlier report and was not re-run, say so. Otherwise write `not verified`.
- **Touches** lists paths, not commit hashes (see section 6).
- **Dead ends** use the same template with `Status: abandoned`; `Rejected` may be omitted.
- No chat transcripts, no code blocks beyond a one-line command or parameter, no emojis.

## 6. Linking to git

- Every commit that implements or is shaped by a decision carries a trailer, same style as `Companion-Doc:`:

  ```
  Decision: D-003
  ```

  Repeat the trailer for multiple decisions. In multi-repo setups (FE, BE, root), put it in each repo's commit.
- To find the commits for a decision: `git log --all --grep="Decision: D-003"`.
- Do **not** write commit hashes into the log. This avoids a second "fix the hash" commit.

## 7. Changing history

- `accepted` entries are append-only. Only the **Status** line may be edited afterwards (and typos).
- To reverse a decision, add a **new** entry, then set the old one to `superseded by D-MMM`.
- IDs are never reused or renumbered.

## 8. Index

The top of `docs/agent_logs/Vuong_DECISION_LOG.md` has a table: `ID | Title | Decided by | Status`.
Update it in the same edit as the entry.

## 9. Milestone review (for the human)

Before a demo, submission, or supervisor meeting, the agent lists every entry that is
still `agent-default`. The human marks each one **keep** (becomes
`agent-proposed, human-approved`) or **change** (new decision entry). This is how
unreviewed AI choices get surfaced instead of buried.

## 10. Agent self-check before presenting drafts

- [ ] Each entry passes the delete test (section 0).
- [ ] No entry lists activity (tool calls, files read).
- [ ] Every `human` entry has a real verbatim quote.
- [ ] `Rejected` contains only real alternatives, or `not considered` / `not recorded`.
- [ ] `Evidence` contains only commands actually run, or `not verified`.
- [ ] Each entry is ≤ 12 lines, one decision.
- [ ] `agent-default` entries are listed first in the confirmation message.
