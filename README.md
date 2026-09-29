# Geodesic Dome Builder

A Blender extension that generates geodesic dome frames with the chord
factors you need to actually cut struts. I make art installations for
events under [Geovisual Creations](https://geovisual.net), and a lot of that work is built on
geodesic domes. One of my main installations is a projection dome. I wrote
this for my own build planning and figured other dome builders could use it.

Requires Blender 4.2 or newer (tested in Blender 5.2). Current version
0.1.3. License: GPL-3.0-or-later.

## Install

1. Download `geodesic_dome_builder-0.1.3.zip` from the
   [Releases](https://github.com/balgarath/geodesic-dome-blender/releases)
   page.
2. In Blender, go to Edit > Preferences > Get Extensions, open the
   dropdown menu at the top right, choose Install from Disk, and pick the
   zip.

## Use

Add > Mesh > Geodesic Dome. The redo panel sets method, frequency,
truncation fraction and radius. Defaults are Kruschke, 3V, 5/9, radius
3 m, because that's what I usually build.

### Methods

- **Kruschke** (3V and 4V). Gives a level base at odd truncations, which
  plain Class I can't do. Chord factors match domerama.com's Kruschke
  calculators (3V 4/9 and 5/9, 4V 5/12 and 7/12).
- **Icosahedron Class I Method 1** (1V to 8V). The standard subdivision.
- **Custom chord table**. Type in your own chord factors and the tool
  relaxes a mesh to fit them. If the table can't form a consistent dome
  it warns you and reports the error in mm at your chosen radius.

### Truncation

Fractions are per frequency. 4/9 is what domerama calls "3/8", and 5/9 is
their "5/8". When a Class I odd-frequency base isn't level, the tool says
so plainly instead of letting you find out at the build site.

## What you get

- A mesh with a per-edge strut type attribute and color, plus an optional
  strut visualization object. Struts are colored shortest to longest in the
  order I paint them: red, blue, green, yellow, purple, black. Domes with
  more than six strut types get generated colors after that.
- An N-panel report listing chord factor, length at your radius, count
  per strut type, and hub counts by valence. When the dome matches a
  published domerama variant, the report adds a Domerama column with
  their published values next to ours.
- CSV export.

## The Kruschke construction

Start from a Class I dome, then slide the five points around each
pentagon hub along the icosahedron edge, by a ratio chosen so the base
rows land level. True Kruschke leveling only works at 3V and 4V, so 5V
and 6V aren't offered.

## Verification

The geometry core is pure Python with no Blender imports, tested with
pytest against domerama's published numbers: Class I 1V to 8V and all
four Kruschke variants, matching counts and chord factors. A separate
verification script checks the math independently.

The tests turned up a couple of issues in domerama's own tables, now
documented here: their 4V 5/12 Kruschke page lists 85 six-way hubs where
the correct number is 45, and their 7V and 8V tables each merge two strut
types that differ by a few hundred-thousandths.

## Known limits

- No automated in-Blender tests yet. The core math is tested; the Blender
  layer is checked by hand.
- Switching method in the redo panel hasn't been exercised through the
  interactive UI yet.
- A custom table on a small dome gives a general error warning rather
  than a per-length count.

## Developer notes

```
python -m pytest tests -q               # run the test suite
python reference/verify_geometry.py     # independent math check
python build.py                         # build the extension zip
```

## Credits

Chord factor references and prior art: domerama.com, David Kruschke
(Dome Cookbook of Geodesic Geometry, 1972), acidome.com, and the
geodesichelp group (Gerry Toomey). Details in [CREDITS.md](CREDITS.md).
