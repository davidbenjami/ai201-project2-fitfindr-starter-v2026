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

FitFindr takes a plain-language thrift request like `vintage graphic tee under
$30, size M` and searches 40 secondhand listings from Depop, thredUp and
Poshmark for the best keyword match within the price and size given. For the
top result, it suggests two outfits using pieces the user already owns, or
general basics if their wardrobe is empty. It then writes a short,
post-ready caption ("fit card") that mentions the price and platform. If
nothing matches, it stops before any model call and says which part of the
request to change, such as the price limit, the size, or the words used.


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

- **What it does:** Filters the 40 listings by price and size, then scores the rest by keyword overlap with the description. A word in the title or `style_tags` scores 2; a word found only in the description, category or colors scores 1. Listings that score 0 are dropped. No model call.
- **Inputs:** <!-- name and type each: `max_price` (float), not "a price" --> `description` (str) — keywords, e.g. `"vintage graphic tee"`; `size` (str or None) — `"M"`, `"8"`, `"W30"`, or None to skip; `max_price` (float or None) — inclusive ceiling, or None to skip.
- **Returns:** A `list[dict]` of up to `config.SEARCH_RESULT_LIMIT` (10) listing dicts, best score first, with the cheaper item winning a tie. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None) and `platform`. **Size match rule:** a letter size must be a whole token of the listing's size, split on `/` and spaces (`M` matches `S/M` and `M/L`; `S` does *not* match `XL` or `US 9`). "One Size" listings match any letter size. A number matches a shoe size exactly (`8` matches `US 8`, not `US 8.5`) or a waist (`30` matches `W30 L30`).
  - > **Revised in unit 4:** "One Size" listings no longer match a letter size — they come back only when no size is given, or for size "One Size". The before-run showed a One Size belt and bucket hat returned for `vintage tee size L`, which broke criterion 5. See **The Improvement**.
- **When it has nothing:** Returns `[]`, an empty list, not None and not an exception. It also returns `[]` when the description has no usable words (e.g. only stopwords).

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for two outfits built around the new item, each with a one-sentence reason it works, in under 120 words.
- **Inputs:** `new_item` (dict) — one listing dict from `search_listings`; `wardrobe` (dict) — `{"items": [...]}`, where each item has `name`, `category`, `colors`, `style_tags` and optional `notes`. `items` may be empty.
- **Returns:** A non-empty `str` of plain text with two outfits. With a wardrobe, it names the user's pieces exactly as written in the wardrobe (e.g. "Baggy straight-leg jeans, dark wash") and uses only those.
- **When it has nothing:** With an empty wardrobe (`items == []`), it switches to a different prompt and returns general styling advice built from common basics. It doesn't raise or return `""`. If the model returns empty text, it falls back to a one-line generic suggestion naming the item.

### `create_fit_card`

- **What it does:** Asks the model for a first-person social-media caption about the find, based on the item and the outfit suggestion.
- **Inputs:** `outfit` (str) — the string `suggest_outfit` returned; `new_item` (dict) — the same listing dict.
- **Returns:** A `str` caption of 2–4 sentences that mentions the price (e.g. `$18`) and platform once each, with at most two emoji and three hashtags. It names a brand only if the listing has one (`brand` is None on most listings).
- **When it has nothing:** If `outfit` is empty or whitespace, it returns the message `"No fit card — there was no outfit suggestion to write about. Run suggest_outfit first and pass its result in."` without calling the model. If the model returns empty text, it falls back to a template caption with the title, price and platform.

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

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` that says which part of the query to change, set the next step
to `"done"`, and return the session without calling `suggest_outfit` or
`create_fit_card`. Otherwise take the first result as `session["selected_item"]`
and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent` (the `if not session["search_results"]:`
inside the `while next_step != "done":` loop). The stop message comes from
`agent.py::_no_results_message`, which re-runs the search with one filter
dropped at a time. That lets it say, for `platform sneakers size 11`, "drop the
size 11 filter — 3 match in other sizes", or name the closest match and its
price when the price limit is what's in the way, instead of just "No results". The loop counts each pass and calls
`trace.check_iterations(count)`, which raises past `MAX_ITERATIONS`.

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->
Regex, in `agent.py::parse_query`. No model call. A price pattern
(`under|below|less than|max|up to` followed by `$N`, or a bare `$N`) sets
`max_price`. A `(in) size X` pattern sets `size` (`M`, `XXS`, `8`, `US 8.5`,
`W30`). Both matches are cut out of the text, along with leading filler like
"looking for a", and what's left is the `description`. For example,
`vintage graphic tee under $30, size M` →
`{"description": "vintage graphic tee", "size": "M", "max_price": 30.0}`.

**What moves through the session:** <!-- which fields, in what order -->
`query` → `parsed` (description / size / max_price) → `search_results` (list of
listing dicts) → **branch** → `selected_item` (`search_results[0]`) →
`outfit_suggestion` (str) → `fit_card` (str). `wardrobe` is set at the start and
read by `suggest_outfit`. On the empty path the order stops at
`search_results` → `error`, and `selected_item`, `outfit_suggestion` and
`fit_card` stay `None`. Each tool reads its inputs from the session, not
from local variables, so every step can be printed and checked afterwards.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit One
Y2K Baby Tee — Butterfly Print paired with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and Black crossbody bag. This outfit works because the fitted butterfly tee balances the voluminous dark denim for an effortless, classic Y2K silhouette.

Outfit Two
Y2K Baby Tee — Butterfly Print paired with Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots. This outfit works because pairing the feminine graphic top with rugged boots and structured outerwear creates a cool, balanced contrast of styles.

  Fit card: Scored this little butterfly tee on depop for just $18 and I’m obsessed. I love dressing it down with baggy denim and chunky sneakers for that classic Y2K look, or toughening it up with trousers and combat boots. Such a versatile vintage find! 🦋✨

#y2kstyle #thrifted #babytee
```

And the empty path, which stops before any model call:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown' in size XXS under $5. To find something: try different words for the item (e.g. 'jacket', 'tee', 'jeans', 'sneakers') — nothing in the listings matches that description.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1
Pair the Vintage Levi's 501 Jeans with the white ribbed tank top, the vintage black denim jacket, and the chunky white sneakers. This works because the medium-wash denim and crisp white tank create a timeless base, while the cropped jacket and sneakers add an effortless, streetwear-inspired edge.

Outfit 2
Pair the Vintage Levi's 501 Jeans with the oversized grey crewneck sweatshirt, the brown leather belt, and the black combat boots. This works because the structured medium wash balances the heavy, oversized knit, and the boots and belt add sharp, grounding contrast.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501s on Depop for just $38 and they fit like an absolute dream. I kept it super classic today by pairing the medium wash indigo denim with my go-to white sneakers. Such an easy, effortless streetwear look 👖✨

#vintagelevis #denimstyle #streetwear
```

The empty cases, tested the same way:

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Outfit One:
Vintage Levi's 501s, a classic white cotton crewneck t-shirt, a black leather belt, and clean white canvas sneakers.
Why it works: This timeless denim-and-tee combination lets the vintage wash shine with effortless, everyday cool.

Outfit Two:
Vintage Levi's 501s, an oversized neutral-toned flannel shirt worn open over a ribbed black tank top, and chunky black loafers.
Why it works: The layered textures and boxy proportions lean into a relaxed, effortless streetwear aesthetic.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
No fit card — there was no outfit suggestion to write about. Run suggest_outfit first and pass its result in.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude (Claude Code) to implement the three stubs in `tools.py` to match my Tool Inventory spec.
- *What came back:* Working implementations, but each edit deleted the starter stub (`# TODO … return []`) outright.
- *What I changed:* I rejected the edit and had it keep the original stubs commented out above each implementation, and keep my own step-by-step comments in `run_agent` as one intact block with the code underneath. That way the diff shows what the starter was and what I replaced it with.

**Moment 2**

- *What I asked for:* An empty-search message that tells the user what to change, not just "No results".
- *What came back:* A version that re-ran the search without the price limit and reported the *cheapest* match. For `leather bomber under $40` it said "4 match without it, the cheapest at $12". That $12 item was a braided leather **belt**, not a bomber, so the advice pointed at the wrong item.
- *What I changed:* I had it report the *top-scoring* match instead ("the closest match, 90s Leather Bomber — Black, is $75"), so the suggested price is for the item the user actually asked about. Testing that query also showed that `leather bomber under $40` *does* return the belt as a match, because "leather" alone scores. I kept that behaviour and noted it below as a known weakness, rather than hiding it.

**Known weakness found while testing:** search is a plain keyword match, so a
query that shares a single word with an unrelated item (`leather bomber under
$40` → *Leather Belt — Brown, Braided*) "succeeds" with the wrong kind of item.
This is the reason criterion 1 targets 4 of 5 and not 5 of 5.

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

Full log: [results/run_2026-10-07_1950_before.md](results/run_2026-10-07_1950_before.md)
(`run_eval.py --label before`, caching off, temperature 0.9).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item = `search_results[0]`, named in outfit and card | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Card has exact price + platform, ≤ 4 sentences, no repeated first sentence | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result respects the parsed price and size | 5 of 5 | PASS | PASS | PASS | PASS | FAIL | MISSED (4/5) |

For criterion 5, Try N is query N in `scenarios.py` (M + $30, W30 + $40,
8.5, S, L + $25). Search has no model call in it, so each query gave the same
results on all five of its runs. Try 5 (`vintage tee size L under $25`)
failed on every run.

The empty-wardrobe diagnostic (`denim jacket under $50`, empty wardrobe)
completed 5 of 5, with general styling advice instead of wardrobe pieces.

**Real output from one try**: `agent.py::run_agent`, with
`tools.py::suggest_outfit` and `tools.py::create_fit_card`, query
`black jeans under $40` (criterion 3, try 1):

```
- selected_item: Straight Leg Black Jeans — Faded ($30.0, thredUp)
- search_results: 9

Outfit suggestion:
Outfit 1
Pair the new Levi's jeans with the black cropped zip hoodie and black combat boots. This works because the faded black wash and cropped silhouette create an effortlessly cool, monochromatic grunge look.

Outfit 2
Pair the new Levi's jeans with the white ribbed tank top, oversized grey crewneck sweatshirt worn on top, and chunky white sneakers. This works because layering the bright white tank under the oversized grey knit adds great texture and casual, vintage-inspired contrast.

Fit card:
Scored these faded Levi's straight leg jeans on thredUp for just $30 and I'm obsessed. I love dressing them down with an oversized grey crewneck and fresh sneakers for an easy, vintage-inspired vibe. 🖤👖 #thrifted #denimstyle #grungeaesthetic
```

And the miss: `tools.py::search_listings` over MCP for
`vintage tee size L under $25` (criterion 5, try 5):

```
[2] search_listings (via MCP)
      in:  description='vintage tee', size='L', max_price=25.0
      out: 4 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Leather Belt — Brown, Braided … +1 more
```

The last two results are `Leather Belt — Brown, Braided` (size `One Size (adjustable)`)
and `Bucket Hat — Reversible, Brown Plaid` (size `One Size`).

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
| 1 | Matching query completes | 4 of 5 | MET (5/5) | A try passed if `session["error"]` was None and `session["fit_card"]` was a non-empty string. |
| 2 | Impossible query stops early | 5 of 5 | MET (5/5) | A try passed if `session["error"]` was set, `outfit_suggestion` and `fit_card` were still None, and the trace ended at step 2 with "branch: empty". The message names what to change (reword the item), not just "No results". |
| 3 | Item carries through the session | 5 of 5 | MET (5/5) | `selected_item["id"] == search_results[0]["id"]` (lst_037 every time), and the outfit and card each contained the title or a word of 4+ letters from it ("jeans", "faded", "straight"). |
| 4 | Fit card quality | 4 of 5 | MET (5/5) | Each card contained "$42" and "poshmark" and had at most 4 sentences (hashtag lines not counted). The five first sentences were compared; all 5 were different strings. |
| 5 | Search respects filters | 5 of 5 | MISSED (4/5) | For each result, checked `price <= max_price` and that the asked-for size is a whole token of the listing's size. Four queries passed; `vintage tee size L under $25` returned two "One Size" items. |

**Diagnoses**

**Criterion 5 (missed, 4/5): in a tool, `tools.py::_size_matches`.** Price
was never the problem; every result was under the ceiling. The miss was the
size filter. When I wrote the size rule in unit 3, I added "One Size listings
match any letter size", so `_size_matches("L", "One Size (adjustable)")`
returned True. Two things combined. That shortcut let every One Size listing
(belts, hats, bags) through any letter-size filter. Then the keyword scorer
gave them a point for "vintage", which is in their style tags. So a search
for a size-L tee came back with a belt and a bucket hat. The loop, the
branch and the session all did their jobs. The tool's own spec disagreed
with criterion 5, which says the size has to appear in the listing's size.
It happens on every run because search is deterministic, so this is one bug,
not five separate failures.

There were no misses on 1–4 in the before run.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

From `results/run_2026-10-07_1950_before.md`, produced by `trace.step()`
calls in `agent.py::run_agent`. The same output prints with
`python app.py ask '...' --trace`.

**Happy path**: `vintage graphic tee under $30`, four steps:

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    branch: results, selected id lst_002
[3] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Outfit 1: Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark wash, black crossbod…
      →    wardrobe has 10 items
[4] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Scored this dreamy butterfly baby tee for just $18 on depop and I'm so obsessed. I love balancing the fitted p…
```

**Empty search**: `designer ballgown size XXS under $5`, which stops at step 2:

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

Nothing matched 'designer ballgown' in size XXS under $5. To find something: try different words for the item (e.g. 'jacket', 'tee', 'jeans', 'sneakers') — nothing in the listings matches that description.
```

**The three failure modes, triggered on purpose**

1. *Empty search*: shown above. The run stops after step 2, and
   `suggest_outfit` is never called.
2. *Empty wardrobe*: `python app.py ask 'denim jacket under $50' --trace --empty-wardrobe`.
   `suggest_outfit` sees 0 items and asks for general styling advice
   instead, so the run still completes:
   ```
   [3] suggest_outfit
         in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
         out: Outfit One: White crewneck t-shirt, black high-waisted wide-leg trousers, and white canvas sneakers.  This wor…
         →    wardrobe has 0 items — general styling advice
   ```
3. *Model unreachable*: a bad key, set as an environment variable so
   `.env` was not touched: `GEMINI_API_KEY=AIzaBADKEY000 python app.py ask 'vintage graphic tee under $30' --trace`.
   `generate()` raises `ModelUnavailable`, and `run_agent` catches it, sets
   `session["error"]` and stops, with no stack trace:
   ```
   [3] suggest_outfit
         in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
         out: ModelUnavailable
         →    model unreachable, stopping

     Found a match, but the styling model couldn't be reached, so there's no outfit or fit card this time. Check GEMINI_API_KEY in .env and your connection, then try again. (Details: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.)
   ```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

`mcp_server.py` registers `search_listings` with FastMCP. It has the same typed
inputs as the Tool Inventory (`description: str`, `size: str | None`,
`max_price: float | None`). Its description gives the units (US dollars,
inclusive), the size rules, and the empty case (`[]`, not an error).
`python mcp_client.py` lists it with `description: string`,
`size: string (optional)` and `max_price: number (optional)`. In
`agent.py::run_agent`, the direct `search_listings(...)` call became
`call_tool("search_listings", {...})`. If the server can't be reached,
`MCPError` is caught and the run stops with a message.

Nothing behaved differently afterwards. Before rewiring, I checked
`call_tool("search_listings", {"description": "vintage graphic tee", "size": None, "max_price": 30})`
against the direct call: `==` was True, with the same 10 dicts in the same
order and prices still floats. An empty search still comes back as `[]`, so
the branch didn't need to change. The only visible difference is speed:
each call starts the server as a subprocess. (`_no_results_message` still
calls `search_listings` directly for its re-searches, because it's an
internal helper, not a step of the loop.)


---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** In `tools.py::_size_matches` I removed the shortcut
that let "One Size" match any letter size. The old lines are kept as
comments. A letter size now has to be a whole token of the listing's size,
and One Size listings only match a request for "One Size". I updated the
MCP tool description and the Tool Inventory to say the same thing. I made
no other change. The MCP server imports from `tools.py`, so the fix reached
the agent with no change to the server code.

**Which failure it was meant to fix:** Criterion 5. The diagnosis was a
tool-spec bug in `_size_matches` (the One Size shortcut), not the loop or
the model, so the fix went in that one function.

### Run Log — After

Full log: [results/run_2026-10-07_1957_after.md](results/run_2026-10-07_1957_after.md)

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item = `search_results[0]`, named in outfit and card | 5 of 5 | PASS | PASS | PASS | PASS | FAIL | MISSED (4/5) |
| 4. Card has exact price + platform, ≤ 4 sentences, no repeated first sentence | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result respects the parsed price and size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes, for the criterion it targeted.
`vintage tee size L under $25` now returns only `Vintage Band Tee — Faded Grey`
(L) and `Graphic Tee — 2003 Tour Bootleg Style` (L) on all five runs, and
the other four filter queries return what they did before. `python test.py`
still passes 10/10.

The after run also has a new miss on **criterion 3**, which the fix did not
cause. That scenario (`black jeans under $40`) gives no size, so
`_size_matches` is never called on it. Its search results were the same
before and after, and `selected_item` was `lst_037` = `search_results[0]`
on all 5 tries, so the state check passed. Try 5 failed on the "mentions
the item" half. The fit card read *"Scored these worn-in Levi's for just $30
on thredUp…"*. It names the item only by its brand, and no word from the
title ("Straight Leg Black Jeans — Faded") appears in it. **Place: the
model's output in `create_fit_card`. Mechanism:** `_describe_item` puts
`Brand: Levi's` in the prompt, and at temperature 0.9 the model sometimes
uses the brand as the item's name instead of the title. The card is about
the right item, but my criterion only accepts title words, so it counts as
a miss.

### Check run

Full log: [results/run_2026-10-11_2140_check.md](results/run_2026-10-11_2140_check.md)
(`run_eval.py --label check`, same code as the after run, caching off,
temperature 0.9). I ran it again to see whether the criterion 3 miss
would come back.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item = `search_results[0]`, named in outfit and card | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Card has exact price + platform, ≤ 4 sentences, no repeated first sentence | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result respects the parsed price and size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 5 gave the same results as the after run: 2, 1, 1, 1 and 2
results, every one within the price and with the asked-for size. Criterion 3
passed this time, but only just. On tries 2 and 5 the card names the item
by brand plus one title word, "faded". Try 5 is almost word for word the
after run's failing card, with "faded" where that card had "worn-in":

```
Scored these faded Levi's for just $30 on thredUp and they instantly became my go-to pair.
```

So the criterion 3 miss is real and intermittent. It depends on one word
the model picks, and 5/5 here doesn't mean it's fixed. The empty-wardrobe
diagnostic completed 5 of 5 again, with general styling advice.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

- **Criterion 3 (4/5 after, 5/5 on the check run).** The miss is in how the
  card names the item, not in the state. The check run passed, but two of
  its five cards hung on the single word "faded", so it can miss again. Two ways to fix it: tell the `create_fit_card` prompt to
  use a word from the item's title, or decide that the brand is an
  acceptable way to name the item. The second would change what the
  criterion measures, so it would need a written revision in
  `criteria.md`, kept under the original. I stopped because Milestone 5
  asks for one change measured properly, and this miss showed up in the
  after run.
- **Criterion 4 passes, but it's a weak check.** All five first sentences
  are different strings, but they're nearly the same template: *"Scored
  this vintage cropped Wrangler jacket on poshmark for just $42 and I'm
  obsessed."* Exact-string comparison can't catch this. A stricter version
  would compare the first several words, or word overlap. I haven't
  changed the criterion.
- **Keyword search lets in loose matches.** `graphic tee size M` still
  returns `Mesh Long-Sleeve Top — Black` second, and `black jeans` returns
  `Biker Shorts — Black, Shiny`, because one shared word ("black", "top")
  is enough to score. None of my criteria test relevance, so this doesn't
  show up as a miss. It's the same weakness noted in unit 3
  (`leather bomber` → belt).
- **Asking for "One Size" by name doesn't parse.** `parse_query("belt size one size")`
  pulls out size `ONE`, so the new One Size rule can't be reached from a
  typed query. Only a direct or MCP call with `size="One Size"` reaches it.
  The fix is to have the `_SIZE` regex in `agent.py` recognise "one size"
  as a phrase.


<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [x] criteria.md has five numbered criteria, each with a target
       [x] Each criterion has a reason underneath it
       [x] All five unit 3 sections above have real content
       [x] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [x] Planning Loop names the branch rule and agent.py::run_agent
       [x] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
