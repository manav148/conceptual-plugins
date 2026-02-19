# Google Ads Plugin

Manage Google Ads campaigns, ad groups, ads, keywords, budgets, bidding strategies, conversions, audiences, assets, and run GAQL reports directly from Claude Code via the Google Ads REST API v23.

## Setup

1. Invoke `/google-ads` in Claude Code
2. Visit **https://app.conceptualhq.com/credentials** and paste the credentials JSON
3. Start managing your Google Ads account

## Features

- **Campaigns** — Create, list, update, pause, remove
- **Ad Groups** — Full CRUD with bid management
- **Ads** — Responsive search ads creation and management
- **Keywords** — Add, update match types/bids, remove
- **Budgets** — Create and adjust campaign budgets
- **Bidding Strategies** — Target CPA, ROAS, maximize conversions
- **Conversion Actions** — Track and manage conversion events
- **Audiences** — Rule-based user list management
- **Assets** — Text, image, video assets with campaign linking
- **GAQL Reports** — Free-form queries + 8 pre-built report templates

## Credentials

Credentials are held in the conversation context only — nothing is written to disk. When the session ends, credentials are gone.
