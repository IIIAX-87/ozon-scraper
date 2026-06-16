---
name: tweaks
description: Use when the user asks to add разные состояния / different states / variants inside a single prototype — dark/light mode, density toggle, color variants, copy alternatives, feature flags. Trigger phrases include "состояние", "состояния", "разные состояния", "states", "variants", "toggle". Provides a floating panel with sliders, toggles, color pickers, segmented controls.
---

# States panel (внутри-дизайна состояния)

In-design controls that let the user explore states/variants inside one HTML file instead of opening multiple. The user-facing label in our Canvas is **«Состояния»** — the toolbar toggle in the host is titled exactly that. The starter file is still called `starters/tweaks-panel.jsx`, and the JSX/React API still uses the names `TweaksPanel`, `useTweaks`, `TweakSection`, etc. — do **not** rename them, the host wires up to those exact identifiers. The concept name in user-facing surfaces is "состояния"; everything else in code stays as-is.

## When to use

- User asks for «состояния», «разные состояния», "states", "variants", or "toggle" of a single aspect (color, density, layout, copy, flag)
- Showing 2+ minor variations that don't deserve separate artboards
- Letting the user "play with" / переключать a single design

## When NOT to use

- For 2+ major variants — emit separate `*_design.html` files instead (the host's Canvas arranges them; Состояния panel is for minor in-design toggles only)
- When the toggle would confuse rather than clarify (avoid 8+ states in one prototype)

## Provided components (keep these names literally — host depends on them)

- `<TweaksPanel>` — floating bottom-right panel with drag + close. Title defaults to **«Состояния»**.
- `useTweaks(defaults)` — `[state, setTweak]` hook with persistence
- `<TweakSection label>` — visual section divider
- `<TweakSlider>`, `<TweakToggle>`, `<TweakRadio>`, `<TweakSelect>`
- `<TweakText>`, `<TweakNumber>`, `<TweakColor>`, `<TweakButton>`

## Persistence pattern

Wrap state defaults in a marker block so values persist to disk on each change:

```jsx
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "dark": false,
  "density": "regular",
  "accent": "#D97757"
}/*EDITMODE-END*/;
```

The JSON between markers is rewritten on every change. **There must be exactly ONE such block per root HTML file.** The `/*EDITMODE-BEGIN*/`…`/*EDITMODE-END*/` marker names are wire-protocol with the host route — do not rename them.

## Rules

- **Panel title — «Состояния»** (matches the toolbar toggle label users see). The starter's default already is `title='Состояния'`; only override if a specific dimension is being tweaked and a more specific label helps (e.g. `title='Темы'`).
- **Hide controls when not active.** When the user closes Состояния, the design should look final — no editor UI visible.
- **Curate color options.** Use `<TweakColor options={[...]}>` with 3–4 swatches, not a free picker.
- **Use TweakRadio for 2–3 short options** (segmented control). For long/many options, use TweakSelect (dropdown).
- **Default-add a couple of states** even if user didn't ask explicitly — surfaces interesting variants. But keep small (3–5 max).
- **Never strip React + Babel to "simplify" the file.** The panel is JSX and needs both, but they load from CDN as three `<script>` tags (see SKILL.md → "Tech rules"). The file stays self-contained — opens by double-click, `file://`, or any static host. **No dev server is required.** If a prior edit produced vanilla HTML without React/Babel, restore the three CDN scripts and the `<script type="text/babel" src="starters/tweaks-panel.jsx">` line; do not rewrite the panel.

## Usage

```jsx
<script type="text/babel" src="starters/tweaks-panel.jsx"></script>
<script type="text/babel">
  const { useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakColor } = window;

  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
    "dark": false,
    "accent": "#D97757"
  }/*EDITMODE-END*/;

  function App() {
    const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
    return (
      <>
        <MyDesign dark={t.dark} accent={t.accent} />
        <TweaksPanel>
          <TweakSection label="Тема" />
          <TweakToggle label="Тёмная" value={t.dark}
                       onChange={(v) => setTweak('dark', v)} />
          <TweakColor label="Акцент" value={t.accent}
                      options={['#D97757', '#2A6FDB', '#1F8A5B']}
                      onChange={(v) => setTweak('accent', v)} />
        </TweaksPanel>
      </>
    );
  }
</script>
```

Read the starter source for full control API including drag-scrubber numbers, palette pickers, etc.
