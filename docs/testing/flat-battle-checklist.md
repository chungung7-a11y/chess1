# Flat Pixel Battle Manual Regression Checklist

Run this checklist against both `chess.html` and the built `deploy/index.html`.
Use `?test` for automated assertions and `?fx` for battle-effect previews.

## Board and controls

- [ ] All 64 square centers are visible and individually clickable.
- [ ] Flip the board twice; pieces, labels, markers, projectiles, and particles stay screen-aligned.
- [ ] Minimize and restore the menu; the board expands and returns without overlap.
- [ ] Hover movable white and black pieces; the eligible-piece glow is obvious.

## Input responsiveness

- [ ] Make a non-capture move, then select a next-turn piece on the next animation frame.
- [ ] During a capture, queue one next-turn piece and see feedback within 50ms.
- [ ] Click a different eligible piece to replace the queued selection.
- [ ] Click the queued piece again to cancel it.
- [ ] Click an invalid square and confirm the queued selection is preserved.
- [ ] Undo during movement and during battle; no stale animation or callback remains.
- [ ] In solo mode, AI calculation may overlap animation but its move waits for the current visual to finish.

## Game modes and outcomes

- [ ] Complete a training answer and load the next problem cleanly.
- [ ] Verify training, solo, and duo modes with both king-rule settings.
- [ ] Preview all six attacks and deaths: pawn, knight, bishop, rook, queen, king.
- [ ] Verify win, loss, and draw presentations.
- [ ] Verify victory fireworks finish without leftover effects.

## Viewports and accessibility

- [ ] Check 520×900, 730×582, 1440×900, and 1600×920 viewports.
- [ ] Repeat on a phone-sized viewport with the menu both open and minimized.
- [ ] Repeat battle previews with reduced motion enabled.
- [ ] Confirm no console errors, timers, corpses, particles, queued input, or stale locks remain.
