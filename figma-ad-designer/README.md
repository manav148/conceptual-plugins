# Figma Ad Designer — Claude Code Plugin

**By Conceptual HQ**

AI-powered ad design assistant for producing Meta and Google Ads in Figma. Built for Conceptual HQ's design team to streamline ad production workflows.

## What It Does

This plugin turns Claude Code into a senior ad designer that works inside Figma via `figma-remote-mcp`. It knows:

- **Meta Ads formats**: 1:1 (1440×1440), 4:5 (1440×1800), 9:16 (1080×1920), 1.91:1 (2064×1080)
- **Google PMax assets**: Landscape, square, portrait, logos, and text asset specs
- **Safe zones**: Where Meta UI overlays, where Google badges appear, where content gets cut
- **Design rules**: Visual hierarchy, typography minimums, contrast ratios, text overlay limits
- **Brand compliance**: Works from brand files or helps set them up from scratch
- **Production workflow**: Master design → format adaptation → review → delivery

## Installation

### Prerequisites
- [Claude Code](https://claude.ai/code) installed
- Figma account with MCP server access
- `figma-remote-mcp` already configured in Claude Code

### Install the Plugin

```bash
# Option 1: From GitHub marketplace
/plugin marketplace add conceptualhq/figma-ad-designer
/plugin install figma-ad-designer

# Option 2: Local development
/plugin marketplace add /path/to/figma-ad-designer
/plugin install figma-ad-designer
```

Restart Claude Code after installation.

## Commands

| Command | Description |
|---------|-------------|
| `/design-ad` | Create new ad designs for Meta or Google campaigns |
| `/setup-brand` | Set up a brand asset file in Figma for a client |
| `/review-ad` | Review existing ad designs against platform rules and best practices |

## Usage Examples

```bash
# Design Meta ads for all formats
/design-ad meta Summer sale campaign for fashion brand — all 4 formats

# Design Google Performance Max assets
/design-ad google pmax assets for B2B SaaS product launch

# Design for both platforms
/design-ad both Full campaign kit for restaurant grand opening

# Set up brand assets for a new client
/setup-brand Acme Coffee Co

# Review existing designs
/review-ad check the Instagram story ads for safe zone compliance
```

## Plugin Structure

```
figma-ad-designer/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json                          # Figma MCP configuration
├── commands/
│   ├── design-ad.md                   # /design-ad command
│   ├── setup-brand.md                 # /setup-brand command
│   └── review-ad.md                   # /review-ad command
├── agents/
│   └── ad-qa-reviewer.md             # QA review sub-agent
├── skills/
│   ├── ad-design-guru/
│   │   ├── SKILL.md                   # Core design knowledge
│   │   └── references/
│   │       ├── meta-ads-rules.md      # Meta platform specs
│   │       └── google-ads-rules.md    # Google/PMax specs
│   └── brand-setup/
│       └── SKILL.md                   # Brand file setup workflow
└── README.md
```

## Customization

### Adding Client Brand Guidelines

Edit or create brand reference files per client. The brand-setup skill
and `/setup-brand` command will help organize these in Figma.

### Updating Ad Formats

If Conceptual HQ's standard sizes change, update the format tables in:
- `skills/ad-design-guru/SKILL.md` (main format table)
- `skills/ad-design-guru/references/meta-ads-rules.md`
- `skills/ad-design-guru/references/google-ads-rules.md`

## License

MIT — Built by Conceptual HQ
