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

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
