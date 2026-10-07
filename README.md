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

- **What it does:** Finds listings whose title, description, category, tags, colors, or brand overlap the requested keywords, optionally filtering by an exact size token and inclusive maximum price; results are ranked by keyword overlap.
- **Inputs:** `description` (`str`); `size` (`str | None`, optional); `max_price` (`float | None`, optional).
- **Returns:** Up to `SEARCH_RESULT_LIMIT` listing dictionaries, each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`, ordered best match first.
- **When it has nothing:** Returns an empty list if no listing passes the filters and has at least one matching keyword.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two outfits for a selected listing, grounding suggestions in pieces the user owns when available.
- **Inputs:** `new_item` (`dict`, a listing); `wardrobe` (`dict`, with an `items` list of wardrobe-item dictionaries).
- **Returns:** A non-empty model-generated outfit suggestion (`str`); with an empty wardrobe, gives general styling ideas without claiming the user owns other pieces.
- **When it has nothing:** Raises `RuntimeError` if the model returns empty text; a model outage raises `ModelUnavailable`.

### `create_fit_card`

- **What it does:** Creates a short social-media caption based on an outfit suggestion and listing, naming the item, price, and platform.
- **Inputs:** `outfit` (`str`); `new_item` (`dict`, a listing).
- **Returns:** A model-generated caption of two to four sentences, mentioning the item, price, and platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a descriptive fallback string without calling the model; empty model text raises `RuntimeError`, and model outages raise `ModelUnavailable`.

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

**Branch rule:** If `search_listings` returns an empty list, store an error message suggesting that the user change the description or remove a size or price limit, then stop before calling `suggest_outfit`. Otherwise, save the first ranked result as `selected_item`, pass it and the wardrobe to `suggest_outfit`, then pass the outfit suggestion and selected item to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract a description, an optional size, and an optional maximum price.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → first result in `selected_item` → `outfit_suggestion` → `fit_card`. If there are no search results or the model is unavailable, `error` is set and the loop stops.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; results = search_listings('graphic tee', max_price=30); print([(item['id'], item['title'], item['price'], item['size']) for item in results])"
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0, 'S/M'), ('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0, 'L'), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0, 'S/M'), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0, 'L'), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0, 'W29'), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0, 'L')]

```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
* Vintage Levi's 501 Jeans (Medium Wash)
* Black cropped zip hoodie
* Chunky white sneakers
* Black crossbody bag

**Outfit 2: Classic Minimal**
* Vintage Levi's 501 Jeans (Medium Wash)
* White ribbed tank top
* Brown leather belt
* Black combat boots
* Vintage black denim jacket

```

Run this command three times with caching disabled (one temporary model 503 was
retried before these three successful responses):

```
$ python -c "import config; config.CACHE_ENABLED = False; from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('Baggy jeans, white tee, sneakers', load_listings()[0]))"
Try 1: Channel off-duty model energy with these vintage Levi's 501 jeans styled with a crisp white tee and your favorite sneakers. These classic denim staples feature a worn-in medium wash and are available on Depop for just $38. Grab them for your capsule wardrobe before someone else does!

Try 2: Nothing beats a classic white tee and these worn-in vintage Levi's 501 jeans for an effortless off-duty look. Styled with fresh sneakers, the light knee fading gives them that perfectly lived-in feel right out of the box. Grab this medium wash staple for just $38.0 on depop before someone else does.

Try 3: Throw on a crisp white tee and your favorite sneakers with these broken-in vintage Levi's 501 jeans for the ultimate effortless weekend uniform. The dreamy medium wash and authentic knee fading give them that hard-to-find lived-in look right out of the box. Grab this timeless pair on Depop right now for just $38.

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

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
