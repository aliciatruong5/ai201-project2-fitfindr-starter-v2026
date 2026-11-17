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

## Criteria for the fourth tool, `price_check`

*Criteria 6 to 10 are for `price_check`, which I added after the first five were written and after unit 4. Nothing above this line was changed. These were written after the tool existed, so I ran each check once to make sure it could be measured; the targets below are not loosened to fit what came back.*

---

## 6. Averages and verdicts match the data, including near the edge

For 6 listings — `lst_004` (typical), `lst_022` (far above), `lst_018` (15.3% under, just outside the band), `lst_033` (13.4% under, just inside it), `lst_030` (16.3% over) and `lst_025` (17.7% over), across tops, bottoms and outerwear — `price_check` returns a `category_average` within $0.01 of the average of the *other* listings in that category, recomputed separately from `data/listings.json`, and a `verdict` that matches the 15% rule. 6 of 6, no exceptions.

**Why this target:** The tool is plain arithmetic with no model, so there is no honest reason for it to be right most of the time. What can go wrong is specific: the item counted in its own average, which shifts the number a few percent and flips verdicts near the line, or the wrong operator at the boundary. That is why the six are not random: `lst_018` and `lst_033` sit 0.3 and 1.6 points from the edge on opposite sides. The average has to be recomputed from the raw file, not read back from `price_check`, or the check only proves the tool agrees with itself.

---

## 7. A category with nothing to compare against never raises

For 3 listings whose `category` is changed to one no other listing has (`hats`, `dresses`, `scarves`), `price_check` returns a dict with `comparable_count` 0, `category_average` `None`, `percent_vs_average` `None` and `verdict` `"no comparison available"`. 3 of 3, 0 exceptions.

**Why this target:** An average over zero listings divides by zero, and a tool the loop calls on whatever item search picked must not take the run down because the data has a category with one listing in it. This is the empty case from the Tool Inventory, and the loop branches on it the way it branches on an empty search, so it has to be a normal return, never `None` and never an error. Three different categories because one passing could be luck of the name; none of them is in the data, so they all hit the same path, and 3 of 3 is the bar.

---

## 8. It leaves the item alone and adds no model calls

For 5 listings, after `price_check(item)` the `item` dict is equal to a copy taken before the call, `generate.call_count()` has not changed, and the call takes under 10 ms. 5 of 5.

**Why this target:** `price_check` runs inside the loop, between `search_listings` and `suggest_outfit`, on the same dict that criterion 3 tracks. If it changed `selected_item` even slightly, the item reaching `suggest_outfit` would no longer be the one search picked. It is also meant to be the one step that costs nothing: no model, no network. Zero added model calls is how I check that, and 10 ms is generous for reading a 40-listing file (it measured 0.13 ms), so a time over 10 ms means something slow, like a network call, got in.

---

## 9. In the loop it runs exactly when it should

For 5 queries that match, `session["price_check"]` is set, its `category` and `price` equal those of `session["selected_item"]`, and the trace shows a `price_check` step. For 5 impossible queries, `session["price_check"]` is `None`, the trace has no `price_check` step, and `session["error"]` is set. 10 of 10.

**Why this target:** This is the same kind of bug as criterion 3, state passing between steps through the session. The tool can be right and still be wired wrong: it could be called on the wrong item, or run before the empty-search branch and be given nothing. The impossible half matters as much as the matching half, because a new tool that runs on a run that should have stopped would break criterion 2. It is deterministic wiring, not model behaviour, so a single miss means the loop is wrong and the bar is 10 of 10.

---

## 10. Every listing gets exactly one consistent verdict

Across all 40 listings in `data/listings.json`, `price_check` returns without an exception, `verdict` is one of `"below typical"`, `"about typical"` or `"above typical"`, and the verdict agrees with `percent_vs_average` (below only when under -15.0, above only when over +15.0). 40 of 40, and all three verdicts must appear at least once.

**Why this target:** Criterion 6 checks six chosen listings and a sign or boundary mistake could hide in the other 34. Running every listing is cheap because there is no model, so there is no reason to sample. Requiring all three verdicts to appear guards against a band so wide or so narrow that the tool says the same thing about everything, which would pass every other check and still be useless; on this data the split is 13 below, 15 typical and 12 above. The 15% band is my choice, not something derived from the data, so this criterion tests that the tool follows its rule, not that the rule is right.

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
