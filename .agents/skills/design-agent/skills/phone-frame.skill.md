---
name: phone-frame
description: Use when the design needs to look like a real iPhone or Android screen — mobile UI mockups, onboarding flows, app screens, mobile-only prototypes. Wraps content in device bezels with status bar, home indicator, and optional keyboard.
---

# Phone Frame

For mobile mockups that need to read as "real phone". Two starters:

- `starters/ios-frame.jsx` — iPhone bezel (status bar, home indicator, keyboard)
- `starters/android-frame.jsx` — Android bezel (status bar, nav bar, keyboard)

## When to use

- Mobile app mockups, onboarding flows
- iOS/Android-specific designs
- Screens shown in marketing/case-study contexts
- Per-screen variants — emit one `*_design.html` per device-bound option (the host's Canvas tab arranges them)

## When NOT to use

- Desktop UIs (use `macos-window` or `browser-window`)
- Responsive previews (browser dev tools, not a frame)
- Full-bleed designs that don't need device chrome

## Rules

- **One frame per file.** Don't crowd multiple phones in one HTML — emit a separate `*_design.html` per screen, the host's Canvas tab shows them side-by-side.
- **Match the OS to the design.** iOS native designs go in `ios-frame`. Material designs go in `android-frame`. Don't mix.
- **Status bar content** (carrier, battery, time) — keep defaults unless the design specifically needs branded status bar content.
- **Touch targets ≥ 44px** inside the frame. The frame already constrains width to realistic device dimensions.

## Usage

Load with React + Babel (see SKILL.md → "Tech rules" for the pin block), then:

```jsx
<script type="text/babel" src="starters/ios-frame.jsx"></script>
<script type="text/babel">
  const { IosFrame } = window;
  function App() {
    return (
      <IosFrame>
        {/* your screen content — sized to device viewport */}
        <div style={{ padding: 16 }}>...</div>
      </IosFrame>
    );
  }
</script>
```

For Android, replace `IosFrame` with `AndroidFrame`. Read the starter file for full prop API (keyboard visibility, status bar customization, etc).
