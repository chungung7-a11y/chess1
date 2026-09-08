# Piece sprite manifest

`manifest.js` is the single source of truth for piece-sheet geometry and animation timing.
It exposes `PIECE_SPRITES` with all twelve side/type keys (`wK` through `wP` and `bK`
through `bP`). The knight entries (`wN` and `bN`) now point to the production 48-frame
pixel sheets; the other pieces keep `url: null` until their own sheets are added, so the
CSS character renderer remains the functional fallback for them.

Each entry has this shape:

```js
{
  url: null,                 // knight entries: "assets/pieces/white-knight.png"
  cell: [96, 128],           // frame width and height in pixels
  grid: [12, 4],             // sheet columns and rows
  foot: [48, 120],           // fixed foot anchor inside every frame
  states: {
    idle: [0, 4, 8, true]    // start frame, frame count, fps, loop
  }
}
```

Frames are numbered left-to-right, then top-to-bottom. Every frame must use the same
cell size and foot anchor. White and black variants must keep identical geometry,
state ranges, frame order, and alpha silhouettes. Sheet URLs are relative to
`chess.html`; both standalone builders replace every non-null manifest image URL with
an embedded data URI and stop with the missing filename if an asset cannot be read.
