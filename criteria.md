# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** `search_listings` scores on plain keyword overlap between
the description and each listing's title/description/category/style_tags —
there's no synonym handling or fuzzy matching, so a phrasing that doesn't
share a literal word with anything in the data (e.g. "sweater" when the
listing only says "crewneck") can come back empty even though a human would
call it a match. That's a property of a simple keyword search, not a bug in
the loop, so I'm leaving room for one miss out of five rather than claiming
5 of 5.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** This path doesn't depend on keyword luck the way
criterion 1 does — it only depends on the branch rule in `run_agent` checking
whether `search_listings` returned an empty list, which is a plain `if` over
code I control completely. There's no model call and no ambiguous matching
involved in deciding to stop, so there's no realistic reason for this to work
4 times and fail the 5th — a miss here would mean the branch itself is broken,
not that the input was unlucky.

---

## 3. Something about state

Given a matching query, `session["selected_item"]["id"]` is the same `id` as
the item dict passed into `suggest_outfit` — checked across 5 of 5 tries.

**Why this target:** `search_listings` and `suggest_outfit` are separate
functions joined only by the session dict — nothing stops a bug from putting
one item in `selected_item` and a different one into the call. Since
`run_agent` always picks `search_results[0]`, the id should match every single
time; any mismatch is a wiring bug, not a flaky search, so 5 of 5 is the right
bar.

---

## 4. Something about the fit card

For 5 different items run through `create_fit_card`, each resulting caption
mentions that item's price and platform — checked across all 5, not just
most.

**Why this target:** The wording will vary every time (`TEMPERATURE` is 0.9 on
purpose), so I can't check for exact text. But the prompt explicitly asks the
model to mention price and platform once each — if either is missing, that's
the prompt or the tool failing, not normal model variation. 5 of 5 because
this is a structural requirement I control via the prompt, not a wording
quality I'm leaving to the model's judgment.



---

## 5. Your choice

Given a query with a `max_price`, every listing in `search_results` has
`price <= max_price` — checked across 5 queries with different price
ceilings, 0 violations allowed in any of them.

**Why this target:** The price filter in `search_listings` is a plain
comparison, not something that depends on the model or on ambiguous keyword
matching — there's no reasonable case where it should ever let a listing
through over the ceiling. A single violation means the filter itself is
broken, so the bar is 0 of however many results come back, every time.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
