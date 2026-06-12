# LodeOS demo video (Remotion)

A code-driven product demo built with [Remotion](https://remotion.dev). No audio;
pure visual storytelling on the LodeOS brand system (warm paper canvas, sage accent,
Hanken Grotesk / Newsreader / Spline Sans Mono).

## Scenes

1. **Problem** - an artist's money lives on six disconnected platforms; nobody watches the gaps.
2. **Control plane** - LodeOS wires the platforms into one agent hub (Flash front line, Pro specialists).
3. **Independent artist** - June Freedom: a $2,400 neighboring-rights finding, drafted for approval.
4. **Label** - Lode Records: $446,716 across 50 artists, with a visible LabelAgent to ActionAgent A2A handoff.
5. **AI-native creator** - Kai Rivers: connectors talk to each other; one ask drafts a Disco pitch under a permission leash.
6. **Close** - one product, three businesses; the stack.

## Commands

```bash
npm install
npm run dev      # open Remotion Studio to preview/scrub
npm run render   # render to out/lodeos-demo.mp4
```

The committed deliverable is rendered to `../docs/lodeos-demo.mp4`:

```bash
npx remotion render LodeOSDemo ../docs/lodeos-demo.mp4 --codec=h264
```

Composition: 1920x1080, 30fps, ~44s. Edit timings in `src/LodeOSDemo.tsx`.
