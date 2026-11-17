# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
FitFindr takes a plain-language shopping request (e.g. "vintage graphic tee under $30") and searches thrift listings for matches on description, size, and price. If it finds a match, it suggests an outfit pairing using the user's existing wardrobe, then writes a short caption-style "fit card" describing the find, its price, and platform. If nothing matches the search, the agent stops and reports why instead of continuing with no item.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings data by price ceiling and size (whole-token match, so a query for size "M" doesn't match inside "XL" or "US 9"), then scores what's left by keyword overlap between the description and each listing's title/description/category/style_tags.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None)
- **Returns:** A list of listing dicts (`id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`), highest keyword-overlap score first, capped at `config.SEARCH_RESULT_LIMIT`.
- **When it has nothing:** Returns `[]` — an empty list — when nothing passes the price/size filters, or nothing scores above zero on keyword overlap.

### `suggest_outfit`

- **What it does:** Calls the model to suggest one or two outfits pairing a thrifted item with pieces from the user's wardrobe.
- **Inputs:** `new_item` (dict — a listing), `wardrobe` (dict with an `'items'` key holding a list of wardrobe item dicts)
- **Returns:** A non-empty string, 2-3 sentences, naming specific wardrobe pieces by name in the pairing.
- **When it has nothing:** If `wardrobe['items']` is empty, it asks the model for general styling advice for the item instead of pairing it with pieces that don't exist — still a non-empty string, never `""`.

### `create_fit_card`

- **What it does:** Calls the model to write a short, social-post-style caption about the find, built from the item's details and the outfit suggestion.
- **Inputs:** `outfit` (str — the output of `suggest_outfit`), `new_item` (dict — a listing)
- **Returns:** A non-empty string, 2-4 sentences, mentioning the item, its price, and its platform exactly once each.
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns a descriptive fallback message (naming the item, price, and platform) instead of calling the model or raising.

### `price_check` (fourth tool, added as the extension)

- **What it does:** Compares a listing's price with the average price of every *other* listing in the same category (tops, bottoms, outerwear, shoes, accessories) and says whether it is cheap, typical, or pricey. No model call.
- **Inputs:** `new_item` (dict — a listing; needs `id`, `category`, `price`)
- **Returns:** A dict: `category` (str), `price` (float), `comparable_count` (int), `category_average` (float, 2 decimals), `percent_vs_average` (float, signed, 1 decimal), and `verdict` (str): `"below typical"`, `"about typical"` (within 15% of the average), or `"above typical"`.
- **When it has nothing:** If no other listing shares the category, it still returns a dict, with `comparable_count` 0, `category_average` and `percent_vs_average` set to `None`, and `verdict` `"no comparison available"`. Never `None`, never an exception.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what to change (loosen the price, drop the size, use broader keywords) and stop — do not call `suggest_outfit`. Otherwise take the first result as `session["selected_item"]` and continue on to `suggest_outfit` and then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. One pattern pulls `under $X` into `max_price`, another pulls `size Y` into `size`, and whatever text is left (with leftover connector words like a trailing "in" cleaned up) becomes `description`.

**What moves through the session:** `parsed` (the dict from `parse_query`) → `search_results` (the full list from `search_listings`) → `selected_item` (the first of those) → `price_check` (from `price_check`) → `outfit_suggestion` (from `suggest_outfit`) → `fit_card` (from `create_fit_card`). `error` is set instead, and everything after it stays `None`, if the branch stops the run early.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for an effortless, nostalgic daytime look. Layer the black cropped zip hoodie over top and accessorize with your black crossbody bag to lean into that authentic turn-of-the-millennium aesthetic.

  Fit card: Scored this absolute dream of a butterfly print baby tee on Depop for just $18 and I'm officially never taking it off. It's giving major 2000s mall-rat energy, especially paired with my favorite baggy jeans and chunky sneakers. Pure Y2K perfection!

2 model calls this session, 374 prompt + 121 output tokens
```

**The three tools, tested one at a time**

```
$ python -c "from pprint import pprint; from tools import search_listings; pprint(search_listings('graphic tee', max_price=30))"

[{'brand': None,
  'category': 'tops',
  'colors': ['white', 'pink', 'purple'],
  'condition': 'excellent',
  'description': 'Super cute early 2000s baby tee with butterfly graphic. '
                 'Fitted crop length. Tag says medium but fits like a small.',
  'id': 'lst_002',
  'platform': 'depop',
  'price': 18.0,
  'size': 'S/M',
  'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'],
  'title': 'Y2K Baby Tee — Butterfly Print'},
 {'brand': None,
  'category': 'tops',
  'colors': ['black'],
  'condition': 'good',
  'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy '
                 'fit. 100% cotton, soft and worn-in.',
  'id': 'lst_006',
  'platform': 'depop',
  'price': 24.0,
  'size': 'L',
  'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'],
  'title': 'Graphic Tee — 2003 Tour Bootleg Style'},
 {'brand': None,
  'category': 'tops',
  'colors': ['black'],
  'condition': 'excellent',
  'description': 'Sheer black mesh long-sleeve. Great for layering under a '
                 'graphic tee or over a bralette. Stretchy material, fits true '
                 'to size.',
  'id': 'lst_017',
  'platform': 'depop',
  'price': 15.0,
  'size': 'S/M',
  'style_tags': ['y2k', 'grunge', 'goth', 'layering'],
  'title': 'Mesh Long-Sleeve Top — Black'},
 {'brand': None,
  'category': 'tops',
  'colors': ['grey', 'charcoal'],
  'condition': 'fair',
  'description': 'Faded grey band-style tee with distressed graphic. Crew '
                 'neck. Fits boxy. Well-loved but no holes or major damage.',
  'id': 'lst_033',
  'platform': 'depop',
  'price': 19.0,
  'size': 'L',
  'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'],
  'title': 'Vintage Band Tee — Faded Grey'},
 {'brand': None,
  'category': 'bottoms',
  'colors': ['khaki', 'tan'],
  'condition': 'fair',
  'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, '
                 'slightly distressed at the hems. Great for layering with a '
                 'long tee.',
  'id': 'lst_011',
  'platform': 'poshmark',
  'price': 27.0,
  'size': 'W29',
  'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'],
  'title': 'Low-Rise Cargo Pants — Khaki'},
 {'brand': None,
  'category': 'tops',
  'colors': ['navy'],
  'condition': 'good',
  'description': 'Perfectly faded navy crewneck. Genuinely vintage — not '
                 'manufactured distressed. Ribbed cuffs and hem. No graphics, '
                 'clean.',
  'id': 'lst_012',
  'platform': 'thredUp',
  'price': 20.0,
  'size': 'XL (fits oversized)',
  'style_tags': ['vintage', 'basics', 'oversized', 'classic'],
  'title': 'Oversized Crewneck Sweatshirt — Vintage Navy'},
 {'brand': None,
  'category': 'tops',
  'colors': ['black', 'charcoal'],
  'condition': 'fair',
  'description': 'Faded black pullover hoodie with barely-visible vintage '
                 'graphic on the chest. Cozy interior. Some pilling but adds '
                 'to the worn-in look.',
  'id': 'lst_015',
  'platform': 'depop',
  'price': 26.0,
  'size': 'L',
  'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'],
  'title': 'Vintage Graphic Hoodie — Faded Black'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[1], get_example_wardrobe()))"

Pair the Y2K butterfly tee with your baggy dark-wash straight-leg 
jeans and chunky white sneakers for a classic, nostalgic 2000s 
street style look. Layer your black cropped zip hoodie over top 
on cooler days, accessorizing with your black crossbody bag.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Scored these vintage Levi's 501 jeans for just $38.0 on Depop, 
and the medium wash is absolute perfection. They're giving 
effortless off-duty model when I pair them with my crisp white 
sneakers. Seriously never taking these off.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to help build the planning loop in `agent.py`, including `parse_query()` to pull `description`, `size`, and `max_price` out of a free-text query with regex.
- *What came back:* The first version of `parse_query` stripped the `under $X` and `size Y` phrases out correctly, but on a query like "silk slip dress in midi length under $40" it left a dangling connector word (`"in"`) at the end of the description once the price phrase was removed.
- *What I changed:* I had it add a cleanup step that strips a trailing `"in"` and stray punctuation after the size/price substrings are removed, and verified it against all six example queries in `app.py` before moving on.

**Moment 2**

- *What I asked for:* I had Claude run `app.py ask` and each of the three tools from the terminal and paste the real output into the Sample Run section.
- *What came back:* Its first draft of the `search_listings` test trimmed the long list of result dicts down to a summary with `...` in place of the full fields, to keep it readable.
- *What I changed:* I had it replace that with the exact, unmodified output the command actually printed — the README is explicit that it wants pasted text matching what printed, not a cleaned-up summary, so a trimmed version wouldn't hold up.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 2. impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 3. selected item reaches suggest_outfit unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 4. fit card mentions price and platform, 5 different items | 5 of 5 | — | — | — | — | — | **MISSED — not measurable with this harness** |
| 5. price ceiling respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |

Criteria 1, 2, 3, and 5 came from `python run_eval.py --label before`, one
scenario per criterion in `scenarios.py`, five tries each. Full output for
every try is in
[`results/run_2026-10-12_1351_before.md`](results/run_2026-10-12_1351_before.md).

Criterion 4 is marked MISSED here for a different reason than 1-3 and 5 ever
could be: it names 5 *different* items, but `run_eval.py` runs one scenario
(one query) five times under one criterion row, not five different queries.
There's no way to produce "5 different items, one row" from the harness as
built — the criterion can't be measured by the tool meant to measure it, not
that the behavior failed. (I did also run it directly outside `run_eval.py` —
5 different listings through `create_fit_card`, each caption checked for
price and platform — and all 5 passed. That's informal evidence the
*behavior* is fine; it just isn't the evidence this harness produces, so the
row stands as MISSED until that's fixed properly.)

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```
tools.py::create_fit_card — lst_004, "90s Track Jacket — Navy/White Stripe"
($45.0, poshmark)

Scored this vintage 90s Champion track jacket on Poshmark for just $45, and
the navy and white stripes give off the ultimate retro trackstar energy. I'm
thinking oversized baggy denim and chunky white sneakers for the full
effortless streetwear vibe. Absolute secondhand win!

mentions price: True, mentions platform: True
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | All 5 tries of `vintage graphic tee under $30` returned a non-empty `fit_card` with `error` still `None`. |
| 2 | Impossible query stops before the second tool | 5 of 5 | MET (5/5) | All 5 tries of `designer ballgown size XXS under $5` set `session["error"]` and left `outfit_suggestion`/`fit_card` at `None`, confirmed by the trace stopping at step `[3] branch`. |
| 3 | Selected item reaches suggest_outfit unchanged | 5 of 5 | MET (5/5) | All 5 tries showed the same item (`90s Track Jacket — Navy/White Stripe`, id `lst_004`) in the `[2] search_listings` output and as the `in:` value of `[3] suggest_outfit` — same id, every try. |
| 4 | Fit card mentions price and platform, 5 different items | 5 of 5 | **MISSED** | `run_eval.py` runs one scenario (one query) five times per criterion row — it has no way to put 5 *different* items under a single row, which is what the criterion actually asks for. The row can't be filled in from `results/`, so it's MISSED as a harness gap, not a behavior failure. |
| 5 | Price ceiling respected | 5 of 5 | MET (5/5) | Checked every listing in `search_results` for `vintage under $50` against `price <= 50` — 0 violations across 10 results, identical on all 5 tries since the filter has no model call to vary it. |

**Diagnoses**

Criteria 1, 2, 3, and 5 all MET. That's worth being honest about rather than
inventing a problem: criteria 2, 3, and 5 test deterministic code
(`parse_query`, the branch in `run_agent`, and the price filter in
`search_listings`), so there was never much room for them to fail once the
tools were written correctly. Criterion 1 is the one that touches the model
and search scoring, and it held up too, but with less margin — a
keyword-overlap search is exactly where I'd expect a miss to show up first
across a larger batch of queries.

Criterion 4 MISSED, and the mechanism is specific: it's not a tool, a loop
branch, or a session-state bug — it's that `scenarios.py` + `run_eval.py`
test *one query, five tries* per criterion, and criterion 4 is written
around *five different items*. Those are different shapes of evidence, and
the harness only produces one of them. I confirmed the underlying behavior
is actually fine (ran `create_fit_card` on 5 different listings directly,
all 5 captions had price and platform), but that confirmation lives outside
`results/`, so it doesn't count as this unit's evidence. The real fix is
Milestone 4's problem: either write a small script that produces this
evidence properly, or revise the criterion so it fits the harness that
exists.



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Pair the Y2K butterfly tee with the baggy dark-wash straight-leg jeans, chunky white sneakers, and the black c…
[4] create_fit_card
      in:  Pair the Y2K butterfly tee with the baggy dark-wash straight-leg jeans, chunky white sneakers, and the black c…
      out: Found the holy grail of 2000s mall-goth nostalgia on Depop today for just $18. I am so obsessed with this litt…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K butterfly tee with the baggy dark-wash straight-leg jeans, chunky white sneakers, and the black crossbody bag for an effortless, classic 2000s street-style look. Alternatively, layer the baby tee under the black cropped zip hoodie paired with the wide-leg khaki trousers and black combat boots to lean into a grungier, mixed-aesthetic vibe.

  Fit card: Found the holy grail of 2000s mall-goth nostalgia on Depop today for just $18. I am so obsessed with this little butterfly baby tee! Going to live in this exact piece all summer long. 🦋✨

2 model calls this session, 395 prompt + 131 output tokens
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch
      →    search_results empty — stopping before suggest_outfit

  No listings matched that search. Try loosening the price ceiling, dropping the size filter, or using broader keywords.

0 model calls this session
```

**On the MCP move:** `agent.py` no longer imports `search_listings` directly from `tools.py` — it imports `call_tool` from `mcp_client.py` and calls `call_tool("search_listings", {...})` instead, with `mcp_server.py` registering that same function (described for a reader who can't see the code) behind the MCP protocol. The rewire worked cleanly: the trace line `[2] search_listings (via MCP)` shows it going out over MCP, and the return value came back as the identical list of dicts the direct call used to produce — same shape, same content, nothing downstream had to change.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** I replaced the single "fit card mentions price and
platform" scenario in `scenarios.py` with five separate scenarios — one per
criterion-4 item — each carrying a query chosen so a different listing
(`lst_001`, `lst_002`, `lst_004`, `lst_019`, `lst_034`) comes back as
`search_results[0]`. `run_eval.py` itself didn't need to change: it already
groups rows by criterion number, so five scenarios tagged `"criterion": 4`
just become five rows under criterion 4 instead of a workaround script
outside the graded evidence trail.

**Which failure it was meant to fix:** Criterion 4's MISSED verdict in the
Before run — not a tool or loop bug, but the harness having no way to put 5
different items under one criterion with the single-scenario, five-tries
shape everything else used.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 2. impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 3. selected item reaches suggest_outfit unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 4. fit card mentions price and platform, 5 different items | 5 of 5 | PASS (lst_001) | PASS (lst_002) | PASS (lst_004) | PASS (lst_019) | PASS (lst_034) | 5/5 — MET |
| 5. price ceiling respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |

Full output: [`results/run_2026-10-12_1406_after.md`](results/run_2026-10-12_1406_after.md),
produced by `python run_eval.py --label after`. Criterion 4's "Try" columns
here are its five scenario rows (one real item each), not five tries of one
scenario — `lst_001` a $38 Depop find, `lst_002` an $18 Depop tee, `lst_004` a
$45 Poshmark jacket, `lst_019` a $48 Poshmark sneaker, `lst_034` a $14 thredUp
hat — and every resulting caption named that item's own price and platform:

```
tools.py::create_fit_card — lst_019, "Platform Sneakers — White Chunky Sole"
($48.0, poshmark)

Scored these chunky white platform sneakers on Poshmark for just $48, and
they are giving major Y2K off-duty model energy. Can't wait to style them
with baggy dark-wash denim and a little ribbed tank for the ultimate
effortless street style look.
```

**Did it help, and how do I know:** Yes. Criterion 4 went from MISSED (no
measurable row at all) to MET (5/5), and I know because the evidence now
sits in `results/run_2026-10-12_1406_after.md` in exactly the shape the
other four criteria's evidence takes — five rows, each one a real tool
call, each one checkable without a side script. Criteria 1, 2, 3, and 5
didn't move — they were already MET before, and they're still MET after,
which is what I'd expect since nothing about `parse_query`, the branch, or
the price filter changed. The improvement was entirely in how criterion 4
gets measured, not in the agent's behavior.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## Extension — `price_check`

**What I added:** A fourth tool, `tools.py::price_check`, that tells the user whether the item the agent found is cheap, typical, or pricey for its category. `agent.py::run_agent` calls it right after it picks `selected_item` (step 3 in the trace), stores the result in `session["price_check"]`, and `app.py ask` prints it as a `Price:` line. The empty-search branch is unchanged, so it stops before the new tool runs. The contract is in the Tool Inventory above.

**Why this one:** It is small and deterministic, so I can check its numbers by hand, and it uses data the agent already has. The "typical" band is 15% either side of the category average. I chose that by eye, and it is not tuned on anything.

**Evidence that it does what I claim**

The tool on its own, on four real listings and one made-up category:

```
$ python -c "from tools import price_check; from utils.data_loader import load_listings; L={l['id']:l for l in load_listings()}; [print(i, L[i]['title'], L[i]['price'], price_check(L[i])) for i in ('lst_002','lst_022','lst_004','lst_001')]"

lst_002 Y2K Baby Tee — Butterfly Print 18.0
{'category': 'tops', 'category_average': 22.0, 'comparable_count': 14, 'percent_vs_average': -18.2, 'price': 18.0, 'verdict': 'below typical'}
lst_022 90s Leather Bomber — Black 75.0
{'category': 'outerwear', 'category_average': 39.57, 'comparable_count': 7, 'percent_vs_average': 89.5, 'price': 75.0, 'verdict': 'above typical'}
lst_004 90s Track Jacket — Navy/White Stripe 45.0
{'category': 'outerwear', 'category_average': 43.86, 'comparable_count': 7, 'percent_vs_average': 2.6, 'price': 45.0, 'verdict': 'about typical'}
lst_001 Vintage Levi's 501 Jeans — Medium Wash 38.0
{'category': 'bottoms', 'category_average': 28.44, 'comparable_count': 9, 'percent_vs_average': 33.6, 'price': 38.0, 'verdict': 'above typical'}
```

I checked the first by hand: the 14 other tops in `data/listings.json` sum to 308, and 308 / 14 = 22.0, so $18 is 18.2% under. All three verdicts were reached. The empty case, a listing in a category nobody else is in (`category` set to `"hats"`), returned `comparable_count` 0, both averages `None`, and verdict `"no comparison available"`, not an error.

In the loop, on a query that matches:

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
[2] search_listings (via MCP)
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] price_check
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: dict with keys: category, price, comparable_count, category_average, percent_vs_average, verdict
[4] suggest_outfit
[5] create_fit_card

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  Price:    below typical for tops — 18% under the $22.00 average
```

On a query that matches nothing, the run is the same length as before and the new tool never runs:

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

[1] parse_query
[2] search_listings (via MCP)
      out: [] (empty)
[3] branch
      →    search_results empty — stopping before suggest_outfit
```

Nothing that already worked broke. `python test.py` passed 10 of 10, and I re-ran the whole five-criteria eval with the new tool in the loop (`results/run_2026-11-11_1635_extension.md`, 10 scenarios × 5 tries). `price_check` ran on all 45 tries that completed and on none of the 5 impossible-query tries. Every one of those 5 stopped early, and the other 45 completed. The run file leaves its Verdict column blank, so I counted completions from the trace; I did not re-score the criteria in this table.

**What this does not show:** `price_check` only compares against the 40 listings in `data/listings.json`, so the "typical" price is typical for this data, not for the market. Shoes (4 listings) and accessories (3) are small groups, so their averages move a lot when one listing changes. The fit card and outfit prompts do not use the price verdict. It is shown to the user and nothing more.

---

## Local Run

**Start command** (full steps and what each log field means are in [RUNNING.md](RUNNING.md#run-it-locally-with-logs)):

```bash
PORT=5001 python serve.py
```

I tested it from a clean copy of the project: a new directory, a new virtualenv, `pip install -r requirements.txt`, `python test.py` (10 passed, 0 failed), then the command above. Two things that test turned up. On a Mac, `python serve.py` alone fails with "Address already in use", because AirPlay Receiver holds port 5000, which is why the command sets `PORT=5001`. And `.env.example` was missing from the repo (my commit `ab9799f` deleted it), so the `cp .env.example .env` step in RUNNING.md failed until I restored it.

**Environment:** Python 3.13.13 (3.11 to 3.13 supported, not 3.14). The pinned dependencies installed as python-dotenv 1.1.1, google-genai 1.75.0, mcp 1.30.0, Flask 3.1.3 and gunicorn 23.0.0. There are no model files: the model (`gemini-3.5-flash-lite`) runs on Google's servers, so nothing is downloaded, and the whole virtualenv is 74 MB. It needs internet and `GEMINI_API_KEY`.

**Run record.** A real session against that clean copy: one query that matches, one that matches nothing, a request with no `query`, a size-filtered query, and two requests sent at the same moment. The raw file is committed as `results/serve_run_2026-11-17.jsonl` and is pasted here unedited:

```json
{"ts": "2026-11-17T19:40:50.804+00:00", "event": "start", "port": 5001, "debug": false, "python": "3.13.13", "model": "gemini-3.5-flash-lite"}
{"ts": "2026-11-17T19:41:00.767+00:00", "event": "ask", "request_id": "b0f1a1b3", "request_number": 1, "query": "vintage graphic tee under $30", "wardrobe": "example", "wait_ms": 0, "run_ms": 2987, "total_ms": 2988, "model_calls": 2, "prompt_tokens": 388, "output_tokens": 139, "outcome": "completed", "status": 200, "error": null, "results": 10, "selected_item": "lst_002", "price_verdict": "below typical"}
{"ts": "2026-11-17T19:41:01.122+00:00", "event": "ask", "request_id": "78e16743", "request_number": 2, "query": "designer ballgown size XXS under $5", "wardrobe": "example", "wait_ms": 0, "run_ms": 339, "total_ms": 340, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "outcome": "no_match", "status": 200, "error": "No listings matched that search. Try loosening the price ceiling, dropping the size filter, or using broader keywords.", "results": 0, "selected_item": null, "price_verdict": null}
{"ts": "2026-11-17T19:41:01.133+00:00", "event": "ask", "request_id": "7ea07d08", "outcome": "bad_request", "status": 400, "reason": "missing 'query'", "total_ms": 0}
{"ts": "2026-11-17T19:41:04.322+00:00", "event": "ask", "request_id": "c81da56e", "request_number": 3, "query": "90s track jacket in size M", "wardrobe": "example", "wait_ms": 0, "run_ms": 3181, "total_ms": 3181, "model_calls": 2, "prompt_tokens": 387, "output_tokens": 139, "outcome": "completed", "status": 200, "error": null, "results": 4, "selected_item": "lst_004", "price_verdict": "about typical"}
{"ts": "2026-11-17T19:41:06.823+00:00", "event": "ask", "request_id": "585a21e2", "request_number": 4, "query": "denim jacket under $50", "wardrobe": "example", "wait_ms": 0, "run_ms": 2488, "total_ms": 2489, "model_calls": 2, "prompt_tokens": 382, "output_tokens": 130, "outcome": "completed", "status": 200, "error": null, "results": 7, "selected_item": "lst_007", "price_verdict": "about typical"}
{"ts": "2026-11-17T19:41:11.393+00:00", "event": "ask", "request_id": "c1ac343d", "request_number": 5, "query": "silk slip dress in midi length under $40", "wardrobe": "example", "wait_ms": 1973, "run_ms": 4570, "total_ms": 6543, "model_calls": 2, "prompt_tokens": 417, "output_tokens": 166, "outcome": "completed", "status": 200, "error": null, "results": 10, "selected_item": "lst_013", "price_verdict": "about typical"}
{"ts": "2026-11-17T19:41:39.742+00:00", "event": "start", "port": 5000, "debug": false, "python": "3.13.13", "model": "gemini-3.5-flash-lite"}
```

How to read it: request 1 completed with two model calls (the outfit and the fit card), picked `lst_002`, and `price_check` called it below typical. Request 2 matched nothing and made zero model calls, so `no_match` is also the cheapest outcome. The bad request logged a 400 with no model call and no request number, because it never reached the agent. The last two are the overlap: "denim jacket" ran immediately (`wait_ms` 0) and "silk slip dress" arrived half a second later and waited 1,973 ms for its turn, then ran for 4,570 ms, for 6,543 ms in total. That is the one-at-a-time lock in `serve.py` working, and the queue message printed once on the terminal.

What the log does not show: every request used the example wardrobe, so the `custom` wardrobe path was never exercised. All six agent runs succeeded, so there is no `error` outcome (an HTTP 500) in the record. The first request (2,987 ms) was no slower than the later completed ones (2,488 to 3,181 ms), so this run shows no cold-start cost.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

All five criteria are MET, so nothing here is a missed criterion — these are
gaps I can see but didn't need to fix to hit this unit's targets.

**Criterion 1's 4-of-5 target is untested.** Both runs hit the same item 5/5
on one query — that tests the model's wording variation, not the search's.
I never ran differently-phrased queries (e.g. "worn-in denim" vs. "vintage
jeans") to find where keyword overlap actually misses, so the target is a
guess, not something I've seen fail.

**`ModelUnavailable` isn't caught around `search_listings`.** It goes
through MCP now, not `generate()`, so a bad key there would surface as an
uncaught `MCPError` instead. I only tested the failure on `suggest_outfit`.

**`parse_query` is only proven on ~9 phrasings.** It's regex over free text —
an unusual phrasing ("around fifty dollars") would likely misparse silently
rather than fail loudly. None of my five criteria exercised this, so it's
untested.


<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
