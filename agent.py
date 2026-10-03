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

def _parse_query(query: str) -> dict:
    """Extract a description and optional size and price ceiling from a query."""
    parsed_query = query
    max_price = None
    price_match = re.search(
        r"\b(?:under|below|less than|at most|up to|max(?:imum)?)\s*"
        r"\$?\s*(\d+(?:\.\d{1,2})?)\b",
        parsed_query,
        re.IGNORECASE,
    )
    if price_match:
        max_price = float(price_match.group(1))
        parsed_query = parsed_query[:price_match.start()] + parsed_query[price_match.end():]

    size = None
    size_match = re.search(
        r"\b(?:size|sz)\s+"
        r"(extra\s+small|extra\s+large|one\s+size|medium|small|large|"
        r"xxs|xxl|xs|xl|s|m|l|w\d+(?:\s*l\d+)?|us\s*\d+|\d{1,2})\b",
        parsed_query,
        re.IGNORECASE,
    )
    if size_match:
        size = re.sub(r"\s+", " ", size_match.group(1)).strip()
        parsed_query = parsed_query[:size_match.start()] + parsed_query[size_match.end():]

    description = re.sub(r"\s+", " ", parsed_query).strip(" ,.!?;:-")
    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


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

    The query is parsed with regular expressions. The loop searches first,
    stops if there are no matches, then suggests an outfit and writes a fit
    card. Every tool result is stored in the session.
    """
    session = new_session(query, wardrobe)
    session["parsed"] = _parse_query(query)

    try:
        for iteration in range(1, config.MAX_ITERATIONS + 1):
            trace.check_iterations(iteration)

            if iteration == 1:
                parsed = session["parsed"]
                results = search_listings(
                    parsed["description"],
                    size=parsed["size"],
                    max_price=parsed["max_price"],
                )
                session["search_results"] = results
                if not results:
                    constraints = []
                    if parsed["size"]:
                        constraints.append(f"size {parsed['size']}")
                    if parsed["max_price"] is not None:
                        constraints.append(f"under ${parsed['max_price']:g}")
                    constraint_text = (
                        f" with {' and '.join(constraints)}" if constraints else ""
                    )
                    session["error"] = (
                        f"No listings matched {parsed['description']!r}{constraint_text}. "
                        "Try changing the item description or removing a size or price limit."
                    )
                    trace.step(
                        "search_listings",
                        inputs=parsed,
                        returned=results,
                        note="empty result; stopping before outfit suggestion",
                    )
                    return session

                session["selected_item"] = results[0]
                trace.step(
                    "search_listings",
                    inputs=parsed,
                    returned=results,
                    note="selected the first ranked result",
                )

            elif iteration == 2:
                item = session["selected_item"]
                session["outfit_suggestion"] = suggest_outfit(
                    item,
                    session["wardrobe"],
                )
                trace.step(
                    "suggest_outfit",
                    inputs={"item": item, "wardrobe": session["wardrobe"]},
                    returned=session["outfit_suggestion"],
                )

            elif iteration == 3:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"],
                    session["selected_item"],
                )
                trace.step(
                    "create_fit_card",
                    inputs={
                        "outfit": session["outfit_suggestion"],
                        "item": session["selected_item"],
                    },
                    returned=session["fit_card"],
                )
                return session

    except ModelUnavailable as exc:
        session["error"] = str(exc)
        trace.step(
            "ModelUnavailable",
            returned=session["error"],
            note="stopping with the model adapter's actionable error",
        )
        return session

    raise RuntimeError(
        f"The planning loop did not finish within {config.MAX_ITERATIONS} iterations."
    )


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
