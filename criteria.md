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

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
The search half of this path is deterministic — same query, same results — but
the other two steps are model calls through `generate()`, and on the free tier
one of five runs can hit a rate-limit retry or a model error that ends the run
without a fit card. 4 of 5 allows for one of those; it doesn't allow for the
loop itself being wrong, which would fail every try.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never calls the model. `search_listings` is pure Python over a fixed
file, and the stop message is built by re-running that same search with one
filter dropped, so nothing on this path can vary between tries. If it fails
once it will fail every time, so anything under 5 of 5 means the branch is broken.

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

For a matching query, `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and the outfit suggestion and the fit
card each mention the selected item (its title or a word from its title) —
in 5 of 5 tries.

**Why this target:**

The IDs are compared in code, with no model involved: `run_agent` reads the
item out of the session and passes it to both later tools, so if the ID check
fails even once, the wrong thing is moving through the session. The "mentions
the item" half rests on the model, but both prompts put the item's title at the
top, so a card about some other piece would point to a state bug rather than
the model's wording. That's why I hold it to 5 of 5 too.

---

## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

The fit card states the selected item's exact price (e.g. "$18") and its
platform, is no longer than 4 sentences (hashtags not counted), and for the
same item run 5 times no two cards share the same first sentence — in at least
4 of 5 tries.

**Why this target:**

The prompt asks for the price and platform once each and for two to four
sentences, but the model doesn't always follow those rules. At temperature 0.9
I expect one try in five to drift, such as writing "under twenty bucks" instead
of "$18", or adding a fifth sentence. 5 of 5 would be asking the model for a
guarantee the prompt can't give. The opening-sentence rule is there to catch
the cache or a temperature of 0, which would make every card identical.

---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Every listing in `session["search_results"]` respects the parsed filters: its
price is at or under the max_price from the query, and when a size was given,
the listing's size contains that size as a whole token (so "M" matches "S/M"
but "S" never matches "XL" or "US 9") — 5 of 5 tries, across five different
queries that each set a price, a size, or both.

**Why this target:**

A price or size filter that's wrong would be the worst kind of failure,
because the user would see a real-looking result for something they can't
buy or can't wear. Both filters are deterministic code in `search_listings`
with no model involved, so the only way to miss is a bug in `_size_matches`
or the regex in `parse_query`, which is exactly what this test is for. The
listing sizes are in three formats (letters, `US 8.5`, `W30 L30`), and a
substring test would quietly fail on them.

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
