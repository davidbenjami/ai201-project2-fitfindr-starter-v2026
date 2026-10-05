"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── search helpers ────────────────────────────────────────────────────────────

# Words that say nothing about the item. Left in, "a" and "for" would score a
# point against nearly every description in the data.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "on", "of", "with", "to",
    "i", "im", "i'm", "me", "my", "looking", "want", "need", "find", "some",
    "something", "any", "please", "size", "under", "below", "less", "than",
    "max", "around", "about", "like", "that", "is", "it",
}

_LETTER_SIZES = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"}


def _tokens(text: str) -> set[str]:
    """Lowercase words with a trailing plural 's' dropped, minus stopwords."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = set()
    for w in words:
        if w in _STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    Whether a listing's size satisfies the size the user asked for.

    The rule, by the shape of what was asked for:
      • A letter size ("M") matches when it is one of the listing's letter
        sizes, split on "/" and spaces — so "M" matches "S/M" and "M/L" but
        "S" does not match "XL" or "US 9". "One Size" listings match any
        letter size.
      • A number ("8", "8.5", "US 8") matches a shoe size exactly, or a waist
        size ("W30" in "W30 L30").
      • A waist ("W30") matches only the waist part of a listing's size.
    """
    wanted = wanted.strip().upper()
    have = listing_size.upper()

    if wanted in _LETTER_SIZES:
        if "ONE SIZE" in have:
            return True
        return wanted in re.findall(r"[A-Z]+", have)

    waist = re.fullmatch(r"W\s*(\d+)", wanted)
    if waist:
        return waist.group(1) in re.findall(r"W(\d+)", have)

    number = re.fullmatch(r"(?:US\s*)?(\d+(?:\.\d+)?)", wanted)
    if number:
        n = number.group(1)
        return n in re.findall(r"US\s*(\d+(?:\.\d+)?)", have) or n in re.findall(r"W(\d+)", have)

    # Anything else ("One Size"): fall back to an exact, case-insensitive match.
    return wanted == have.strip()


def _score(listing: dict, query_words: set[str]) -> int:
    """
    Keyword overlap. A word in the title or style tags is worth 2, a word that
    only appears in the category, colors or description is worth 1.
    """
    strong = _tokens(listing["title"] + " " + " ".join(listing["style_tags"]))
    weak = _tokens(
        " ".join([listing["description"], listing["category"], *listing["colors"]])
    )
    score = 0
    for word in query_words:
        if word in strong:
            score += 2
        elif word in weak:
            score += 1
    return score


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    # Starter stub, kept for reference:
    # # TODO: replace this with your implementation
    # return []

    query_words = _tokens(description or "")
    if not query_words:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = _score(listing, query_words)
        if score > 0:
            scored.append((score, listing))

    # Highest score first; cheaper wins a tie.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    # Starter stub, kept for reference:
    # # TODO: replace this with your implementation
    # return ""

    item_text = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            f"Someone is thinking about buying this secondhand piece:\n{item_text}\n\n"
            "They haven't told us anything about their wardrobe. Suggest two "
            "outfits built around this piece using common basics most people "
            "could find or already own. For each outfit, list the pieces and "
            "say in one sentence why it works. Keep it under 120 words. Plain "
            "text, no markdown headers."
        )
    else:
        closet = "\n".join(
            f"- {w['name']} ({w['category']}; colors: {', '.join(w.get('colors') or [])}"
            f"{'; ' + w['notes'] if w.get('notes') else ''})"
            for w in items
        )
        prompt = (
            f"Someone is thinking about buying this secondhand piece:\n{item_text}\n\n"
            f"Here is what they already own:\n{closet}\n\n"
            "Suggest two outfits that pair the new piece with items from their "
            "wardrobe. Name the wardrobe pieces exactly as written above, and "
            "only use pieces from that list. For each outfit, say in one "
            "sentence why it works. Keep it under 120 words. Plain text, no "
            "markdown headers."
        )

    response = generate(
        prompt,
        system="You are a practical personal stylist who specialises in thrifted and vintage clothing.",
    )
    if not response.strip():
        return f"Try the {new_item.get('title', 'piece')} with simple basics: a plain top or jeans and clean sneakers."
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    # Starter stub, kept for reference:
    # # TODO: replace this with your implementation
    # return ""

    if not outfit or not outfit.strip():
        return (
            "No fit card — there was no outfit suggestion to write about. "
            "Run suggest_outfit first and pass its result in."
        )

    prompt = (
        f"Write a caption for a social media post about this thrift find:\n"
        f"{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit}\n\n"
        "Rules:\n"
        "- Two to four sentences, written in first person like a real post, not a product listing.\n"
        f"- Mention the price (${new_item.get('price', 0):.0f}) and the platform "
        f"({new_item.get('platform', 'a thrift app')}) exactly once each.\n"
        "- Be specific about the vibe, using the outfit above.\n"
        "- Only mention a brand if one is given above.\n"
        "- At most two emoji and three hashtags. Return only the caption."
    )
    response = generate(prompt, system="You write short, authentic outfit captions for a fashion-sharing app.")
    if not response.strip():
        return (
            f"Thrifted the {new_item.get('title', 'piece')} for ${new_item.get('price')} "
            f"on {new_item.get('platform')} — styled it up and I'm obsessed."
        )
    return response


# ── shared ────────────────────────────────────────────────────────────────────

def _describe_item(item: dict) -> str:
    """A listing as a few prompt lines. Brand only appears when there is one."""
    lines = [
        f"Title: {item.get('title')}",
        f"Category: {item.get('category')}",
        f"Colors: {', '.join(item.get('colors') or [])}",
        f"Style: {', '.join(item.get('style_tags') or [])}",
        f"Condition: {item.get('condition')}",
        f"Price: ${item.get('price')} on {item.get('platform')}",
    ]
    if item.get("brand"):
        lines.insert(1, f"Brand: {item['brand']}")
    return "\n".join(lines)
