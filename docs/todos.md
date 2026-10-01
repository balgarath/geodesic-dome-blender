# TODOs

## Active
(none blocking; see backlog for deferred ideas)

## Backlog / future ideas
- [ ] "Leveled Class I" method: slide only the base row of a Class I dome
      to a plane (fewer new strut types than extended Kruschke).
- [ ] Hub connector visualization (spheres or plates at hubs).
- [ ] Cut-list CSV variant (one row per physical strut).
- [ ] Automated Blender-side tests (`blender --background --python`) as a
      real CI step; manual headless smoke runs were done for this build on
      both Blender 4.0.1 and 5.2.0 (see the v0.1.1 session report) but
      nothing runs it automatically yet.
- [ ] If a scan of Kruschke's Dome Cookbook pages 18-23 turns up, check the
      book's 2V treatment and published tables against our construction.
- [ ] Custom chord table relaxation solver has no explicit symmetry
      enforcement (design.md 7, as specced). For chord tables that deviate
      more than about 1 percent per class from the Class I / Kruschke
      defaults, the solver converges to a "best fit" that is only
      approximately symmetric, so the reported strut table can show many
      more near-duplicate types than the topology's true symmetry class
      count (verified with table "0.36 0.41 0.42" on 3V k=4: 119 reported
      types instead of 3, at the v0.1.1 production default merge tolerance
      1e-6). v0.1.1 added an explicit warning for this case ("Your table is
      not geometrically consistent for this dome..."), but the underlying
      solver still has no symmetry enforcement; a future pass could
      explicitly average each edge class to its symmetry-orbit mean every
      few iterations to keep the report readable for larger deviations.
- [ ] Dynamic fraction EnumProperty does not re-validate its stored value
      when the user switches `method` in the redo panel; if the previously
      selected fraction key does not exist in the new method's item list,
      Blender's own enum handling resets it silently. Not observed to
      crash in the headless smoke test, but worth an explicit interactive
      check in Blender's UI (not just via `bpy.ops` calls). Ralph's 5.2
      screenshot confirmed fraction labels render correctly; switching
      method mid-redo still unchecked.
