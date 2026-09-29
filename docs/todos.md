# TODOs

## Active
(none blocking; see backlog for deferred ideas)

## Backlog / future ideas
- [ ] "Leveled Class I" method: slide only the base row of a Class I dome
      to a plane (fewer new strut types than extended Kruschke).
- [ ] Hub connector visualization (spheres or plates at hubs).
- [ ] Cut-list CSV variant (one row per physical strut).
- [ ] Automated Blender-side tests (`blender --background --python`) as a
      real CI step; a manual headless smoke run was done for this build
      (see the session report) but nothing runs it automatically yet.
- [ ] If a scan of Kruschke's Dome Cookbook pages 18-23 turns up, check the
      book's 2V treatment and published tables against our construction.
- [ ] Custom chord table relaxation solver has no explicit symmetry
      enforcement (design.md 7, as specced). For chord tables that deviate
      more than about 1 percent per class from the Class I / Kruschke
      defaults, the solver converges to a "best fit" that is only
      approximately symmetric, so the reported strut table can show many
      more near-duplicate types than the topology's true symmetry class
      count (verified during the T11 smoke test with table "0.36 0.41
      0.42" on 3V k=4: 50 reported types at merge_tolerance 1e-4 instead of
      3). This matches the design's "no symmetry enforcement" note, but a
      future pass could explicitly average each edge class to its
      symmetry-orbit mean every few iterations to keep the report readable
      for larger deviations.
- [ ] Dynamic fraction EnumProperty does not re-validate its stored value
      when the user switches `method` in the redo panel; if the previously
      selected fraction key does not exist in the new method's item list,
      Blender's own enum handling resets it silently. Not observed to
      crash in the headless smoke test, but worth an explicit interactive
      check in Blender's UI (not just via `bpy.ops` calls).

## Design decisions recorded this session (see docs/design.md for detail)
- 5V/6V extended Kruschke: stays in the pure core with tests, hidden from
  every Blender UI path (design.md 14, item 1).
- Kruschke (Domerama) and Kruschke (Traditional) merged into one `KRUSCHKE`
  method; domerama's published values now show as a report column instead
  of a second menu entry (design.md 2 and 5.3).
- Defaults confirmed: method Kruschke, frequency 3V, fraction 5/9, radius
  3 m (design.md 14, item 2).
