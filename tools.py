"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

Searches use the local listings data. Outfit suggestions and fit cards use
the model adapter in `generate.py`.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


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

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    stop_words = {
        "a", "an", "and", "for", "i", "in", "it", "looking", "me",
        "of", "on", "or", "please", "the", "to", "want", "with",
    }
    query_terms = {
        term
        for term in re.findall(r"[a-z0-9]+", description.casefold())
        if term not in stop_words
    }
    if not query_terms:
        return []

    def normalize_size(value: str) -> str:
        value = re.sub(r"\s+", " ", value.strip().casefold())
        return {
            "extra small": "xs",
            "small": "s",
            "medium": "m",
            "large": "l",
            "extra large": "xl",
            "one size": "one size",
        }.get(value, value)

    requested_size = normalize_size(size) if size else None
    ranked: list[tuple[int, int, dict]] = []

    for index, listing in enumerate(load_listings()):
        price = listing.get("price")
        if max_price is not None and (price is None or price > max_price):
            continue

        if requested_size is not None:
            listing_size = str(listing.get("size", "")).casefold()
            available_sizes = {
                normalize_size(part)
                for part in re.findall(
                    r"xxs|xxl|xs|xl|(?<![a-z0-9])[sml](?![a-z0-9])|"
                    r"w\d+(?:\s*l\d+)?|us\s*\d+|\d+",
                    listing_size,
                )
            }
            if "one size" in listing_size:
                available_sizes.add("one size")
            if requested_size not in available_sizes:
                continue

        searchable = " ".join(
            [
                str(listing.get("title", "")),
                str(listing.get("description", "")),
                str(listing.get("category", "")),
                " ".join(listing.get("style_tags") or []),
                " ".join(listing.get("colors") or []),
                str(listing.get("brand") or ""),
            ]
        ).casefold()
        listing_terms = set(re.findall(r"[a-z0-9]+", searchable))
        score = len(query_terms & listing_terms)
        if score:
            ranked.append((score, index, listing))

    ranked.sort(key=lambda result: (-result[0], result[1]))
    return [
        listing
        for _, _, listing in ranked[: config.SEARCH_RESULT_LIMIT]
    ]


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

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_details = (
        f"Item: {new_item.get('title', 'Unknown item')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Size: {new_item.get('size', 'unknown')}\n"
        f"Colors: {', '.join(new_item.get('colors') or []) or 'unspecified'}"
    )
    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = (
            f"{item_details}\n\n"
            "Suggest one or two practical outfits that style this thrifted item. "
            "The user's wardrobe is empty, so give general ideas and do not "
            "claim they own any other pieces. Keep the advice concise."
        )
    else:
        owned_items = "\n".join(
            f"- {item.get('name', 'Unnamed item')} "
            f"(category: {item.get('category', 'unknown')}; "
            f"colors: {', '.join(item.get('colors') or []) or 'unspecified'}; "
            f"style: {', '.join(item.get('style_tags') or []) or 'unspecified'})"
            for item in wardrobe_items
        )
        prompt = (
            f"{item_details}\n\n"
            f"Items the user owns:\n{owned_items}\n\n"
            "Suggest one or two wearable outfits combining the thrifted item "
            "with specific pieces from the user's wardrobe. Name the pieces "
            "you use, and do not invent items they own."
        )

    response = generate(
        prompt,
        system=(
            "You are a thoughtful personal stylist. Give concise, specific "
            "advice grounded only in the item and wardrobe details provided."
        ),
    ).strip()
    if not response:
        raise RuntimeError("The model returned an empty outfit suggestion.")
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

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit.strip():
        return (
            "No outfit suggestion is available yet. Try pairing this item with "
            "pieces from your wardrobe to build a fit."
        )

    prompt = (
        f"Item: {new_item.get('title', 'Unknown item')}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Outfit idea: {outfit}\n\n"
        "Write a short, natural social-media fit caption in two to four "
        "sentences. Mention the item, its price, and its platform exactly "
        "once each. Make the vibe specific to this item and outfit; avoid "
        "sounding like a product listing."
    )
    response = generate(
        prompt,
        system=(
            "Write authentic, concise fashion captions. Follow the sentence "
            "count and required details exactly."
        ),
    ).strip()
    if not response:
        raise RuntimeError("The model returned an empty fit card.")
    return response
