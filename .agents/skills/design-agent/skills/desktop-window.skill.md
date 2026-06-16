---
name: desktop-window
description: Use when the design is a desktop app, web app screenshot, or marketing image needing macOS/browser window chrome around it. Provides traffic-light window controls (macOS) or tab bar + URL bar (browser).
---

# Desktop Window Chrome

Two starters:

- `starters/macos-window.jsx` — macOS window with traffic lights and titlebar
- `starters/browser-window.jsx` — Browser tab bar, URL bar, controls

## When to use

- Desktop app mockup (use `macos-window`)
- Web app screenshot/marketing context (use `browser-window`)
- "What it looks like in context" presentations
- Comparing desktop-bound variants — emit one `*_design.html` per option (the host's Canvas arranges them)

## When NOT to use

- Mobile (use `phone-frame`)
- Full-bleed marketing without chrome
- Real apps (just render the HTML, no frame)

## Rules

- **Don't fake URLs you wouldn't use.** Browser URL should match the actual brand: `app.koko.com`, not `lovely-product.com`.
- **Tab names should be product-relevant**, not "Untitled 1".
- **macOS window for apps**, browser window for web. Don't mix unless the design specifically calls for a Mac running a browser.

## Usage

```jsx
<script type="text/babel" src="starters/macos-window.jsx"></script>
<script type="text/babel">
  const { MacosWindow } = window;
  function App() {
    return (
      <MacosWindow title="Koko Studio" width={1200} height={800}>
        {/* your app content */}
      </MacosWindow>
    );
  }
</script>
```

For browser, replace with `BrowserWindow` and pass tab names + URL via props. Read the starter source for full prop API.
