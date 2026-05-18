# iOS caveats

Things that look like bugs in your code but are platform behaviour. Ordered by
how often they bite.

## Liquid Glass swallows custom button styling

iOS 26 gives every `Button` and `NavigationLink` a default glass background,
painted *behind* whatever background you set. Custom buttons get a visible
capsule "bubble" around them.

```swift
Button { … } label: { Text("Play").background(myColor, in: RoundedRectangle(…)) }
.buttonStyle(.plain)   // without this, iOS draws its own capsule too
```

Applies to `NavigationLink` with a custom label as well. If buttons look wrong
on device but fine in Previews, this is why.

## Swipe gestures fight the navigation pop gesture

A view pushed onto a `NavigationStack` gets iOS's interactive pop gesture, which
outranks your `DragGesture` near the left edge. In a game or canvas, swiping
left navigates back instead of doing anything useful.

Fix by not pushing: present as `.fullScreenCover`, which has no dismiss gesture
at all, and supply your own top bar. Gesture-priority workarounds
(`.highPriorityGesture`, hiding the back button) are fragile by comparison —
removing the navigation removes the conflict.

## `.offset` does not affect layout size

This is the single most confusing SwiftUI layout trap. `.offset` moves a view
visually but its parent still measures it at its original position. A `ZStack`
of offset children therefore measures as **one child**, and an outer
`.frame(width:height:)` — which centres by default — parks that one-child-sized
stack in the middle. Every offset is then measured from the centre, and the
whole grid shifts down and right.

```swift
.frame(width: w, height: h, alignment: .topLeading)   // not optional
```

A uniform whole-layout translation is almost always an anchor bug, not a
per-element maths bug.

## Animating position needs stable identity

SwiftUI can only animate a view it recognises as the *same view* across
renders. A grid of cells whose values change gives it no way to know something
moved — it cross-fades two unrelated cells instead of sliding one.

Model moving things as `Identifiable` with an `id` created once and preserved
across moves, render them in a flat `ZStack` positioned by `.offset`, and
movement animates for free. A nested `VStack`/`HStack` of cells physically
cannot do this. `ForEach(array.indices, id: \.self)` is fine only for constant
data — with mutable data, index-as-identity animates the wrong things.

## App icons

- Must be exactly **1024×1024** and contain **no alpha channel** — the App
  Store rejects both.
- `NSImage.lockFocus()` renders at the display's backing scale, so a 1024-*point*
  canvas produces a 2048-*pixel* file on any Retina Mac. Draw into an explicitly
  sized `CGContext` instead.
- A 24-bit no-alpha `CGBitmapContext` is **not a supported pixel format** and
  traps. Use `CGImageAlphaInfo.noneSkipLast` — 32 bits with the alpha byte
  ignored, valid as a context *and* produces an alpha-free PNG.
- A wrong-sized icon fails the asset catalog compile, which reads in raw logs
  exactly like a Swift compile error.

## Dynamic Type

`.font(.system(size: 17))` does **not** scale with the user's accessibility text
size. Real support means semantic styles (`.body`, `.title`) plus `@ScaledMetric`
for anything hand-sized.

Mitigations that help either way: `ScrollView` around content that could
overflow, `minimumScaleFactor` on single-line labels, `.padding` instead of
fixed `.frame(height:)` on buttons, `.fixedSize(horizontal: false, vertical:
true)` so body text wraps rather than truncates.

## Simulator vs device

- **CoreMotion returns nothing in the Simulator.** Tilt and shake can only be
  tested on hardware — gate them behind a setting rather than a recompile.
- Haptics are silently ignored in the Simulator.
- Keyboard input needs **I/O → Input → Send Keyboard Input to Device** (⇧⌘K) or
  macOS keeps the keystrokes.
- First boot of a new simulator prints minutes of
  `Waiting on Data Migration … Status=2`. Normal, one-time.

## Shell traps in build scripts

`set -o pipefail` plus `xcodebuild ... | head -1` is an intermittent
script-killer: `head` exits after the first line, `xcodebuild` takes SIGPIPE,
and the pipeline fails — but only when it loses the race. Capture the whole
output first, then trim. Same applies to `grep -m1` and `awk … exit`.

Always pair `set -e` with an `ERR` trap. Its default behaviour — abort with zero
output — is indistinguishable from success at a glance.
