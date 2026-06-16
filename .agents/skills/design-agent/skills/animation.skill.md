---
name: animation
description: Use for animated video-style HTML artifacts — explainer animations, motion design demos, sequential reveals. Loads the timeline engine with Stage, Sprite, easing curves, and a scrubber UI.
---

# Animation Engine

Timeline-based motion design. Single starter: `starters/animations.jsx`.

## When to use

- Animated video / explainer
- Motion-design demos
- Sequential reveals that need precise timing
- Interactive prototypes where state-based CSS transitions aren't enough

## When NOT to use

- Simple hover/click transitions (CSS transitions / React state are enough)
- Static designs that don't need motion
- Interactive prototypes with user-driven flow (use React state instead)

## Provided primitives

- `<Stage>` — auto-scaling canvas with built-in scrubber and play/pause
- `<Sprite start end>` — element visible between two timeline points
- `useTime()` — hook returning current playhead time
- `useSprite()` — hook for sprite-local time
- `Easing.{linear, easeIn, easeOut, easeInOut, ...}` — easing curves
- `interpolate(t, from, to, easing)` — value interpolation helper

## Rules

- **Compose scenes by nesting Sprites in a Stage.** Don't manage time manually.
- **Resist titles.** Don't add a title card to the animation unless explicitly asked — center the actual content in the viewport.
- **Persist playback position** in localStorage so refreshes don't reset (the starter handles this).
- **Fall back to Popmotion** only if the starter genuinely can't cover the case (e.g. physics).

## Usage

```jsx
<script type="text/babel" src="starters/animations.jsx"></script>
<script type="text/babel">
  const { Stage, Sprite, useTime, Easing, interpolate } = window;

  function Scene() {
    const t = useTime();
    return (
      <Stage duration={5000} width={1280} height={720}>
        <Sprite start={0} end={2000}>
          <div style={{
            transform: `translateX(${interpolate(t, 0, 200, Easing.easeOut)}px)`
          }}>Hello</div>
        </Sprite>
        <Sprite start={1500} end={5000}>
          {/* second element */}
        </Sprite>
      </Stage>
    );
  }
</script>
```

Read the starter source for full API. Don't reinvent — use the provided primitives.
