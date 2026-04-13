# Mercury Plugin

Query and manage your Mercury Bank account directly from Claude Code via the Mercury API v1. Read accounts, transactions, statements, cards, and recipients; send money (ACH, wire, check) and manage recipients.

## Setup

1. Generate a Mercury API token from **Settings → API** in the Mercury dashboard.
   - **Read Only** — accounts, transactions, statements, cards, recipients
   - **Read/Write** — everything above plus sending money and managing recipients (requires IP allowlist)
   - **Custom** — scope to specific endpoints (e.g., `RequestSendMoney` only)
2. Export the token as an environment variable before starting Claude Code:
   ```bash
   export MERCURY_API_KEY="secret-token:..."
   ```
3. Invoke `/mercury` in Claude Code.

## Features

- **Accounts** — List all accounts, get account details and balances
- **Transactions** — List with filters (date range, status, search), get transaction details
- **Statements** — List monthly statements, download statement PDFs
- **Cards** — List debit/credit cards for an account
- **Recipients** — List, get, create, update payment recipients
- **Payments** — Send money via ACH, domestic wire, or check
- **Approval Flow** — Use request-send-money to queue payments for human approval

## Authentication

The plugin reads `MERCURY_API_KEY` from the environment — nothing is written to disk. Mercury tokens look like `secret-token:<base64>`; include the `secret-token:` prefix.

## Safety

Write operations (sending money, updating recipients) are **live** — Mercury has no public sandbox. The skill will confirm destructive or money-moving actions before executing them. Use `request-send-money` rather than direct `transactions` when you want every payment to require dashboard approval.
