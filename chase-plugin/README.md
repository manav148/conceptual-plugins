# Chase Plugin

Query your Chase bank account directly from Claude Code via **Plaid** — accounts, balances, transactions, identity, and ACH routing/account numbers.

## ⚠️ Read this first — how this plugin works

Chase does **not** offer a public REST API for individual account holders. There is no `api.chase.com` you can hit with a Bearer token the way you can with Stripe or Mercury. J.P. Morgan's institutional Payments / Treasury Services APIs exist, but they require an enterprise contract, mTLS certificates, and a 4–12 week onboarding — they are not self-serve.

The standard, legitimate way to programmatically access Chase accounts is **Plaid**. Plaid performs an OAuth handoff to Chase, stores long-lived consent, and exposes a clean REST API for reads. This plugin wraps that API. If you want a direct Chase-only integration, it is not feasible as a self-serve plugin.

## Setup

1. Create a Plaid developer account at https://dashboard.plaid.com/signup — sandbox and development tiers are free and self-serve.
2. Grab your **client_id** and **secret** for your target environment (`sandbox`, `development`, or `production`).
3. Link your Chase account through Plaid Link **once** to obtain an `access_token` for that Item. Plaid's Quickstart (https://plaid.com/docs/quickstart/) walks through this — it's a short Node/Python script that redirects to chase.com, you consent, and it prints the token.
4. Export the four env vars before starting Claude Code:
   ```bash
   export PLAID_CLIENT_ID="..."
   export PLAID_SECRET="..."
   export PLAID_ACCESS_TOKEN="access-development-..."
   export PLAID_ENV="development"   # or sandbox / production
   ```
5. Invoke `/chase` in Claude Code.

## Features (reads — all available on Plaid Development tier, free)

- **Accounts** — list linked Chase accounts with balances
- **Balance** — force a real-time balance refresh for a single account
- **Transactions** — cursor-based sync (preferred) or date-range query, with pending/posted, merchant enrichment, categories
- **Identity** — account holder name, email, phone, address (for KYC/ownership verification)
- **Auth** — ACH routing + account numbers for setting up external transfers
- **Investments** — holdings and transactions (Chase You Invest) if the Plaid product is enabled
- **Liabilities** — Chase credit cards, auto loans, mortgages if enabled
- **Item status** — consent expiration, available products, institution info

## Writes — Plaid Transfer (gated)

Plaid Transfer can initiate ACH debits against a linked Chase account, but it is **not enabled by default** on new Plaid accounts. Enabling it requires:

1. Contacting Plaid sales and signing an addendum to your Plaid MSA.
2. ACH underwriting (business verification, ODFI relationship with Plaid's partner bank, Cross River).
3. Production-only — Transfer does not ship useful sandbox simulation for write flows out of the box.

Until Transfer is enabled on your Plaid account, the write endpoints in this plugin will return `PRODUCT_NOT_READY`. Transfer is debit-only — Plaid cannot push money from Chase to an arbitrary destination; it debits into Plaid's partner bank, from which you disburse through your own flow.

**There is no programmatic path** to send money out of Chase via Zelle, Chase QuickPay, or Chase's own APIs. This is a platform limitation, not a plugin limitation. Do not scrape chase.com — it violates Chase's ToS and breaks constantly.

## Authentication

The plugin reads all four Plaid env vars from the environment. Nothing is written to disk. Plaid credentials are sent as JSON body fields on each call (not headers).

## Safety

- All reads are safe and free on the Plaid Development tier (up to 100 Items per account).
- Writes (`/transfer/*`) will be explicitly confirmed with the user before execution.
- Chase's OAuth consent expires approximately every 12 months — if `item.consent_expiration_time` is close, the plugin will warn you to re-run Plaid Link.
