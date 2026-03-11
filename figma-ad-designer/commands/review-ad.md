---
description: Review existing ad designs in Figma against platform rules, safe zones, brand compliance, and best practices.
argument-hint: "[figma link or selection]"
allowed-tools:
  - Read
  - mcp__figma*
---

# /review-ad

## Instructions

You are reviewing ad designs for production readiness.

### 1. Read the ad-design-guru skill
Read `skills/ad-design-guru/SKILL.md` — specifically Rules 1-8 and the Checklist.

### 2. Read platform-specific rules
- For Meta ads: `skills/ad-design-guru/references/meta-ads-rules.md`
- For Google ads: `skills/ad-design-guru/references/google-ads-rules.md`

### 3. Inspect the Figma Design via figma-remote-mcp

Check each ad frame for the following:

**A. Two-container structure (Rule 1):**
- Does Container 1 exist at correct format dimensions?
- Does ContentFrame exist as a child of Container 1?
- Are ContentFrame dimensions and position correct per format table?
- Is ContentFrame NOT 1280x1280 at x=80 y=80? (known default bug)
- Are all text/logo/CTA children of ContentFrame?
- Are background/overlay/decorative elements children of Container 1?

**B. Naming (Rule 2):**
- Frame name matches BrandName-MM.DD-Format-Variation?
- No spaces, no text months, no underscores?
- All layers have descriptive names (no auto-generated)?

**C. Typography (Rule 3):**
- Headlines meet minimum size for the frame width?
- Headlines are Bold or Semibold weight?
- Body and CTA meet minimums?

**D. Image safety (Rule 4):**
- No text over faces, heads, hair, eyes?
- No text covering hands holding products?
- Dark overlay present where text sits over images?

**E. Logo (Rule 5):**
- Logo width is 8-15% of frame width?

**F. Platform compliance:**
- 9:16: No content in top 250px or bottom 250px of the artboard (Meta UI zones)?
- CTA contrast ratio 4.5:1 or higher?

**G. Composition (Rule 12):**
- Clear 3-tier visual hierarchy? (headline largest/boldest → body medium → metadata recedes)
- Single focal point? (no competing elements at the same visual weight)
- Sufficient whitespace? (min 40px after heading, 24px between blocks)
- Reading flow matches format? (top-down for vertical, Z-pattern for 1.91:1)
- Text on images legible? (overlay or shadow present)

### 4. Deliver the Review

Format your review as:

**Overall Score: X/10**

**Critical Issues** (must fix before launch):
- Issue description + specific fix recommendation with exact values

**Warnings** (should fix for better performance):
- Issue description + recommendation

**Suggestions** (nice to have):
- Improvement ideas

**What's Working Well:**
- Positive observations

Be specific with measurements, positions, and actionable fixes.
Don't just say "improve contrast" — say "CTA button #FF0000 on #CC0000
background has 1.5:1 ratio. Needs minimum 4.5:1. Suggest white text
on the existing red, or change button to #FF0000 on white."
