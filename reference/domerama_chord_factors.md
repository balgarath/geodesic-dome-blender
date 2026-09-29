# Domerama.com geodesic dome chord factors

Retrieved 2026-09-28. Structured data (machine-readable) is in `domerama_chord_factors.json` in this
same folder. This file is the human-readable companion, plus context and caveats. **Never round or
"fill in" a number that wasn't shown on the site** — this file only reports what domerama.com actually
displays. Where a value is missing, it says so.

Primary sources fetched:
- Calculator index: https://www.domerama.com/calculators/
- Master chord-factor table (1V-8V, "method 1"): https://www.domerama.com/calculators/chord-charts/
- Individual calculator pages for 1V, 2V, 3V (3/8, 5/8), 4V (1/2, plus Kruschke 5/12 and 7/12), 5V (7/15, 8/15), 6V
- 3V Kruschke pages (4/9 and 5/9)
- Octahedral 5V "Mexican method" page
- "Leveling the base of a dome" (explains Kruschke) and "Making a 3v timber Kruschke dome" (explains timber-specific detail)

## Important note on how chord factors were matched to strut counts

The **chord-charts page** is the only page on the site that publishes full-precision decimal chord
factors. It gives one table per frequency (1V-8V), each row showing a strut letter, its count, its
chord factor, and its bend angle — but only for ONE truncation per frequency (the "base" case: 2/3 for
1V, 1/2 for 2V, 3/8 for 3V, 1/2 for 4V, 7/15(3/8) for 5V, 1/2 for 6V, 10/21 for 7V, and an unlabeled
truncation for 8V).

The **individual calculator pages** (one per frequency, sometimes per truncation) give strut counts and
bend angles for a specific named truncation (e.g. 3V 5/8, 5V 8/15), but do **not** show the chord factor
decimal anywhere in the rendered page or in the page's JavaScript/HTML source (checked directly).

Where a calculator page's strut letters, counts, and angles matched the chord-charts table exactly
(3V 3/8, 5V 7/15, 6V 1/2), the correspondence is unambiguous. Where a variant has the *same* strut
letters/angles as the base case but larger counts (3V 5/8, 5V 8/15), the same chord factors apply —
confirmed by exact angle equality, not by a separately published table. This is noted per-entry below.

**4V is the one place this breaks down**: the chord-charts page and the 4V calculator page disagree on
angles for two of the six strut types, and the chord-charts page has two different chord factors sharing
the same angle (9.35°) while the calculator page lists only one strut type at that angle. This is flagged
in the JSON and below rather than force-matched.

## Dome variants captured

### Class I Method 1 (standard icosahedron subdivision)

| Dome | Fraction | Struts (label: count @ angle = CF) | Total struts | Hubs |
|---|---|---|---|---|
| 1V (a.k.a. 2/3) | 2/3 | A: 25 @ 31.72° = 1.05146 | 25 | 6×5-way, 5×4-way |
| 2V | 1/2 | A: 35 @ 18° = 0.61803; B: 30 @ 15.86° = 0.54653 | 65 | 10×6-way, 6×5-way, 10×4-way |
| 3V | 3/8 | A: 30 @ 10.04° = 0.34862; B: 40 @ 11.64° = 0.40355; C: 50 @ 11.90° = 0.41241 | 120 | 25×6-way, 6×5-way, 15×4-way |
| 3V | 5/8 | A: 30 @ 10.04° = 0.34862; B: 55 @ 11.64° = 0.40355; C: 80 @ 11.90° = 0.41241 | 165 | 40×6-way, 6×5-way, 15×4-way |
| 4V | 1/2 | See "4V ambiguity" note below — chord factors and counts could not be safely paired | 250 (counts only) | 65×6-way, 6×5-way, 20×4-way |
| 5V | 7/15 (3/8) | A:30@5.69°=0.19814743; B:30@6.48°=0.23179025; C:60@6.65°=0.22568578; D:60@6.66°=0.24724291; E:50@7.04°=0.25516701; F:50@7.05°=0.24508578; G:30@7.10°=0.26159810; H:30@7.33°=0.23159760; I:10@7.52°=0.24534642 | 350 | 95×6-way, 6×5-way, 25×4-way |
| 5V | 8/15 (5/8) | Same 9 letters/angles/CFs as 7/15 above, counts: A30,B30,C60,D70,E70,F80,G35,H30,I20 | 425 | 120×6-way, 6×5-way, 25×4-way |
| 6V | 1/2 | A:30@4.66°=0.16256722; B:30@5.22°=0.19047686; C:60@5.38°=0.18190825; D:90@5.47°=0.20281969; E:30@5.68°=0.1873834; F:60@5.82°=0.19801258; G:130@5.91°=0.20590774; H:65@6.18°=0.21535373; I:60@6.22°=0.21662821 | 555 | 160×6-way, 6×5-way, 30×4-way |
| 7V | 10/21 | 15 strut types (A-O), CF 0.13774 to 0.1879 — see JSON for full table | not stated (angles+CF only; no dedicated calculator page) | not published |
| 8V | not stated by site | 19 strut types (A-S), CF 0.11946 to 0.16465 — see JSON for full table | not stated | not published |

Full-precision chord factors (as many digits as domerama shows, no rounding) are in the JSON file.

### 4V ambiguity (read before using 4V data)

The chord-charts page's "4V 1/2 method 1" table:

| Label | CF | Angle |
|---|---|---|
| A | 0.25318 | 7.27° |
| B | 0.29524 | 8.47° |
| C | 0.29453 | 9.35° |
| D | 0.31287 | 9° |
| E | 0.32492 | 8.59° |
| F | 0.29859 | 9.35° |

The 4V calculator page's own strut table (https://www.domerama.com/calculators/4v-geodesic-dome-calculator/):

| Label | Count | Angle |
|---|---|---|
| A | 30 | 7.27° |
| B | 30 | 8.49° |
| C | 60 | 8.47° |
| D | 70 | 9.35° |
| E | 30 | 8.59° |
| F | 30 | 9.00° |

Only two rows line up cleanly by angle (7.27° and 8.59°). The chord-charts table has **two different
chord factors at the same 9.35° angle** (C and F), while the calculator page has only **one** strut type
at 9.35° (D, count 70) — there is no way to tell from the site which of the two chord factors (0.29453 or
0.29859) belongs to that 70-count strut without more information. The calculator page's B (8.49°) also
doesn't match the chord-chart's B (8.47°) — possibly a typo on one of the two pages. We recorded both
tables separately in the JSON (as two "4V 1/2" entries) rather than guessing a pairing. **Recommend
re-deriving the 4V chord factors geometrically for the Blender plugin's pass/fail set instead of trusting
this site's 4V count-to-CF pairing.**

### Kruschke method domes

No chord factor decimals are published anywhere on the site for any Kruschke dome — checked the
rendered page text and the raw page source/JavaScript for hidden numeric constants on all four Kruschke
calculator pages; none were found. Only bend angles and strut counts are shown. If exact chord factors
are needed for these as pass/fail test data, they will need to be computed independently (geometrically)
or sourced from Kruschke's original 1972 published tables (not available on domerama.com).

| Dome | Site fraction | Common alias | Struts (label: count @ angle) | Total | Hubs |
|---|---|---|---|---|---|
| 3V Kruschke | 4/9 | "3/8" | A:30@9.49°; B:30@11.02°; C:50@12.16°; D:10@12.74° | 120 | 25×6-way, 6×5-way, 15×4-way |
| 3V Kruschke | 5/9 | "5/8" | A:30@9.49°; B:35@11.02°; C:80@12.16°; D:20@12.74° | 165 | 40×6-way, 6×5-way (4-way count not captured — see Missing below) |
| 4V Kruschke | 5/12 | — | A:30@6.38°; B:30@7.46°; C:50@8.89°; D:40@9°; E:20@9.35°; F:20@9.48° | 190 | 85×6-way, 6×5-way, 20×4-way |
| 4V Kruschke | 7/12 | — | A:30@6.38°; B:35@7.46°; C:80@8.89°; D:80@9°; E:45@9.35°; F:40@9.48° | 310 | 85×6-way, 6×5-way, 20×4-way |

Note: the two 4V Kruschke pages list identical bolt/nut/washer counts (111/111/222) despite different
total strut counts (190 vs 310) — recorded exactly as shown on site, not corrected, and flagged as a
likely site data-entry duplication.

**No 5V, 6V, 7V, or 8V Kruschke calculator was found on domerama.com.** Only 3V and 4V have published
Kruschke variants.

### Other method: Octahedral 5V, "Mexican method" (NOT Kruschke)

URL: https://www.domerama.com/calculators/octahedral-5v-mexican-method/

Base polyhedron: **octahedron** (not icosahedron). Fraction: 1/2. This is a distinct alternate
triangle-subdivision method, unrelated to Kruschke, attributed on the site to Mexican mathematician
Hector Alfredo Hernandez Hernandez.

| Label | Count | Angle |
|---|---|---|
| A | 12 | 12.6° |
| B | 24 | 12.4° |
| C | 36 | 11.7° |
| D | 48 | 10.6° |
| E | 40 | 9.0° |

Total: 160 struts. Hubs: 40×6-way, 17×4-way, 4×3-way. No chord factor decimals published.

Site's own description: *"With this system of triangle subdivision, strut lengths are equalized along
each set of three paths followed by the struts. As a result, the number of unique strut lengths equals
the dome's frequency. The method can be applied to geodesic domes based on either the octahedron or
icosahedron, but the equal-length feature begins to break down at frequency 6."*

## What the site says about how Kruschke differs from standard subdivision

From https://www.domerama.com/dome-basics/odd-frequency-geodesic-domes-and-flat-base-at-the-hemisphere/
("Leveling the base of a dome"):

- The geometry normally used for geodesic domes is called **"method 1"** on the site. It gives a flat
  base only when the dome is an exact hemisphere, which requires an **even** frequency (2V, 4V, 6V...).
- For **odd** frequencies (3V, 5V...), method 1 does not produce a flat base at any truncation — "not
  all nodes (where struts meet) lie in the same plane."
- A typical dome is a 1/2 truncation (exact hemisphere). Other truncations include 4/9, 5/9, 3/8, 5/8,
  etc., "but not all truncations are flat at the base."
- Example given: a 3V icosahedron sphere does not split into identical hemispheres. You can set the
  base a little above the equator for a low-profile "4/9" dome (4 rows of triangles) or a little below
  for a high-profile "5/9" dome (5 rows). **"Many dome builders refer to 4/9 and 5/9 domes as '3/8' and
  '5/8' — terminology that dates back to the early days of geodesic dome design."** This is why the
  site's own 3V Kruschke calculator URLs use "38" and the page title says "4/9" — same dome, two names.
- Site lists five ways people historically dealt with the uneven-base problem: shimming the base,
  shaping the foundation to match the uneven perimeter, altering strut lengths in the bottom row,
  reducing the footprint from 15 edges to 10 (replacing triangle clusters with 5 trapezoids), or **using
  an entirely different geometry with a flat base built in from the outset — this last option is the
  Kruschke method.**
- **The Kruschke method (aka "Kruschke calculator" on the site) gives a flat/level base for both
  low-profile and high-profile versions of an odd-frequency dome**, regardless of truncation. The
  underlying geometry was reportedly used by Buckminster Fuller in early dome building, but the math
  wasn't published until 1972, by David Kruschke, an American teacher.
- **"So when you see Kruschke, think flat or level base, whatever the truncation."**

From https://www.domerama.com/calculators/3v-geodesic-dome-calculator/making-a-timber-kruschke-dome/
("Making a 3v timber Kruschke dome"):

- **A Kruschke-method dome requires one extra strut length compared to the standard method** to achieve
  its flat base — the site states this directly: *"A geodesic dome that utilizes the Kruschke method
  (main reason is to have a flat base) will require 4 different strut lengths."* (Standard 3V Class I
  Method 1 only needs 3.) This matches what we found: the 3V Kruschke pages have strut types A-D (4
  types), while the standard 3V pages have A-C (3 types).
- For **hub-based (conduit) construction**, this is the whole story — one cut/bend angle per strut end.
- For **timber/lumber construction**, it's more complex: the "C" strut is actually "the same length,
  different angles" at its two ends, referred to as C1 and C2, requiring different cut angles even
  though the strut length itself doesn't change. This only matters if you're not using a hub system —
  hub systems only need the axial/bend angle.
- Even with the Kruschke method, a **timber** dome's base is only flat at the hub/node points, not truly
  flat along the surface of the base struts themselves — there's a slight tilt to the base struts when
  built from lumber, described on the site as: *"it's not technically flat on the surface of the strut:
  there is a tilt of the base struts."*

## Other sources (NOT domerama.com — for context only, not part of the pass/fail set)

- **simplydifferently.org** — Referenced directly by the domerama.com chord-charts page itself: *"If
  you are looking for an advanced explanation of chord factors, bend angles and varying truncations,
  simplydifferently.org has an extensive and impressive information site on geodesic domes and other
  structures."* We did not fetch this site (out of scope — task is domerama.com only), but it's worth
  noting for later since it's the site domerama itself points to for deeper chord-factor theory.

## Missing / could not verify

1. **No 5V, 6V, 7V, or 8V Kruschke calculator exists on domerama.com.** Only 3V (4/9, 5/9) and 4V
   (5/12, 7/12) Kruschke variants were found.
2. **No chord factor decimals are published for any Kruschke dome** — checked rendered text and raw
   page source/JS on all four Kruschke pages; none found. Angle + count only.
3. **No dedicated 7V or 8V calculator pages exist** — those two frequencies appear only as rows on the
   chord-charts summary page (full chord factor + angle + count there, but no separate page for
   alternate truncations, no hub connector counts, and 8V's truncation fraction isn't stated at all).
4. **4V 1/2 chord-factor-to-count pairing is ambiguous** between the chord-charts page and the 4V
   calculator page (see "4V ambiguity" section above) — recorded both tables separately rather than
   guessing a merge.
5. **3V 5/9 Kruschke page's 4-way hub connector count** was not captured in our fetch (6-way and 5-way
   were visible before the page content we extracted ended) — recommend re-checking
   https://www.domerama.com/calculators/3v-geodesic-dome-calculator/3v-flat-base-815-kruschke-calculator/
   directly if that number is needed.
6. **Face/panel counts** are only given as loose prose on the chord-charts page (e.g. "105 faces",
   "15 3-sided faces") and in a couple of cases the text extraction from HTML came out garbled/ambiguous
   (the 3V and 5V rows mix truncation-fraction labels with face counts in a way that's hard to parse
   with certainty) — we did not force an interpretation; raw counts are noted per-entry in the JSON
   where legible, and treated as informational only, not structural (strut counts are the reliable
   source of truth for geometry).
