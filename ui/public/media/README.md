# Pet art

File name = state name: `idle curious thinking asking celebrating sleeping stressed detective`
Formats tried in order: `.png`, `.webp`, `.gif`, `.svg` (transparent background, square, ~512px is plenty).

Lookup per state (first file that loads wins, otherwise built-in fallback art):
1. `media/{variant}-s3/{state}.*`   only at stage 3 (`wizard-s3`, `dragon-s3`)
2. `media/{variant}/{state}.*`      `wizard` or `dragon` (stage 2+)
3. `media/{state}.*`                generic, used by every stage/variant that has no specific file

The files in here are generated placeholders (`npm run gen:media`). To use real art: drop your files
in the same folders (a `.png` beats a placeholder `.svg`) or delete the placeholder folders.
A missing file never breaks anything, that state just falls back to the built-in drawing.

Mood overlays (detective glasses, hard hat) are drawn on top of whatever art loads. If your art puts the
face elsewhere, nudge the coordinates in `src/pet/Overlays.tsx`.
Preview every state: http://localhost:1420/?gallery (has a "force fallback art" toggle).
