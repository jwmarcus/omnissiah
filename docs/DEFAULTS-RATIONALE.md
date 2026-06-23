# Defaults rationale

Omnissiah ships a set of safe-but-permissive defaults turned on in every generated repo. This is the explainer for each one: the default, why it is the middle ground (with the too-restrictive and too-permissive failure modes), and how to tune it.

The whole point is that you tune knowingly. Each default also appears inline in the generated `OPERATING-CONTRACT.md` with a one-line rationale, so you meet it in context. None of these has a config flag that silently disables it. If you want different behavior, you edit the contract by hand, and that edit shows up in your git history.

A note on "permissive": these defaults are permissive relative to a locked-down assistant. The assistant is allowed to act, write, and touch external systems. They are conservative relative to an unbounded agent. The balance is action with tracks.

## Drafts over sends

The default: outbound email and messages are created as reviewable drafts. The human sends.

Why it is the middle ground: too restrictive is an assistant that can only read your inbox and tells you what to type, which is barely better than no assistant. Too permissive is an assistant that sends mail on its own; the first wrong recipient, wrong tone, or hallucinated commitment goes out under your name and cannot be recalled. A draft captures all the value (the assistant composes, threads, and formats) while keeping the irreversible step with you. Reviewing a draft is seconds; unsending an email is impossible.

How to tune: for low-stakes internal channels you may decide a specific tool can send directly. Make that a per-tool decision in the contract, name the tool, and keep everything else draft-only. Do not flip a global "can send" switch.

## List, then read, then act

The default: never act on a record (archive, label, reply, delete) without reading it first.

Why it is the middle ground: too restrictive is forcing a human read of every item before any bulk operation, which kills the point of automation on a hundred-message inbox. Too permissive is acting on search results or list metadata alone; subject lines and labels lie, threads get misclassified, and you archive the one message that mattered. Read-before-act means the assistant pulls the actual content into context before the irreversible step, so its decision is grounded in the record and not a guess from a list row.

How to tune: for genuinely safe bulk operations (for example labeling everything from a known newsletter sender) you can define a narrow, explicit exception in the contract. Keep it scoped to operations that are reversible and to selectors that cannot misfire.

## Single events over fragile recurrence

The default: for short protocols (medication courses, travel, sprints) prefer a batch of single calendar events over a recurrence rule.

Why it is the middle ground: too restrictive is refusing to put anything on the calendar without manual entry. Too permissive is leaning on recurrence rules for everything; recurrence drifts, syncs unpredictably across clients, and is hard to edit or cancel cleanly for a five-day course. A batch of explicit single events is deterministic: each one is visible, individually editable, and disappears when the protocol ends. For long stable schedules recurrence is fine, but it gets called out.

How to tune: keep recurrence for genuinely long-running standing commitments. When you do use it, have the assistant flag the recurrence and the sync risk so you are not surprised later.

## Verify on high-stakes input

The default: verify before acting when the input involves dates, money, health, legal matters, external-system state, or current facts.

Why it is the middle ground: too restrictive is verifying everything, which makes the assistant slow and annoying on trivia. Too permissive is acting on confident-sounding output for exactly the inputs where being wrong is expensive; a misremembered dose, a wrong wire amount, or a stale system status is a real-world cost, not a typo. Scoping verification to high-stakes categories keeps the assistant fast on the cheap stuff and careful where it counts.

How to tune: adjust the list of high-stakes categories to your life. If you never touch legal matters but do a lot of inventory work, swap it in. Widen the list when you are in a domain where errors compound.

## Capture is allowed to be messy, but it drains

The default: one capture surface, drained on a cadence. Capture stays in your task system, not a new app.

Why it is the middle ground: too restrictive is demanding you file every thought into the right project with a due date at capture time, which means you stop capturing because it is too much friction. Too permissive is letting capture pile up forever, or worse, standing up a second and third inbox; every extra surface is another place that never gets drained. The balance is one messy inbox that you trust because it has a scheduled drain. Untriaged items are a visible backlog, not a hidden swamp. (Wintermute learned this the hard way: its predecessor notes vault failed because capture and storage were the same place with no drain.)

How to tune: set the drain cadence to match your volume (weekly is a reasonable start). You can change which surface is the one capture inbox. The rule you do not break is the count: one inbox, and it drains.

## No destructive filesystem or git operations unless asked

The default: the assistant does not run destructive filesystem or git commands, and does not revert your work, unless you explicitly ask for that specific operation.

Why it is the middle ground: too restrictive is a read-only assistant that cannot help with real code or file work. Too permissive is an assistant that decides on its own to `git reset --hard`, force-push, or delete files to "clean up"; that is how unrecoverable work loss happens. The middle ground lets the assistant make scoped, additive changes (write files, make commits you can review) while treating destructive and history-rewriting operations as something only you initiate, by name.

How to tune: this one is meant to stay strict. If a specific destructive operation is routine for you, ask for it explicitly each time rather than granting blanket permission. Backups do not make blanket destructive authority safe; they make it recoverable, which is not the same thing.

## Secrets stay local

The default: secrets (tokens, keys, credentials) never go into commits, notes, chat summaries, or docs.

Why it is the middle ground: there is no benign too-restrictive failure here, so this is the one default with essentially no permissive side. The permissive failure is a leaked credential in git history or a pasted token in a chat log, which is a real breach that outlives the session. Secrets live in `.env` (gitignored) and in your host config, and nowhere the assistant writes durable text.

How to tune: do not loosen this. If you need the assistant to use a credential, put it in `.env` and reference it by variable name. The generated `.gitignore` already excludes `.env` and the `var/` working directory.

## Scoped MCP tools over broad ambient authority

The default: external-system access goes through named, scoped MCP tools, not a general shell or a broad API key with everything enabled.

Why it is the middle ground: too restrictive is no external access at all, which defeats the purpose of a connected assistant. Too permissive is handing the assistant ambient authority (a root shell, a full-scope token) and hoping it only does what you meant; the blast radius of a mistake is then your entire account. Scoped tools make the boundary the thing you can see and audit: each tool is a specific operation with specific arguments, and the set of tools is the exact surface the assistant can touch.

How to tune: add tools deliberately, one capability at a time, and scope each to the narrowest operation that does the job. Adding a tool is a real decision; it widens the boundary. The generated server shows the pattern with a single local provider so you extend by copying a known-good shape.

## Move when the next action is clear; ask the smallest necessary question otherwise

The default: when the next action is unambiguous, take it. When it is not, ask one targeted question rather than stalling or guessing.

Why it is the middle ground: too restrictive is an assistant that asks permission for every step, which turns a quick task into an interrogation. Too permissive is an assistant that guesses through ambiguity and produces confident wrong work you then have to find and undo. The balance is bias toward action on clear targets and a single sharp question on genuine ambiguity, not a wall of clarifying questions and not a silent guess.

How to tune: calibrate to your own risk tolerance and the stakes of the work. Raise the bar for action (ask more) on irreversible or high-stakes tasks; lower it on cheap, reversible ones.

## Concrete communication

The default: report actions, evidence, and results. No flattery, and no approval language standing in for an actual report.

Why it is the middle ground: too restrictive is terse output that omits what changed and what was verified. Too permissive (the common failure) is warm, agreeable filler ("Great question, this is a fantastic approach") that reads as progress but reports nothing; it hides what the assistant actually did and erodes your ability to catch mistakes. The balance is short, direct status: what changed, what was checked, what remains open.

How to tune: set the verbosity you want, but keep the substance. Shorter is fine. Replacing reporting with reassurance is not.

## Durable context survives the chat

The default: commitments go to your task system; durable technical and system decisions go to repo docs. The chat is not the system of record.

Why it is the middle ground: too restrictive is writing everything down formally, which is overhead that does not survive contact with a fast working session. Too permissive is leaving decisions and commitments in the chat transcript, where they vanish at the next fresh session and you rediscover the same problem next week. The balance is routing the two things that must outlive the chat (commitments and durable decisions) to durable homes, and letting everything else stay ephemeral.

How to tune: pick your task system and your docs layout. The rule that does not change is the routing: real commitments go to the task system, durable decisions go to repo docs, and you do not rely on chat memory for either.
