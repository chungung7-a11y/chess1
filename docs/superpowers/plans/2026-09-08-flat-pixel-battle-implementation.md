# Flat Pixel Battle Chess Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the perspective 3D board and rigid single-pose characters with a responsive flat board, genuine multi-frame pixel characters, and synchronized four-second multi-hit battles.

**Architecture:** Keep the game rules and modes in `chess.html`, but replace the visual layer behind small interfaces: a flat board transform, one shared sprite animator, an input queue, and a battle timeline. Piece art lives in equal-cell sprite sheets described by one manifest; the standalone builder embeds every sheet into `deploy/index.html` for Vercel.

**Tech Stack:** HTML, CSS, vanilla JavaScript, Web Audio API, transparent PNG sprite sheets, Node build script, Vercel static hosting.

**Spec:** `docs/superpowers/specs/2026-09-08-flat-pixel-battle-design.md`

## Global Constraints

- Complete top-down square; no perspective, rotateX, or translateZ camera compensation.
- Preserve training, solo, duo, king-rule toggle, hover, movable glow, minimized menu, flip, undo, and victory fireworks.
- Use the approved original chibi pixel-art direction; do not copy commercial characters, frames, or sounds.
- Capture battles last about 4 seconds; reduced motion shortens them to about 1.5 seconds.
- Ordinary moves accept the next turn's selection by the next render frame; battles accept one queued selection within 50ms.
- Equal sprite cells and one common foot-center anchor; white and black have identical frame layouts.
- Optimized sprite assets total at most 4MB.
- At battle end no corpse, particle, timer, queued input, or stale lock remains.

---

### Task 1: Add browser regression tests for geometry and latency

**Files:**
- Modify: `chess.html` (self-test and query-string test harness)
- Create: `docs/testing/flat-battle-checklist.md`

**Interfaces:**
- Produce `window.__battleTest` with `assert(name, condition, detail)`, `results`, and `report()`.
- Produce `measureInputLatency(action): Promise<number>`.

- [ ] Write failing checks for no perspective, no 3D board matrix, identity camera compensation, and ordinary next-turn input on the next animation frame.
- [ ] Open `chess.html?test` and confirm all four new checks fail on the current implementation.
- [ ] Document manual scenarios: 64 square centers, flip twice, minimize/restore, both-side hover, rapid ordinary move, queued capture selection, queue replace/cancel, undo during animation, AI turn, training answer, all six FX, win/loss/draw.
- [ ] Commit: `git commit -m "test: add flat board and responsiveness checks"`.

### Task 2: Flatten the board without changing rules

**Files:**
- Modify: `chess.html` (root variables, stage, board, frame, sprite/effect transforms, `fit()`, `flipBoard()`)

**Interfaces:**
- Produce `setBoardFacing(flipped: boolean)`.
- Produce screen-aligned `--piece-face` used by pieces, labels, projectiles, and particles.

- [ ] Replace stage/board CSS with a screen-parallel 8×8 square and remove perspective.
- [ ] Replace `--cam` from every sprite, marker, projectile, death, and particle transform with `--piece-face`.
- [ ] Run `Select-String chess.html -Pattern 'perspective|rotateX\(|translateZ\(|var\(--cam\)|--tilt'`; expect no rendering-path matches.
- [ ] Replace nonlinear perspective fitting with direct width/height square calculation.
- [ ] Keep pieces upright when the board flips by counter-rotating them 180 degrees.
- [ ] Verify equal square bounds and no offscreen center at 520×900, 730×582, 1440×900, and 1600×920.
- [ ] Commit: `git commit -m "feat: replace perspective board with flat top-down board"`.

### Task 3: Separate logical turns from visual motion

**Files:**
- Modify: `chess.html` (`click`, `doMove`, `aiTurn`, `glide`, `layout`, `paint`, undo/reset functions)

**Interfaces:**
- Produce `visualBusy: boolean`, `queuedSelection: number|null`.
- Produce `queueSelection(i): boolean`, `flushQueuedSelection()`, and `cancelVisuals()`.

- [ ] Add failing tests for queue accept, replace, second-click cancel, invalid-click preservation, and stale-callback cancellation.
- [ ] Add explicit visual/queue state; a queued piece receives a distinct `.queued` glow and “다음 말 선택됨” message immediately.
- [ ] Make ordinary moves commit board state, turn, and legal moves before visual walking begins; do not set `locked` for walking.
- [ ] During capture animation accept one current-side piece selection; do not permit a destination move or overlapping battle.
- [ ] At battle completion select the queued piece only if it still belongs to the current side and remains selectable.
- [ ] Remove fixed `later(500, aiTurn)`; compute AI after state commit and begin its visual move when both calculation and current battle are complete.
- [ ] Add a visual generation token. Undo, new game, mode change, and resize increment it, clear all timers/effects, and clear the queue.
- [ ] Verify ordinary selection on the next frame, queued feedback under 50ms, exact one-time flush, and no stale callback.
- [ ] Commit: `git commit -m "feat: remove move input lag and queue battle selections"`.

### Task 4: Add the sprite manifest and shared frame player

**Files:**
- Create: `assets/pieces/manifest.js`
- Create: `assets/pieces/README.md`
- Modify: `chess.html`
- Modify: `build-standalone.js`
- Modify: `build-standalone.pl`

**Interfaces:**
- Produce `PIECE_SPRITES` keyed by `wN`, `bN`, and the other side/type pairs.
- Produce `setPieceState(el, state, options?)`, `stopPieceState(el)`, and one `spriteTick(now)`.

- [ ] Define manifest entries with URL, cell size, sheet grid, foot anchor, and states as `[startFrame, frameCount, fps, loop]`.
- [ ] Add failing tests for frame 0, frame boundaries, loop wrapping, non-loop final frame, facing, and fixed foot anchor.
- [ ] Implement one shared `requestAnimationFrame` loop over an active-element Set; never create one timer per character.
- [ ] Replace split body/arm markup with one complete `.pixel-sprite`; limb motion comes from redrawn frames rather than clipped copies.
- [ ] Teach Node and Perl builders to inline `manifest.js` and all manifest images, failing with the missing filename when an asset is absent.
- [ ] Verify the CSS fallback still allows rules/clicking when an image is missing and the active animation Set returns to zero.
- [ ] Commit: `git commit -m "feat: add manifest-driven pixel sprite player"`.

### Task 5: Produce and integrate production knight sheets

**Files:**
- Create: `assets/pieces/white-knight.png`
- Create: `assets/pieces/black-knight.png`
- Modify: `assets/pieces/manifest.js`
- Modify: `chess.html`

**Interfaces:**
- Produce final `wN` and `bN` sheets and the quality baseline for later pieces.

- [ ] Generate the white sheet from the approved concept: original chibi arcade knight, horse-head helmet, silver armor, gold trim, blue cloth, transparent equal cells, common foot anchor, hard pixel edges, and genuinely redrawn limbs/weapon.
- [ ] Include idle 4, walk 6, hit 3, recover 3, cheer 4, anticipation 3, attack-A 6, attack-B 6, finisher 8, and death-entry 5 frames.
- [ ] Validate exact dimensions, cell containment, nonempty frames, foot position within 3px, and no pixel-identical neighboring motion frames.
- [ ] Generate black by preserving every pose/pixel/alpha edge and changing only the palette to black iron, red-copper trim, and crimson cloth; verify matching alpha masks.
- [ ] Connect idle, walking, selection, hover, hit, and victory states; remove static-picture bobbing.
- [ ] Implement crouch, jump, two small slams with 60ms hit stops, high jump, final 90ms slam, squash death, recover, and cheer.
- [ ] Verify both sides, normal/reduced motion, both board directions, duration 3.7–4.3s, and responsive queued input.
- [ ] Commit: `git commit -m "feat: add animated pixel knight and multi-slam battle"`.

### Task 6: Produce rook and bishop sheets and battles

**Files:**
- Create: `assets/pieces/white-rook.png`, `black-rook.png`
- Create: `assets/pieces/white-bishop.png`, `black-bishop.png`
- Modify: `assets/pieces/manifest.js`
- Modify: `chess.html`

- [ ] Generate rook sheets with castle helmet, arm cannon, loading, two light recoil cycles, main recoil, hit, shatter entry, and cheer; validate geometry and white/black alpha equality.
- [ ] Synchronize loading metal, two light shots, main shot, 90ms hit stop, eight sprite-derived wedges, and metal debris. Full sprite disappears exactly when wedges appear.
- [ ] Generate bishop sheets with pointed helm, electric staff, wind-up, three casting strikes, lightning finisher, hit, burn entry, and cheer; validate both sides.
- [ ] Synchronize three crackle bursts and one low lightning strike. Victim uses genuine hit frames before white flash, black burn, and ash.
- [ ] Verify 3.7–4.3s duration, correct death, zero leftovers, and queue feedback under 50ms for both sides/orientations.
- [ ] Commit: `git commit -m "feat: add animated rook cannon and bishop lightning battles"`.

### Task 7: Produce queen, king, and pawn sheets and battles

**Files:**
- Create: `assets/pieces/white-queen.png`, `black-queen.png`
- Create: `assets/pieces/white-king.png`, `black-king.png`
- Create: `assets/pieces/white-pawn.png`, `black-pawn.png`
- Modify: `assets/pieces/manifest.js`
- Modify: `chess.html`

- [ ] Generate queen sheets with crown helm, acid staff, three casts, full-body finisher, hit, melt entry, and cheer; validate geometry and matching alpha masks.
- [ ] Synchronize three wet contacts and a large acid wave. Force the entire victim green before collapsing it into a wide pool.
- [ ] Generate king sheets with crown armor, throwable sword, two cuts, spin wind-up, release, recover, hit, pierced fall, and cheer.
- [ ] Synchronize two cuts, rotating throw, embedded blade, fall, and metal impact. The held sword disappears on release and returns only during recover/cheer.
- [ ] Generate pawn sheets with round helmet, short spear, six-frame walk, three distinct jabs, heavy lunge, hit, sand entry, and cheer.
- [ ] Synchronize three light jabs and one full-body lunge before frame-based sand death.
- [ ] Run all six piece types in `?fx` for both sides, reduced motion, flip, mobile viewport, queue, and cancellation; no state may fall back to static bobbing.
- [ ] Commit: `git commit -m "feat: complete animated pixel chess army"`.

### Task 8: Tune audio, hit stops, and performance

**Files:**
- Modify: `chess.html`
- Modify: `docs/testing/flat-battle-checklist.md`

**Interfaces:**
- Produce `audioBus` with master, impact, weapon, and ambient gains.
- Produce `hitStop(ms)` capped at 90ms.
- Produce normal/reduced motion profiles and a 120-particle ceiling.

- [ ] Instrument scheduled contact, actual contact frame, and audio trigger; fail tests if they differ by more than one animation frame.
- [ ] Route oscillators/noise through a master compressor and gain so rapid hits do not clip.
- [ ] Pause only the battle timeline and two battle sprites during a hit stop; never block pointer feedback, menus, or the global sprite loop.
- [ ] Pool/recycle at most 120 active battle particles and assert zero after completion/cancellation.
- [ ] For reduced motion, remove shake/trails, reduce repeat hits, shorten to about 1.5s, and preserve essential state/sound at lower density.
- [ ] Profile ordinary move, capture, AI thinking, menu minimize, and victory fireworks. No game-code long task above 50ms; ordinary feedback within one frame; queue feedback under 50ms.
- [ ] Commit: `git commit -m "perf: synchronize battle audio and keep input responsive"`.

### Task 9: Final build, regression, and Vercel verification

**Files:**
- Modify if required: `build-standalone.js`, `build-standalone.pl`, `vercel.json`
- Generated/ignored: `standalone.html`, `artifact.html`, `deploy/index.html`

- [ ] Run `npm run build` on Node/Vercel and `perl build-standalone.pl` locally; compare after normalizing known doctype/data-URI differences.
- [ ] Open `deploy/index.html?test` and `?fx`; all assertions pass, 64 squares click, 12 side/type attacks complete, no console error or leftover effect/active frame.
- [ ] Execute the manual checklist for all modes, AI levels, king rules, hover, queue, undo, reset, flip, minimized menu, fireworks, loss, draw, reduced motion, desktop, and mobile.
- [ ] Confirm optimized sheets total at most 4MB; optimize losslessly before reducing fidelity.
- [ ] Commit release files and push `main`.
- [ ] Wait for the matching Vercel deployment to become READY.
- [ ] Verify `https://chess1-psi.vercel.app`: title, 32 initial pieces, embedded sheets, flat board, queue, all six deaths, and zero console errors.

