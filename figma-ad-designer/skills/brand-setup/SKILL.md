---
name: brand-setup
description: >
  Set up brand asset files in Figma for ad production. Triggers when the
  user needs to create a brand book, organize brand assets, or set up a
  Figma file with brand colors, fonts, logos for a client.
version: 1.1.0
---

# Brand Setup - Conceptual HQ

You help designers set up and organize brand assets in Figma so the
ad-design-guru skill can read them automatically during ad production.

**This is not just organization — it's the data source.** The ad-design-guru
skill will read this brand page via figma-remote-mcp to extract colors, fonts,
and logo references. The structure and naming must be exact.

---

## STANDARDIZED BRAND PAGE STRUCTURE

Create a page named exactly: `BrandAssets`

This page contains 4 required frames with exact names. ad-design-guru
will search for these frame names when reading the brand file.

### Frame 1: `Colors`

Contains color swatches as named rectangles.

Required swatches (each is a filled rectangle, named exactly):
- `Primary` — main brand color
- `Secondary` — secondary brand color
- `Accent` — accent or highlight color
- `CTA` — call-to-action button color
- `TextLight` — text color for dark backgrounds (typically white or near-white)
- `TextDark` — text color for light backgrounds (typically black or near-black)
- `BackgroundLight` — light background option
- `BackgroundDark` — dark background option

Each rectangle:
- Size: 200x200px
- Fill: the exact brand hex color
- Name: exactly as listed above (PascalCase, no spaces)
- Arranged in a row with 40px gaps

Optional additional swatches: `Neutral`, `Success`, `Warning`, `Error`
Name them in PascalCase, no spaces.

Under each swatch, add a text layer named `[SwatchName]-Hex` containing
the hex value. Example: a text layer named `Primary-Hex` containing `#1A73E8`.

### Frame 2: `Typography`

Contains text samples showing the font configuration.

Required text layers (named exactly):
- `HeadingFont` — a sample heading using the heading font + weight
- `BodyFont` — a sample body text using the body font + weight
- `CTAFont` — a sample CTA text using the CTA font + weight

Each text layer:
- Set to the correct font family and weight
- Font size: Heading at 80px, Body at 32px, CTA at 36px
- Fill: brand TextDark color

Under each sample, add a descriptor text layer named `[LayerName]-Spec`
containing the font specification string.
Format: `FontFamily / Weight / Size`
Example: a text layer named `HeadingFont-Spec` containing `Montserrat / Bold / 80`

### Frame 3: `Logos`

Contains logo variations as named groups or components.

Required logo layers (named exactly):
- `LogoFull` — full logo (wordmark + icon)
- `LogoIcon` — icon/symbol only
- `LogoLight` — logo version for dark backgrounds (white/light variant)
- `LogoDark` — logo version for light backgrounds (dark variant)

Each logo:
- Vector format (SVG imported or Figma vector)
- Properly grouped if multi-element
- Named exactly as listed

Not every brand has all four. Include what exists, skip what doesn't.
Minimum required: `LogoFull` or `LogoIcon` (at least one).

### Frame 4: `ImageStyle`

Contains 2-3 reference images showing the brand's visual style.

- Name images: `StyleRef-1`, `StyleRef-2`, `StyleRef-3`
- Add a text layer named `ImageNotes` with photography/illustration style notes
  (e.g., "Warm tones, natural lighting, lifestyle focus, avoid stock look")

This frame is for designer reference. ad-design-guru does not read from it
programmatically, but may reference the style notes.

---

## HOW AD-DESIGN-GURU READS THIS PAGE

When the designer provides a brand file link, ad-design-guru will:

1. Open the file via figma-remote-mcp
2. Find the page named `BrandAssets`
3. Read the `Colors` frame → extract hex values from swatch fills
4. Read the `Typography` frame → extract font families and weights from text layers
5. Read the `Logos` frame → get logo node references for placement
6. Present the extracted brand data to the designer for confirmation
7. Use those values for the entire ad campaign (no manual hex/font entry needed)

**This only works if the naming is exact.** If the frame is named "Color Palette"
instead of "Colors", or a swatch is named "primary" instead of "Primary",
ad-design-guru won't find it.

---

## WORKFLOW: FROM BRAND BOOK

1. Designer provides brand book (PDF, URL, or description)
2. Extract: primary/secondary/accent colors, CTA color, fonts, logo files
3. Create `BrandAssets` page in Figma via figma-remote-mcp
4. Build all 4 frames with exact naming from the spec above
5. Present to designer for review
6. Designer confirms → brand file is ready for ad production

## WORKFLOW: FROM SCRATCH

1. Ask the designer:
   - Client website URL?
   - Any logo files?
   - Industry / visual direction?
   - Any existing social posts or ads for reference?
2. Extract brand elements from website (colors, fonts, imagery style)
3. Propose palette and font pairing
4. After designer approval, create the standardized `BrandAssets` page
5. Designer confirms → brand file is ready

## WORKFLOW: FROM EXISTING FIGMA FILE

If the designer already has a Figma file with brand assets but it's not
in the standardized format:

1. Read the existing file via figma-remote-mcp
2. Identify colors, fonts, logos, imagery from whatever structure exists
3. Create a new `BrandAssets` page with the standardized frame structure
4. Populate it from the existing assets
5. Designer confirms → brand file is ready

---

## NAMING SUMMARY

Everything uses PascalCase, no spaces:

- Page: `BrandAssets`
- Color frame: `Colors`
- Color swatches: `Primary`, `Secondary`, `Accent`, `CTA`, `TextLight`, `TextDark`, `BackgroundLight`, `BackgroundDark`
- Hex labels: `Primary-Hex`, `Secondary-Hex`, etc.
- Typography frame: `Typography`
- Font samples: `HeadingFont`, `BodyFont`, `CTAFont`
- Font specs: `HeadingFont-Spec`, `BodyFont-Spec`, `CTAFont-Spec`
- Logo frame: `Logos`
- Logo layers: `LogoFull`, `LogoIcon`, `LogoLight`, `LogoDark`
- Image frame: `ImageStyle`
- Reference images: `StyleRef-1`, `StyleRef-2`, `StyleRef-3`
- Style notes: `ImageNotes`
