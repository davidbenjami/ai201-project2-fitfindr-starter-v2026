"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """


    # ── MY WORK (commented out) ───────────────────────────────────────────────

#      1. Start a session with new_session().
    # session = new_session(query, wardrobe)

    # count = 0
#      2. Count the times round the loop, and call trace.check_iterations(count)
#         on each one before you go again. It raises when the count passes
#         MAX_ITERATIONS in config.py — see trace.py.

    # trace.check_iterations(count)

#      3. Parse the query into a description, a size, and a max_price. Regex,
#         string splitting, or asking the model are all fine — say which you
#         chose in your README. Put the result in session["parsed"].
#
#      4. Call search_listings() with what you parsed.
#         Put the results in session["search_results"].

#         ⚠️ THIS IS THE BRANCH. If nothing came back:
#              - put a message in session["error"] saying what the user could
#                change — "No results" is not that message
#              - return the session
#              - do NOT call suggest_outfit with nothing

#      5. Choose an item — the first result is fine. Put it in
#         session["selected_item"].
#
#      6. Call suggest_outfit() with the selected item and the wardrobe.
#         Put the result in session["outfit_suggestion"].
#
#      7. Call create_fit_card() with the outfit and the item.
#        Put the result in session["fit_card"].

#      8. Return the session.



    # pass



    # # TODO: delete these two lines and build the loop.
    # session["error"] = "The planning loop isn't built yet — see the TODO in agent.py."
    # return session

    # ── UNIT 4 INSTRUCTIONS (commented out) ──────────────────────────────────
    #
    # IN UNIT 4 you come back and add two things:
    #
    #   • Trace calls. One per step. `trace.step("search_listings", inputs=...,
    #     returned=...)` — see trace.py. Your README needs the output.
    #
    #   • A handler for ModelUnavailable, so a bad key produces a message rather
    #     than a stack trace. The import is already at the top of this file.
    #
    # And from mcp_server.py (Milestone 1) — swap the direct call:
    #
    #     results = search_listings(description, size, max_price)
    #
    # for the MCP one:
    #
    #     from mcp_client import call_tool
    #     results = call_tool("search_listings", {
    #         "description": description,
    #         "size": size,
    #         "max_price": max_price,
    #     })
    #
    # **What comes back should not change.**

    # ── CLAUDE'S WORK (live code) ────────────────────────────────────────────

    # Step 1: start the session.
    session = new_session(query, wardrobe)

    # Step 3: parse with regex (see parse_query below).
    session["parsed"] = parse_query(query)
    trace.step("parse_query", inputs=query, returned=_args_text(session["parsed"]))

    # Each pass round the loop looks at what the session holds so far and picks
    # the next step from it. "done" ends the loop on either path.
    # Step 2: count each pass and check it against MAX_ITERATIONS.
    next_step = "search"
    count = 0
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "search":
            # Step 4: search with what was parsed — over MCP (unit 4, Milestone 1).
            parsed = session["parsed"]
            arguments = {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            }
            try:
                session["search_results"] = call_tool("search_listings", arguments)
            except MCPError as exc:
                session["error"] = (
                    "Search is unavailable right now — the listings server couldn't "
                    "be reached. Try again in a moment."
                )
                trace.step("search_listings (via MCP)", inputs=_args_text(arguments),
                           returned=str(exc), note="MCP call failed, stopping")
                next_step = "done"
                continue

            # THE BRANCH: nothing found → say what to change and stop, before
            # suggest_outfit. Otherwise take the first result (step 5).
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                trace.step("search_listings (via MCP)", inputs=_args_text(arguments),
                           returned=session["search_results"],
                           note="branch: empty, stopping before suggest_outfit")
                next_step = "done"
            else:
                session["selected_item"] = session["search_results"][0]
                trace.step("search_listings (via MCP)", inputs=_args_text(arguments),
                           returned=session["search_results"],
                           note=f"branch: results, selected id {session['selected_item']['id']}")
                next_step = "suggest"

        elif next_step == "suggest":
            # Step 6: outfit from the item the session holds, not a local copy.
            # ModelUnavailable (bad key, no network) ends the run with a message.
            n_items = len((session["wardrobe"] or {}).get("items") or [])
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
            except ModelUnavailable as exc:
                session["error"] = _model_unavailable_message(exc)
                trace.step("suggest_outfit", inputs=session["selected_item"],
                           returned="ModelUnavailable", note="model unreachable, stopping")
                next_step = "done"
                continue
            trace.step("suggest_outfit", inputs=session["selected_item"],
                       returned=session["outfit_suggestion"],
                       note=f"wardrobe has {n_items} items"
                       + (" — general styling advice" if not n_items else ""))
            next_step = "card"

        elif next_step == "card":
            # Step 7: fit card from the session's outfit and item.
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
            except ModelUnavailable as exc:
                session["error"] = _model_unavailable_message(exc)
                trace.step("create_fit_card", inputs=session["selected_item"],
                           returned="ModelUnavailable", note="model unreachable, stopping")
                next_step = "done"
                continue
            trace.step("create_fit_card", inputs=session["selected_item"],
                       returned=session["fit_card"])
            next_step = "done"

    # Step 8.
    return session


def _args_text(args: dict) -> str:
    """Tool arguments as one readable trace line: description='tee', size=None, ..."""
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def _model_unavailable_message(exc: Exception) -> str:
    """What the user sees when the model can't be reached — no stack trace."""
    first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    return (
        "Found a match, but the styling model couldn't be reached, so there's no "
        "outfit or fit card this time. Check GEMINI_API_KEY in .env and your "
        "connection, then try again."
        + (f" (Details: {first_line})" if first_line else "")
    )


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(r"(?:under|below|less than|max|up to|<)\s*\$?\s*(\d+(?:\.\d+)?)|\$(\d+(?:\.\d+)?)", re.I)
_SIZE = re.compile(r"\b(?:in\s+)?size\s+((?:US\s*)?[A-Z]*\d+(?:\.\d+)?|[A-Z]{1,4})\b", re.I)
_FILLER = re.compile(r"^(?:i'?m\s+)?(?:(?:looking for|i want|i need|find me|show me)\s+)?(?:an?\s+|some\s+)?", re.I)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of a plain-language query,
    with regular expressions. No model call.

        "vintage graphic tee under $30, size M"
          → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    size and max_price are None when the query doesn't give one.
    """
    text = query.strip()

    max_price = None
    price = _PRICE.search(text)
    if price:
        max_price = float(price.group(1) or price.group(2))
        text = text[: price.start()] + text[price.end():]

    size = None
    size_match = _SIZE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[: size_match.start()] + text[size_match.end():]

    text = _FILLER.sub("", text.strip())
    description = re.sub(r"[\s,]+", " ", text).strip(" ,.")
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """
    Say which part of the query to change, not just that nothing matched.

    Re-runs the search with one filter dropped at a time — no model calls —
    so the message can say, e.g., that the price ceiling is what's in the way.
    """
    desc, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]
    asked = f"'{desc}'" + (f" in size {size}" if size else "") + (
        f" under ${max_price:g}" if max_price is not None else ""
    )
    hints = []

    if max_price is not None:
        without_price = search_listings(desc, size=size)
        if without_price:
            best = without_price[0]
            hints.append(
                f"raise your price limit — the closest match, {best['title']}, "
                f"is ${best['price']:g}"
            )
    if size:
        without_size = search_listings(desc, max_price=max_price)
        if without_size:
            hints.append(f"drop the size {size} filter — {len(without_size)} match in other sizes")
    if not hints:
        hints.append(
            "try different words for the item (e.g. 'jacket', 'tee', 'jeans', "
            "'sneakers') — nothing in the listings matches that description"
        )

    return f"Nothing matched {asked}. To find something: " + "; or ".join(hints) + "."


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
