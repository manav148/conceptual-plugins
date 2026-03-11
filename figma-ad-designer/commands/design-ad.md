---
description: Create ad designs in Figma for Meta or Google campaigns.
argument-hint: "[meta|google|both] [brief]"
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__figma*
---

# /design-ad

## STEP 1: READ SKILL

Read `skills/ad-design-guru/SKILL.md` completely before doing anything else.
Also read the relevant platform reference:
- Meta campaigns → `skills/ad-design-guru/references/meta-ads-rules.md`
- Google campaigns → `skills/ad-design-guru/references/google-ads-rules.md`

## STEP 2A: READ BRAND FILE

1. Ask the designer for: brand name + Figma brand file link
2. Open the brand file via figma-remote-mcp
3. Find the `BrandAssets` page
4. Read colors from the `Colors` frame (swatches: Primary, Secondary, Accent, CTA, TextLight, TextDark, BackgroundLight, BackgroundDark)
5. Read fonts from the `Typography` frame (layers: HeadingFont, BodyFont, CTAFont)
6. Read logos from the `Logos` frame (layers: LogoFull, LogoIcon, LogoLight, LogoDark)
7. Present extracted brand data to the designer for confirmation

If the brand file doesn't have a standardized `BrandAssets` page, fall back to manual questions:
- Heading font + weight? Body font? CTA font? (MANDATORY — suggest pairings if unsure)
- Brand colors (hex)? CTA button color? Dark or light background?

## STEP 2B: CAMPAIGN QUESTIONS

Ask all of the following. Wait for answers. Do not start designing until all are answered.

1. Campaign name?
2. **Which Figma page?** (MANDATORY — follow this procedure):
   a. List ALL pages in the Figma file via figma-remote-mcp
   b. Present the list to the designer
   c. Ask: "Which page should I place the ads on?"
   d. Wait for their answer — do NOT proceed without confirmation
   e. If they want a new page: create `[CampaignName]-Ads` (CamelCase, no spaces)
   f. NEVER use the first page. NEVER use the BrandAssets page.
3. Formats needed? (1:1, 4:5, 9:16, 1.91:1, PMax, all)
4. Headline text?
5. CTA text?
6. Body copy?
7. Image(s)?

DO NOT CREATE ANYTHING UNTIL STEPS 2A AND 2B ARE BOTH COMPLETE.

## STEP 3: SELECT LAYOUT TEMPLATE (Rule 11)

Based on the campaign brief and content, choose a layout template:
- **Template A: Hero Image + Overlay** — lifestyle imagery, product photography, brand awareness
- **Template B: Thread / Conversation** — social proof, UGC-style, Reddit/X native ads
- **Template C: Centered Minimal** — announcements, offers, typographic ads
- **Template D: Product Showcase** — e-commerce, product launches, feature highlights
- **Template E: Testimonial / Quote** — customer quotes, review highlights

If the designer has a preference, use it. Otherwise, recommend one based on the content.
Templates can be combined (e.g., Hero Image background + Testimonial content).

## STEP 4: BUILD THE 1:1 MASTER FORMAT FIRST

Design the 1:1 square as the master. All other formats adapt from this.
Follow the two-container architecture from SKILL.md Rule 1.

### A. Create Container 1 (outer Ad Frame)
- 1440×1440 for 1:1
- Clip content: ON
- Name: `BrandName-MM.DD-1:1-1` (see Step 5 for naming rules)

### B. Add background INSIDE Container 1
- Background image: fill entire Container 1 edge-to-edge
- Dark overlay (if needed): x=0, y=0, 1440×1440, black fill, opacity 40–60%, name `DarkOverlay`
- Decorative shapes, gradients, blobs — all go in Container 1

### C. Create ContentFrame INSIDE Container 1
- 1150×1150 at x=145, y=145
- No fill, no stroke, clip content ON
- Name: `ContentFrame`

### D. VERIFY ContentFrame (MANDATORY — Rule 8)
**KNOWN ISSUE:** figma-remote-mcp may default to 1280×1280 at x=80, y=80.
1. Select ContentFrame, read actual W, H, X, Y
2. If wrong → resize to 1150×1150, reposition to x=145, y=145
3. Do NOT proceed until verified

### E. Place content INSIDE ContentFrame using zones (Rule 10)
Use the zone system for element placement:
- Logo zone (top 0-8%): logo at ~y=0-92
- Primary zone (10-50%): headline at ~y=115-575
- Secondary zone (45-85%): body copy at ~y=518-978
- Action zone (85-100%): CTA at ~y=978-1150

All coordinates RELATIVE to ContentFrame. x=0, y=0 = top-left of ContentFrame.
DO NOT use auto-layout. DO NOT put text in Container 1.

### F. Apply design rules
- Text sizes: Rule 3 (min 72px headline for 1440px frames)
- Image safety: Rule 4 (never cover faces, hands)
- Logo sizing: Rule 5 (8–15% of frame width: 115-216px for 1440px)
- CTA contrast: minimum 4.5:1 ratio

## STEP 5: ADAPT TO ADDITIONAL FORMATS (Rule 9)

For each additional format requested, adapt from the 1:1 master.

### For each format, repeat:
A. Create Container 1 at format dimensions
B. Add background (same image, fill to new dimensions)
C. Create ContentFrame at exact specs:

| Format | Width | Height | X   | Y   |
|--------|-------|--------|-----|-----|
| 4:5    | 1150  | 1430   | 145 | 185 |
| 9:16   | 1000  | 1220   | 40  | 250 |
| 1.91:1 | 1664  | 860    | 200 | 110 |

Google PMax:
| Format    | Width | Height | X  | Y  |
|-----------|-------|--------|----|----|
| Landscape | 1080  | 548    | 60 | 40 |
| Square    | 1080  | 1080   | 60 | 60 |
| Portrait  | 860   | 1080   | 50 | 60 |

D. VERIFY ContentFrame (Rule 8 — mandatory for every format)
E. Place content using adaptation rules:

**4:5** — same widths, spread elements vertically, keep font sizes
**9:16** — scale fonts ~75-80%, narrow element widths, vertical stack
**1.91:1** — DIFFERENT LAYOUT: split content side-by-side (left half + right half), scale fonts for height constraint

F. Name frame and layers (Step 5)

## STEP 6: NAME — STRICT FORMAT

### Frame naming
`BrandName-MM.DD-Format-Variation`

Rules:
- NO spaces anywhere
- CamelCase for multi-word brands: `AcmeCoffee`, not `Acme Coffee`
- MM.DD with leading zeros: `03.03`, not `3.3` or `Mar 3`
- Variation is a plain number: `1`, `2`, `3`

CORRECT: `Marquis-03.03-1:1-1`, `AcmeCoffee-01.15-4:5-2`, `Superhuman-12.08-9:16-3`
WRONG: `Marquis - Mar 3 - 1:1 - 8`, `marquis-03.03-1:1-1`, `Marquis-3.3-1:1-1`

### Layer naming
All layers named descriptively. No `Frame 47` or `Rectangle 12`.
Required: `CTA`, `BodyCopy`, `Heading`, `Logo`, `DarkOverlay`, `Image`, `Background`, `ContentFrame`

## STEP 7: FINAL VERIFICATION (every format)

Before showing the designer, check ALL of the following for EACH format:

1. **ContentFrame dimensions** — W, H, X, Y match the table for this format
2. **ContentFrame not defaulted** — NOT 1280×1280 or 1440×1440
3. **Content hierarchy** — ALL text/logo/CTA are children of ContentFrame
4. **Background hierarchy** — Background/overlay/decorative elements are children of Container 1
5. **Frame naming** — `BrandName-MM.DD-Format-Variation`, no spaces, no text months
6. **Layer naming** — Every layer has a descriptive name
7. **Text sizes** — Meet minimums for this frame width (Rule 3)
8. **No text over faces** — Rule 4 respected
9. **Zone placement** — Content sits in correct zones (Rule 10)
10. **1.91:1 layout** — Uses side-by-side layout, NOT vertical stack
11. **Page placement** — All frames are on the designer's chosen page (NOT first page, NOT BrandAssets)

If ANY check fails, fix it before presenting to the designer.
