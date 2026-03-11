# Figma Ad Designer — Quick Reference (v2.2.0)

## Commands

| Command | What it does | Key inputs |
|---------|-------------|------------|
| `/design-ad` | Create ad designs in Figma | Brand file, campaign brief, formats, content |
| `/setup-brand` | Set up standardized BrandAssets page | Brand name, brand book/website/files |
| `/review-ad` | QA review existing ads against all rules | Figma link or selection |

## /design-ad Workflow (7 steps)

1. **Read skill** — loads ad-design-guru + platform rules (Meta/Google)
2. **Read brand file** (2A) — pulls colors, fonts, logos from BrandAssets page
   **Campaign questions** (2B) — campaign name, page, formats, headline, CTA, body, images
3. **Select template** — A (Hero), B (Thread), C (Centered), D (Product), E (Testimonial)
4. **Build 1:1 master** — Container 1 → background → ContentFrame → verify → content → composition
5. **Adapt formats** — 4:5 (spread), 9:16 (scale down), 1.91:1 (side-by-side)
6. **Name** — `BrandName-MM.DD-Format-Variation` (no spaces, MM.DD, CamelCase)
7. **Verify** — ContentFrame dims, hierarchy, naming, text sizes, composition

## Format Cheat Sheet

| Format | Container 1 | ContentFrame | Position | Use case |
|--------|------------|--------------|----------|----------|
| 1:1 | 1440×1440 | 1150×1150 | x=145 y=145 | Feed square (master) |
| 4:5 | 1440×1800 | 1150×1430 | x=145 y=185 | Feed vertical, mobile |
| 9:16 | 1080×1920 | 1000×1220 | x=40 y=250 | Reels/Story |
| 1.91:1 | 2064×1080 | 1664×860 | x=200 y=110 | Link ads, landscape |

## Templates (Rule 11)

- **A: Hero Image** — full-bleed photo + dark overlay + text on top
- **B: Thread** — question card + reply card, social proof style
- **C: Centered Minimal** — solid bg, centered text stack, typographic
- **D: Product Showcase** — product image top, text bottom
- **E: Testimonial** — large quote + attribution

## Key Rules to Remember

- **ContentFrame bug**: May default to 1280×1280 at x=80,y=80 — always verify after creation
- **Naming**: No spaces, no text months → `Marquis-03.03-1:1-1`
- **Page placement**: NEVER first page — always list pages and ask, or create new
- **9:16 safe zones**: Top 250px + bottom 250px reserved for Meta UI
- **1.91:1 layout**: Side-by-side (not vertical stack)
- **Text minimums**: 72px headline (1440w), 56px (1080w), 80px (2064w)
- **Logo**: 8-15% of frame width
- **CTA contrast**: 4.5:1 minimum

## BrandAssets Page Structure (for /setup-brand)

Page name: `BrandAssets`
- `Colors` frame → `Primary`, `Secondary`, `Accent`, `CTA`, `TextLight`, `TextDark`, `BackgroundLight`, `BackgroundDark`
- `Typography` frame → `HeadingFont`, `BodyFont`, `CTAFont` + spec labels
- `Logos` frame → `LogoFull`, `LogoIcon`, `LogoLight`, `LogoDark`
- `ImageStyle` frame → `StyleRef-1/2/3` + `ImageNotes`
