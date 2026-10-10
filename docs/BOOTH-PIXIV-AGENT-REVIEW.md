# BOOTH + Pixiv agent review — 2026-09-22

Two agents, reviewed against their actual toolchains. Every finding below is
reproduced from the code or the files, not inferred. Where a claim could be
tested, it was tested, and one plausible-sounding finding was **refuted** by
testing.

Read this as: what the agent is told, what the tools actually do, and where the
two disagree. The last section is the part that matters in a live run.

---

## Part 1 — BOOTH (agent-20)

### 1.1 The tag target is three different numbers

The single most consequential defect. The agent is told to hit a number, and
that number differs depending on which file it read last.

| Source | Says | Line |
|---|---|---|
| Validator constant | `TARGET_BOOTH_TAGS = 25` | `bin/validate_booth_listing.py:37` |
| Spec, §7 | "Selected tags must number 18-25, **targeting 25**" | `agents/agent-20-...md:520` |
| Spec, output template | "Use tier-below tags to reach 25 … 25 is the ceiling" | `:912` |
| **Spec, §7 step 4** | "**Reach 20** when the tier-below candidates are defensible" | `:562` |
| **Spec, §7A** | "Expansion block (any remainder **up to the 20 cap**)" | `:723` |
| **Bank rule 4** | "Preserve the existing **48-candidate bound, 40 strongest-candidate target**" | `booth-font-tag-bank.md:31` |
| Bank, description pass | "never count it toward **40**" | `:59` |

So: **20, 25, and 40** are all live instructions. The validator rejects anything
above 25 outright.

An agent reading top-down gets "target 25" from §7, then "Reach 20" from step 4,
then "up to the 20 cap" from §7A, then opens the bank it is required to start
from and reads "40 strongest-candidate target". It has no way to know which
wins. The likely outcome is that it aims at 20 in practice — the lowest number
it can satisfy that also passes — and quietly ignores the 25 target, which is
exactly what the warning-only implementation permits.

**The bank's candidate bound is stale on both counts.** It says "48-candidate
bound"; the bank file now holds **67 numbered rows**. It says target 40; the
validator caps at 25.

### 1.2 The spec misdescribes the validator as failing closed on the target

Spec `:978`:

> The validator fails closed on: the 18-25 tag contract (target 25;
> `MIN_BOOTH_TAGS` / `MAX_BOOTH_TAGS` / `TARGET_BOOTH_TAGS`) …

Spec `:520` repeats it: "enforces that range … **and fails closed outside it**".

The code disagrees. `TARGET_BOOTH_TAGS` produces a **warning**, never a failure
(`bin/validate_booth_listing.py:562-567`). Only `MIN`/`MAX` fail closed.

This matters because the agent is told the target is enforced. It will believe a
20-tag listing would be rejected, find that it is not, and lose trust in the
gate's descriptions — or, worse, pad to 25 to satisfy a "hard" rule that was
deliberately made soft precisely to avoid padding. The comment in the code says
so: *"padding to reach it is what the spec bans."*

### 1.3 A "dead warning" that is not dead — tested and refuted

A survey pass reported the below-floor exemption warning
(`bin/validate_booth_listing.py:557-561`) as unreachable, reasoning that gate
failures are "typically present" at low counts.

**That is wrong, and it was worth testing.** Truncating a passing listing to 14
tags with 14 matching evidence rows fires it cleanly:

```
[WARN] tag count 14 is below the 18 floor but every selected tag proves a
       young-cohort win-rate >= 5.0%; below-floor exemption applied
[PASS] ... BOOTH listing-copy, one-per-line tags, evidence, and scope checks passed
```

Both branches are reachable and behave as documented. Recorded here because a
plausible-sounding claim that survives review is how a real check gets deleted.

### 1.4 Bank/gate tension the agent has to resolve alone

The bank is **frozen** and forbids refreshing during a run
(`booth-font-tag-bank.md:28-31`), including when its evidence is "older than 45
days". The validator warns on evidence older than 45 days.

So the agent is instructed to use stale evidence and simultaneously warned about
it. Neither instruction is wrong — harvesting per run was explicitly rejected as
too expensive — but the agent is given no rule for what to do when the warning
fires. It should be told the 45-day warning is expected on a frozen bank and is
recorded, not resolved.

### 1.5 BOOTH coverage is sound

Checked directly: **48 listing files on disk, 48 with a `## BOOTH TAGS` header.**
No silent skipping. Whatever else is wrong, the BOOTH toolchain sees its whole
catalogue, and the sibling advisory counts against all 48.

---

## Part 2 — Pixiv (agent-22)

### 2.1 The rotation tool is blind to 11 of 13 packages — and does not say so

`validate_pixiv_tag_circulation.py` prints:

```
Packages scanned: 2; post angles scanned: 6
```

There are **13** packages. It silently omits 11.

Cause: `POST_HEADING = r"^##\s+POST\s+\d+\s*[-—]"` requires a `## POST 1 —`
heading before it will record any tag block. Eleven packages use the older
`## PIXIV POST` heading, so their tags are never collected. The "no packages
found" branch does not fire, because two *did* parse — so the report looks
healthy and is computed on 2 of 13 packages.

This is the worst failure mode in either agent. It does not crash, does not warn,
and returns a confident percentage over a sixth of the data. The user asked for
Pixiv rotation; **this tool is the rotation instrument, and it is currently
measuring almost nothing.**

### 2.2 The tag format contract is split three ways

| Source | Requires |
|---|---|
| Spec `:315` | "**exactly 10** Pixiv tags, **ONE PER LINE** … never comma-separated" |
| `validate_pixiv_listing.py:98-101` | Accepts **both** — "the active one-tag-per-line contract and the legacy comma-separated form" |
| `validate_pixiv_tag_circulation.py:91` | Parses **comma-separated only** (`stripped.split(",")` on a single line) |
| Real packages 85, 86 | **comma-separated** — `フォント, typography, font, ...` |

So the form the spec calls a defect is the form both newest packages use **and**
the only form the circulation validator can read. And because
`validate_pixiv_listing.py` deliberately tolerates both, nothing catches the
drift. The comment at `:55` is candid about why: *"rejecting the listing over it
made the validator disagree with the listings it exists to check."* The validator
was bent to match reality instead of reality being corrected to the contract.

Consequence for rotation: an agent that obeys the spec exactly (one per line)
produces a file **the rotation tool cannot read at all**.

### 2.3 One of the only two visible packages fails the other validator

`85-quill-crest-pixiv.md` is one of the two the circulation tool can see, and it
fails `validate_pixiv_listing.py`:

```
[FAIL] frontmatter platform must be Pixiv
[FAIL] BOOTH DESTINATION must contain a public booth.pm/items/<id> URL or LINK REQUIRED
[FAIL] POST 1 - STYLE SHOWCASE is missing a Title field
[FAIL] POST 1 - STYLE SHOWCASE is missing a Tags field
```

So the rotation signal is drawn from two packages: one non-conformant, and one
(86) that conforms only because the validator tolerates the comma form.

### 2.4 The spec credits the tool with a check it does not have

Spec `:130`:

> … and when a relevant **banked or platform-supplied candidate has not been used
> recently**.

`validate_pixiv_tag_circulation.py` implements three warnings and none of them is
this one: duplicate-within-a-post, repeated-across-every-package, used-in-all-
three-angles-of-one-package. There is no check for an *unused* banked candidate.
Since the bank is the rotation source, the missing check is the one that would
drive rotation.

### 2.5 The entry point asks for the opposite of the spec

`.omp/commands/pixiv-font.md` requests:

> "**one** paste-ready … package with exactly 10 consolidated tags and **one**
> declarative description"

The spec requires **three** posts — `POST 1 - STYLE SHOWCASE`,
`POST 2 - LETTERING SHOWCASE`, `POST 3 - USE-CASE SHOWCASE` — and the output is
"incomplete if … a post has no tags". An agent dispatched through the command is
told to produce one post; the spec it then reads demands three.

### 2.7 The listing validator read only the first tag of every post

Found while fixing §2.2. `post_tags` used `^###\s+Tags\s*(?:\([^)]*\))?\s*:?\s*(.*)$`,
where `\s*` matches the newline — so the trailing `(.*)` reached past the heading
and captured the first tag line. Verified against the pre-change code:

```
POST 1 - STYLE SHOWCASE: 1 tag(s) seen -> ['フォント']
POST 2 - LETTERING SHOWCASE: 1 tag(s) seen -> ['フォント']
POST 3 - USE-CASE SHOWCASE: 1 tag(s) seen -> ['フォント']
```

Every post looked like it had exactly one tag. Consequences: the 10-tag ceiling
could never fire, the duplicate-tag check could never fire, and the
"evidence rows fewer than distinct selected tags" check compared against 1. A
post with 30 tags would have passed. This is why §2.2's drift went unnoticed —
the gate was not measuring the tag block at all.

### 2.6 Rotation is advisory and unwired

Spec `:385`: "`validate_pixiv_tag_circulation.py` is advisory … Report its
warnings; **they do not block**."

So the Pixiv rotation instrument is, by design, a report the agent may note and
ignore. Given §2.1 (it sees 2 of 13 packages) and §2.2 (it cannot read the
spec-mandated format), the practical result is that nothing enforces or even
reliably observes Pixiv tag rotation.

---

## Part 3 — What the agent should assume, and what to do when tools fight

This is the part the agent is missing, and the reason the contradictions above
cause damage rather than mere confusion. Today the spec assumes all its tools
agree. They do not, and an agent in a live run hits these without warning.

**Precedence, when two sources disagree:**

1. **The validator's exit code beats the spec's prose.** If the spec says
   "fails closed" and the validator passes, the listing is complete — do not
   invent a fix for a failure that did not occur. Report the discrepancy in
   `RESEARCH NOTES` and continue.
2. **A machine-readable contract beats a descriptive sentence.** The validator's
   constants are the contract; the number in a prose paragraph is a description
   of it and may be stale. Where the bank and the validator disagree on a count,
   **the validator wins** and the bank is read for candidates, not for limits.
3. **Never pad to satisfy a number.** If two sources give different targets,
   take the lower defensible count and say which sources conflicted. Padding to
   resolve an ambiguity is the one outcome the spec explicitly bans.
4. **A tool reporting a fraction of its input is a blocker, not a result.**
   `Packages scanned: 2` against 13 files is not a low-reuse finding. An agent
   that sees a scan count smaller than the file count it can enumerate must stop
   and report the gap rather than reasoning from the partial result.
5. **Report the conflict; do not silently pick.** The failure above is not that
   the numbers differ — it is that the agent resolves them invisibly, and the
   run looks clean.

**Concretely, for the two agents as they stand:**

- BOOTH: target **25**, floor **18**, hard ceiling **25**. Treat `TARGET` as a
  goal that warns. Ignore the bank's 40 and §7A's 20 — they are stale, and this
  document is the record of that.
- Pixiv: obey the spec's one-per-line contract **but know the circulation tool
  cannot read it**. Until that is fixed, rotation cannot be measured from the
  output, and a clean circulation report means nothing.

---

## Part 4 — What to fix, in order of consequence

> **Status: 1-6 applied (2026-09-22).** See the commit that follows this file.
> One further defect was found *while* fixing: the listing validator was reading
> only the first tag of every post (§2.7 below), so the 10-tag ceiling, the
> duplicate check, and the evidence-row count had never been evaluated against
> real tags.


1. **Pixiv circulation parser blindness** (§2.1). Highest impact: the rotation
   instrument the user asked for measures 2 of 13 packages and reports success.
   Fix the heading match, and make a skip count visible.
2. **Pixiv format contract** (§2.2). Pick one form, make the spec, both parsers,
   and the packages agree. Presently the spec is the only holdout and the tools
   accommodate the drift instead of surfacing it.
3. **BOOTH target reconciliation** (§1.1, §1.2). One number in the spec, the
   validator, and the bank; and stop describing the warning as a hard fail.
4. **Pixiv missing rotation check** (§2.4) — either implement the unused-banked-
   candidate warning or remove the claim.
5. **Pixiv entry point** (§2.5) — one post or three, decided.
6. **Add the precedence rule** (Part 3) to both specs, so a live run has a
   defined behaviour when sources conflict.

---

## Method

Facts gathered by reading the specs, tools, bank, and real packages, and by
running the tools against real inputs. Two parallel survey passes were used for
breadth; **both were independently verified here**, and one of their findings
(§1.3) was tested and refuted. Claims in this document are reproducible from the
cited lines; nothing is inferred from documentation alone.
