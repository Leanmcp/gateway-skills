// Generates the 1024x1024 App Store icon (a "2048" tile) and writes it into
// the asset catalog. Run from the project root:
//
//     swift workspace/make_icon.swift
//
// Uses CoreGraphics + CoreText rather than AppKit, for two reasons:
//
//   1. NSImage.lockFocus() renders at the display's backing scale, so on a
//      Retina Mac a 1024-point canvas yields a 2048-pixel file and actool
//      rejects it. A CGContext is sized in pixels, full stop.
//   2. AppKit drawing from a bare `swift` script (no NSApplication) is fragile
//      and can trap. CoreGraphics has no such dependency.
//
// The bitmap uses `noneSkipLast`: 32 bits per pixel with the alpha byte
// ignored. That is a valid CGBitmapContext layout (24-bit RGB is NOT — asking
// for it crashes), and it produces a PNG with no alpha channel, which the App
// Store requires for app icons.
import CoreGraphics
import CoreText
import Foundation
import ImageIO

let pixels = 1024
let outputPath = "Twenty48/Assets.xcassets/AppIcon.appiconset/AppIcon.png"

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

guard let context = CGContext(
    data: nil,
    width: pixels,
    height: pixels,
    bitsPerComponent: 8,
    bytesPerRow: 0,
    space: CGColorSpaceCreateDeviceRGB(),
    bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
) else {
    fail("Could not create bitmap context")
}

let side = CGFloat(pixels)

// Background: the same gold as Theme.tileColor(for: 2048). Drawn edge to edge —
// iOS applies its own rounded-rect mask, so the artwork needs no corner radius.
context.setFillColor(CGColor(srgbRed: 0.93, green: 0.76, blue: 0.18, alpha: 1))
context.fill(CGRect(x: 0, y: 0, width: side, height: side))

/// Picks the first font that actually resolves. `CTFontCreateWithName` falls
/// back silently to a default rather than failing, so the PostScript name is
/// compared back to confirm the real thing was found.
func resolveFont(size: CGFloat) -> CTFont {
    for name in ["SFProDisplay-Bold", "SFProText-Bold", "HelveticaNeue-Bold", "Helvetica-Bold"] {
        let font = CTFontCreateWithName(name as CFString, size, nil)
        if (CTFontCopyPostScriptName(font) as String) == name {
            return font
        }
    }
    return CTFontCreateWithName("Helvetica-Bold" as CFString, size, nil)
}

let attributed = NSAttributedString(
    string: "2048",
    attributes: [
        kCTFontAttributeName as NSAttributedString.Key: resolveFont(size: side * 0.30),
        kCTForegroundColorAttributeName as NSAttributedString.Key:
            CGColor(srgbRed: 0.18, green: 0.17, blue: 0.15, alpha: 1)
    ]
)

// Optical bounds centre the glyphs by their visible ink rather than by the
// font's line metrics, which include ascender/descender padding the digits
// never use.
let line = CTLineCreateWithAttributedString(attributed)
let bounds = CTLineGetBoundsWithOptions(line, .useOpticalBounds)

context.textPosition = CGPoint(
    x: (side - bounds.width) / 2 - bounds.minX,
    y: (side - bounds.height) / 2 - bounds.minY
)
CTLineDraw(line, context)

guard let image = context.makeImage() else {
    fail("Could not render image")
}

let url = URL(fileURLWithPath: outputPath) as CFURL
guard let destination = CGImageDestinationCreateWithURL(url, "public.png" as CFString, 1, nil) else {
    fail("Could not open \(outputPath) for writing")
}

CGImageDestinationAddImage(destination, image, nil)
guard CGImageDestinationFinalize(destination) else {
    fail("Could not write PNG")
}

let hasAlpha = image.alphaInfo != .none && image.alphaInfo != .noneSkipLast && image.alphaInfo != .noneSkipFirst
print("Wrote \(outputPath) — \(image.width)x\(image.height), alpha: \(hasAlpha)")
