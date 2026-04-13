# Stripe Plugin

Query and manage your Stripe account directly from Claude Code via the Stripe API v1. Read customers, charges, payment intents, subscriptions, invoices, products, prices, balance, payouts, refunds, disputes, and events. Create customers, products, prices, payment intents, subscriptions, invoices, checkout sessions, refunds, and payouts.

## Setup

1. Grab a secret key from the Stripe dashboard → **Developers → API keys**.
   - `sk_test_...` for test mode (safe, no real money)
   - `sk_live_...` for live mode (real money, real cards, real customers)
2. Export it as an environment variable before starting Claude Code:
   ```bash
   export STRIPE_API_KEY="sk_test_..."
   # or: export STRIPE_API_KEY="sk_live_..."
   ```
3. Invoke `/stripe` in Claude Code.

## Features

- **Customers** — list, get, create, update
- **Charges & Payment Intents** — list, get, create, confirm, capture, cancel
- **Refunds** — create full or partial refunds against charges or payment intents
- **Subscriptions** — list, get, create, update (including price swaps with proration), cancel immediately or at period end
- **Invoices** — list, get, create drafts, finalize, pay, send, void
- **Products & Prices** — list, get, create (prices are immutable — archive to replace)
- **Balance & Balance Transactions** — check available / pending balance, query the ledger
- **Payouts** — list, get, create manual payouts to the linked bank
- **Disputes** — list and inspect chargebacks
- **Events** — audit 30-day event log and replay specific events
- **Checkout Sessions** — create hosted-page payment flows
- **GAQL-style free-form queries** — the skill accepts any REST path and renders the response as a table

## Authentication

The plugin reads `STRIPE_API_KEY` from the environment — nothing is written to disk. The key prefix (`sk_test_` vs `sk_live_`) is surfaced before every write so you always know which mode you're about to mutate.

## Safety

Write operations are gated behind explicit confirmation, and any money-moving call (`refunds`, `payouts`, `payment_intents/confirm`, `invoices/pay`, `invoices/send`, subscription cancellation) receives an `Idempotency-Key` automatically so retries don't double-charge. Test with `sk_test_` first.
