# conceptual-plugins

Claude Code marketplace for Google Ads and marketing tools.

## Plugins

### google-ads

Full Google Ads API management — campaigns, ad groups, ads, keywords, budgets, bidding strategies, conversions, audiences, assets, and GAQL reporting.

See [google-ads-plugin/README.md](./google-ads-plugin/README.md) for details.

### mercury

Mercury Bank account access — list accounts, transactions, statements, cards, recipients; send money via ACH, wire, or check; manage recipients. Authenticates via the `MERCURY_API_KEY` environment variable.

See [mercury-plugin/README.md](./mercury-plugin/README.md) for details.

## Marketplace

This repository serves as a Claude Code marketplace. The `marketplace.json` at the root catalogs all available plugins.

## figma-ad-designer v2.2.0
AI ad design assistant that creates production-ready Meta and Google Ads directly in Figma. Claude Code acts as the designer brain — ##Important must install Figma MCP from Claude Marketplace - is the bridge. Supports 1:1, 4:5, 9:16, and 1.91:1 formats with automatic safe zone compliance, brand file integration, format adaptation, and built-in QA review. Three commands: /design-ad, /setup-brand, /review-ad
