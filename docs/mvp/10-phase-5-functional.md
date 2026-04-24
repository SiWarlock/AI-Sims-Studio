# MVP Spec — Phase 5 — Functional Overlay

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.6

> Archetype configuration, tuning extraction, clone pipeline, functional variant packaging.

---

**Phase goal:** Enable upgrading selected items to functional objects via base-game tuning cloning for the four MVP archetypes.

**Phase acceptance gate:** A user can upgrade at least one item per archetype (lava lamp → light on/off, CD player → audio device, mirror → mirror archetype, decor object → moodlet emitter) and the functional variant works in-game.

#### Tasks

**5.1 — Base-game resource extraction**
Build the module that reads base-game resources from the user's local Sims 4 install. Must extract specific reference objects (meshes, tuning, strings) by ID without modifying the install.

*Outputs:* Read-only extraction module. Given a TGI ID, returns the resource bytes.
*Dependencies:* 0.4, 1.6.
*Acceptance:* Can extract known resources from a standard Sims install. Never writes to the install directory.

**5.2 — Reference object identification (D-4)**
Identify the exact resource IDs for each of the four archetype reference objects. Document in TAD. Build a lookup table mapping archetype to reference object IDs.

*Outputs:* A mapping in the TAD and a corresponding Python constant. Decision D-4 resolved.
*Dependencies:* 5.1.
*Acceptance:* All four archetypes have confirmed reference object IDs that extract correctly.

**5.3 — Tuning XML parser and editor**
Build a tuning XML parser and targeted-edit module. Must parse tuning, identify editable fields relevant to each archetype, and produce modified tuning without breaking references.

*Outputs:* Python module with typed tuning access.
*Dependencies:* 5.1.
*Acceptance:* Can parse reference tuning, modify targeted fields (light color, moodlet reference, etc.), and serialize valid tuning XML.

**5.4 — Archetype handler: light on/off**
Implement the light on/off archetype handler. Given a user item + configured parameters, clone the reference lamp tuning, swap in the user's mesh/textures/strings, apply configured light color and intensity, produce a functional tuning set.

*Outputs:* Handler module that produces tuning ready for packaging.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional lava lamp turns on and off in-game, changes color correctly.

**5.5 — Archetype handler: audio device**
Implement the audio device archetype handler.

*Outputs:* Handler module.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional CD player plays and pauses audio in-game.

**5.6 — Archetype handler: mirror**
Implement the mirror archetype handler.

*Outputs:* Handler module.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional mirror exposes standard mirror interactions in-game.

**5.7 — Archetype handler: moodlet emitter**
Implement the moodlet emitter archetype handler with user-selectable moodlet type, duration, and radius.

*Outputs:* Handler module and curated safe moodlet list.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional emitter applies the configured moodlet to nearby Sims with the configured duration.

**5.8 — Functional upgrade wizard UI**
Build the wizard UI: archetype selection (filtered by template compatibility), per-archetype configuration form, summary preview, confirmation step.

*Outputs:* React wizard component.
*Dependencies:* 5.4 through 5.7, 3.9.
*Acceptance:* User can launch the wizard from the item detail view, select and configure an archetype, and see a summary before committing.

**5.9 — Functional variant packaging**
Extend the DBPF build pipeline to produce functional `.package` variants. Support decor-only, functional, or both-variant exports per item.

*Outputs:* Build function handling both variants.
*Dependencies:* 4.2, 5.4 through 5.7.
*Acceptance:* Functional `.package` files are valid, installable, and behave as expected.

**5.10 — Functional validation extension**
Extend validation to cover functional variant completeness, tuning integrity, and archetype-template compatibility.

*Outputs:* Extended validation rules.
*Dependencies:* 4.1, 5.9.
*Acceptance:* Invalid functional configurations are caught before export.

---
