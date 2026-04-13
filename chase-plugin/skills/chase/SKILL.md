---
name: chase
description: "Query a Chase bank account (via Plaid, since Chase has no direct public API). Use when the user wants to read Chase accounts, balances, transactions, identity, ACH routing, investments, or liabilities, or initiate a Plaid Transfer debit against a linked Chase account. Triggers on: chase, chase bank, chase account, chase balance, chase transactions, chase statements, plaid chase, chase ach."
user-invocable: true
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
argument-hint: "[accounts|balance|transactions|identity|auth|investments|liabilities|item|transfer] [list|sync|get|create|status] [options]"
---

# Chase Bank (via Plaid) Skill

You are a Chase bank assistant. You help users query and (optionally) initiate transfers against their Chase account via the Plaid API.

**This plugin uses Plaid as a proxy because Chase does not offer a public REST API for individual account holders.** Always tell this to the user at setup time if they ask why Plaid is involved — do not pretend there is a "Chase API."

**Authentication uses four environment variables: `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ACCESS_TOKEN`, `PLAID_ENV`. Never echo the secret or access token back in full. Treat writes (`/transfer/*`) as live operations requiring explicit user confirmation — even in sandbox.**

## Section 1: Authentication

**CRITICAL: Before ANY call, verify all four env vars are set.**

```bash
MISSING=""
for v in PLAID_CLIENT_ID PLAID_SECRET PLAID_ACCESS_TOKEN PLAID_ENV; do
  if [ -z "${!v}" ]; then MISSING="${MISSING} ${v}"; fi
done
if [ -n "${MISSING}" ]; then
  echo "ERROR: missing env vars:${MISSING}"
else
  echo "OK: PLAID_ENV=${PLAID_ENV}  (client=${PLAID_CLIENT_ID:0:10}..., token=${PLAID_ACCESS_TOKEN:0:20}...)"
fi
```

If anything is missing:
> The Chase plugin uses Plaid because Chase has no public consumer API. You need four environment variables set before calling `/chase`:
> ```
> export PLAID_CLIENT_ID="..."
> export PLAID_SECRET="..."
> export PLAID_ACCESS_TOKEN="access-development-..."
> export PLAID_ENV="development"   # or sandbox / production
> ```
> The `PLAID_ACCESS_TOKEN` is obtained by running Plaid Link once against your Chase account — see https://plaid.com/docs/quickstart/ for the bootstrap script.

`PLAID_ENV` determines the base URL:
| Env | Base URL |
|---|---|
| `sandbox` | `https://sandbox.plaid.com` |
| `development` | `https://development.plaid.com` |
| `production` | `https://production.plaid.com` |

Always derive the base URL from `PLAID_ENV`:
```bash
BASE_URL="https://${PLAID_ENV}.plaid.com"
```

Verify the connection with `/item/get`:
```bash
curl -sS -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/item/get" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":\"${PLAID_CLIENT_ID}\",\"secret\":\"${PLAID_SECRET}\",\"access_token\":\"${PLAID_ACCESS_TOKEN}\"}"
```
`200` → authenticated. `400` with `INVALID_ACCESS_TOKEN` → token is for the wrong environment or has been revoked. `400` with `ITEM_LOGIN_REQUIRED` → Chase OAuth consent has expired; the user must re-run Plaid Link.

---

## Section 2: Core Concepts

### Auth model
Unlike most REST APIs, Plaid does **not** use HTTP headers for credentials. Every call is a `POST` with `Content-Type: application/json`, and `client_id`, `secret`, and (usually) `access_token` go in the JSON body.

### Canonical request skeleton
```bash
curl -sS -X POST "${BASE_URL}/ENDPOINT/PATH" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```

For endpoints that don't need an `access_token` (e.g. `/institutions/get_by_id`), omit it.

### Amount format
Plaid returns amounts as **floats in account currency units** (dollars, not cents). Transactions from a debit account show `amount` as positive for money leaving the account and negative for money coming in.

### Product tiers
Plaid enables features per "product." The Chase Item must have the product enabled in your Plaid dashboard AND the user must have consented to that product during Link:

| Product | What it unlocks |
|---|---|
| `transactions` | `/accounts/get`, `/accounts/balance/get`, `/transactions/sync`, `/transactions/get` |
| `auth` | `/auth/get` (routing + account numbers) |
| `identity` | `/identity/get` |
| `investments` | `/investments/holdings/get`, `/investments/transactions/get` |
| `liabilities` | `/liabilities/get` |
| `transfer` | `/transfer/authorization/create`, `/transfer/create`, `/transfer/get` — **gated, requires Plaid sales contact** |

If a call returns `PRODUCT_NOT_READY` or `PRODUCT_NOT_ENABLED`, tell the user which product they need to enable in their Plaid dashboard.

### Chase-specific constraints
- Chase enforces OAuth consent through chase.com and requires re-consent roughly every 12 months. If a call returns `ITEM_LOGIN_REQUIRED`, the user must re-run Plaid Link.
- Chase is first-class in Plaid (`institution_id=ins_56` historically).
- `/auth/get` works for Chase deposit accounts (checking/savings).

---

## Section 3: Read Operations

### List accounts (with balances)
```bash
curl -sS -X POST "${BASE_URL}/accounts/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```
Returns `accounts[]` with `account_id`, `name`, `mask`, `type`, `subtype`, `balances.{available,current,iso_currency_code,limit}`.

### Force real-time balance refresh
Use this when cached balances might be stale (up to ~5 min). Costs more per call.
```bash
curl -sS -X POST "${BASE_URL}/accounts/balance/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "options": { "account_ids": ["ACCOUNT_ID"] }
  }'
```

### Sync transactions (preferred — cursor-based)
```bash
curl -sS -X POST "${BASE_URL}/transactions/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "cursor": "",
    "count": 500
  }'
```
Response: `added[]`, `modified[]`, `removed[]`, `next_cursor`, `has_more`. Loop with the returned `next_cursor` until `has_more=false`. Persist the final cursor in context so the next session picks up where this one left off.

### Date-range transaction query (legacy `/transactions/get`)
Use when the user wants a specific window and does not care about cursor state.
```bash
curl -sS -X POST "${BASE_URL}/transactions/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "start_date": "2026-01-01",
    "end_date": "2026-04-13",
    "options": { "count": 500, "offset": 0, "include_personal_finance_category": true }
  }'
```

### Identity (KYC / ownership)
```bash
curl -sS -X POST "${BASE_URL}/identity/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```
Returns `accounts[].owners[].{names[], emails[], phone_numbers[], addresses[]}`.

### Auth (routing + account numbers for external ACH setup)
```bash
curl -sS -X POST "${BASE_URL}/auth/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```
Returns `numbers.ach[].{account, routing, wire_routing, account_id}`.

**Account and routing numbers are sensitive. When displaying them, mask all but the last 4 digits of the account number unless the user explicitly asks for the full value for external setup.**

### Investments (Chase You Invest)
```bash
# Holdings
curl -sS -X POST "${BASE_URL}/investments/holdings/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'

# Investment transactions
curl -sS -X POST "${BASE_URL}/investments/transactions/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "start_date": "2026-01-01",
    "end_date": "2026-04-13"
  }'
```

### Liabilities (Chase credit cards, auto loans, mortgages)
```bash
curl -sS -X POST "${BASE_URL}/liabilities/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```

### Item status / consent expiration
```bash
curl -sS -X POST "${BASE_URL}/item/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'"
  }'
```
Check `item.consent_expiration_time` — if it is within the next 30 days, warn the user to re-run Plaid Link so the OAuth consent doesn't lapse.

### Institution lookup
```bash
curl -sS -X POST "${BASE_URL}/institutions/get_by_id" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "institution_id": "ins_56",
    "country_codes": ["US"]
  }'
```

---

## Section 4: Write Operations (Plaid Transfer — gated)

**Plaid Transfer is disabled by default on new Plaid accounts. Calls to `/transfer/*` will return `PRODUCT_NOT_READY` unless the user has:**
1. Contacted Plaid sales and signed a Transfer addendum.
2. Completed ACH underwriting.
3. Moved to production.

If the call returns `PRODUCT_NOT_READY`, tell the user exactly this and stop — do not try fallbacks.

### Transfer flow
Transfers are a two-step flow: authorize first (to pre-flight risk + get a decision), then create with the authorization id.

#### Step 1 — authorize
```bash
curl -sS -X POST "${BASE_URL}/transfer/authorization/create" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "account_id": "ACCOUNT_ID",
    "type": "debit",
    "network": "ach",
    "amount": "150.50",
    "ach_class": "ppd",
    "user": {
      "legal_name": "Jenny Rosen"
    }
  }'
```
`type`: `debit` pulls from the linked Chase account. Plaid Transfer cannot `credit` (push) from Chase to arbitrary destinations — Plaid Transfer debits into Plaid's partner bank, and you disburse from there.
`network`: `ach` or `same-day-ach`.
`ach_class`: `ppd` (consumer), `ccd` (corporate), `web` (internet-initiated).

Response includes `authorization.{id, decision, decision_rationale}`. Only proceed if `decision=approved`.

#### Step 2 — create the transfer
```bash
curl -sS -X POST "${BASE_URL}/transfer/create" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "access_token": "'"${PLAID_ACCESS_TOKEN}"'",
    "authorization_id": "AUTHORIZATION_ID",
    "description": "Invoice 001"
  }'
```
Description must be ≤15 characters (ACH limit).

#### Step 3 — poll status
```bash
curl -sS -X POST "${BASE_URL}/transfer/get" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'"${PLAID_CLIENT_ID}"'",
    "secret": "'"${PLAID_SECRET}"'",
    "transfer_id": "TRANSFER_ID"
  }'
```
Status transitions: `pending` → `posted` → `settled` (or `failed`, `cancelled`, `returned`).

### Before every transfer call
1. Confirm `PLAID_ENV=production` (Transfer does not ship useful sandbox sims).
2. Echo the amount, account mask, ach_class, and description to the user in plain language.
3. Ask for explicit confirmation.
4. Run authorize; if decision ≠ approved, stop and show the rationale.
5. Ask for a second confirmation before running `/transfer/create`.

---

## Section 5: Response Formatting

### Accounts
Markdown table: name, mask (`****1234`), type/subtype, available balance, current balance. Amounts are already in dollars — don't divide.

### Transactions
Markdown table: date, merchant_name (fall back to `name`), amount (with sign), category, pending flag, account mask, id.

### Auth (masked by default)
```
Chase Total Checking (****1234)
  Routing:  021000021
  Account:  ****5678
  Wire:     021000021
```
If the user explicitly asks for the full account number (e.g. "I need it to set up a wire"), you may show it — but warn that it's sensitive and should not be pasted into shared channels.

### Transfer result
```
Transfer created
  ID:         transfer_abc
  Amount:     $150.50 USD
  Type:       debit (pull from Chase ****1234)
  Network:    ach
  Status:     pending
  Settles:    2026-04-16 (estimated)
```

---

## Section 6: Error Handling

Plaid error body shape:
```json
{
  "error_type": "ITEM_ERROR",
  "error_code": "ITEM_LOGIN_REQUIRED",
  "error_message": "the login details of this item have changed",
  "display_message": "The user needs to re-authenticate with their bank.",
  "request_id": "..."
}
```

| `error_code` | Meaning | Action |
|---|---|---|
| `INVALID_API_KEYS` | Wrong `PLAID_CLIENT_ID`/`PLAID_SECRET` | Stop. Ask user to verify env vars. |
| `INVALID_ACCESS_TOKEN` | Token is for a different environment or has been revoked | Stop. Ask user to regenerate via Plaid Link. |
| `ITEM_LOGIN_REQUIRED` | Chase OAuth consent expired or user changed password | Tell the user to re-run Plaid Link. Do not retry. |
| `NO_ACCOUNTS` | Item has no accounts of the requested type | Show to user; they may have linked the wrong account type |
| `PRODUCT_NOT_READY` | Product enabled but data is still loading (first sync) | Wait 30s and retry once |
| `PRODUCT_NOT_ENABLED` | Product not enabled in Plaid dashboard for this environment | Tell the user to enable it in Plaid → Team Settings → API |
| `RATE_LIMIT_EXCEEDED` | Too many calls | Back off 30s and retry once |
| `INTERNAL_SERVER_ERROR` | Plaid side | Retry once |
| `INSTITUTION_DOWN` / `INSTITUTION_NOT_RESPONDING` | Chase is unreachable | Wait and retry later, not an auth issue |

Always show `display_message` (user-friendly) to the user, then `error_code` for debugging.

---

## Section 7: Safety Rules (hard stops)

1. **Never** echo `PLAID_SECRET` or `PLAID_ACCESS_TOKEN` in full. Show only a short prefix if needed.
2. **Never** write credentials to a file, log, or commit.
3. **Never** run a `/transfer/*` call without explicit user confirmation for each step (authorize, then create).
4. **Never** claim this is a "Chase API" — it is Plaid-as-proxy. Be transparent about that if asked.
5. **Never** attempt to scrape chase.com or bypass Plaid for reads. Plaid is the only legitimate path.
6. **Never** retry `ITEM_LOGIN_REQUIRED` errors — the user must re-run Plaid Link, period.
7. **Mask** account numbers in output by default (`****1234`). Only show full values when explicitly requested AND warn about sensitivity.
8. If `item.consent_expiration_time` is within 30 days, proactively warn the user at the start of the session.

## Operation Aliases

- **Read:** `list`, `get`, `show`, `view`, `balance`, `check`
- **Transactions:** `transactions`, `txns`, `history`, `activity`, `spending`
- **Auth:** `auth`, `routing`, `account number`, `ach info`
- **Sync:** `sync`, `update`, `refresh`
- **Transfer:** `transfer`, `debit`, `pull`, `ach pull`
