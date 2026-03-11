---
description: Set up a brand asset file in Figma for a new or existing client. Creates the standardized BrandAssets page that ad-design-guru reads from automatically.
argument-hint: "[client name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__figma*
---

# /setup-brand

## Instructions

You are setting up a brand asset file in Figma for ad production.
The structure you create will be read automatically by the ad-design-guru
skill during `/design-ad`. Naming must be exact.

### 1. Read the brand-setup skill
Read `skills/brand-setup/SKILL.md` for the complete structure spec and naming rules.

### 2. Ask What's Available
- "What's the brand name?"
- "Do you have a brand book or style guide?"
- "Is there an existing Figma file with brand assets?"
- "Can you share the client's website URL?"
- "Do you have logo files?"

### 3. Create the BrandAssets Page in Figma

Using figma-remote-mcp, create a page named exactly `BrandAssets` with these 4 frames:

**`Colors` frame** — rectangles named: Primary, Secondary, Accent, CTA, TextLight, TextDark, BackgroundLight, BackgroundDark. Each filled with the correct hex color. Add hex label text layers (Primary-Hex, Secondary-Hex, etc.).

**`Typography` frame** — text layers named: HeadingFont, BodyFont, CTAFont. Each set to the correct font family and weight. Add spec labels (HeadingFont-Spec, etc.) with format: "FontFamily / Weight / Size".

**`Logos` frame** — logo layers named: LogoFull, LogoIcon, LogoLight, LogoDark. Include whichever variations exist.

**`ImageStyle` frame** — 2-3 reference images named StyleRef-1, StyleRef-2, StyleRef-3. Add an ImageNotes text layer with photography/style notes.

### 4. Verify the Structure

After creating, read back the BrandAssets page via figma-remote-mcp and confirm:
- Page is named `BrandAssets` (not "Brand Assets" or "brand-assets")
- All frame names match exactly: `Colors`, `Typography`, `Logos`, `ImageStyle`
- All swatch/layer names use PascalCase with no spaces
- Color swatches have correct hex fills

### 5. Confirm with the Designer
Present the brand setup and ask for approval before ad production begins.

Tell the designer: "Your brand file is set up. When you run /design-ad,
I'll read these assets automatically — no need to re-enter colors or fonts."

## Examples
```
/setup-brand Acme Coffee Co
/setup-brand new client — website is example.com
/setup-brand existing file — https://figma.com/file/xxxxx
```
