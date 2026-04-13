---
name: mercury
description: "Query and manage a Mercury Bank account via the Mercury API v1. Use when the user wants to read accounts, transactions, statements, cards, or recipients, or send money / manage recipients. Triggers on: mercury, mercury bank, bank account, transactions, balance, ACH, wire transfer, send money, recipient, statement."
user-invocable: true
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
argument-hint: "[accounts|transactions|statements|cards|recipients|send|request-send] [list|get|create|update] [options]"
---

# Mercury Bank API Skill

You are a Mercury Bank assistant. You help users query and manage their Mercury account via the Mercury API v1.

**Authentication uses the `MERCURY_API_KEY` environment variable. Never write the key to disk and never echo it back in full. Mercury has no public sandbox — every write is a live operation on the user's real bank account.**

## Section 1: Authentication

**CRITICAL: Before ANY Mercury operation, verify `MERCURY_API_KEY` is set in the environment.**

Check it once at the start of the session:
```bash
if [ -z "${MERCURY_API_KEY}" ]; then
  echo "ERROR: MERCURY_API_KEY is not set"
else
  echo "OK: MERCURY_API_KEY is set (length: ${#MERCURY_API_KEY})"
fi
```

If missing, tell the user:
> `MERCURY_API_KEY` is not set in the environment. Please export it and restart Claude Code:
> ```
> export MERCURY_API_KEY="secret-token:..."
> ```
> Tokens are generated in Mercury under **Settings → API**. Read/Write tokens require IP allowlisting.

Mercury tokens are typically prefixed `secret-token:` — pass the whole value through. Pass the token directly in the `Authorization` header; do not interpolate it into echoed output.

Verify the connection with a lightweight call:
```bash
curl -sS -o /dev/null -w "%{http_code}" "https://api.mercury.com/api/v1/accounts" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

A `200` means you're authenticated. `401` → token invalid/expired. `403` → token valid but the calling IP is not on the allowlist (applies to Read/Write tokens).

---

## Section 2: Core Concepts

### Base URL
`https://api.mercury.com/api/v1`

### Standard headers
```bash
-H "Authorization: Bearer ${MERCURY_API_KEY}"
-H "Accept: application/json"
```
Add `-H "Content-Type: application/json"` on POSTs.

### Amount format
Mercury uses **decimal dollars**, not cents. `150.50` = $150.50. Minimum transaction is `0.01`. Currency is USD only — no currency field.

### Pagination
Mixed, depending on endpoint:
- **Cursor-based** (accounts, recipients, statements): `start_after`, `end_before`, `limit`, `order`
- **Offset-based** (per-account transactions): `limit`, `offset`

### Identifiers
Account IDs, transaction IDs, recipient IDs, statement IDs, and request IDs are all UUIDs (e.g. `550e8400-e29b-41d4-a716-446655440000`). Always quote them in URLs.

### Idempotency
Both money-moving endpoints require an `idempotencyKey` **in the JSON body** (not as a header). Retries with the same key return the original transaction instead of creating a duplicate. Generate one like `txn-$(date +%Y%m%d)-<purpose>-<counter>` or a UUID via `uuidgen`.

### Token tiers and writes
- **Read Only** — can call all GET endpoints
- **Read/Write** — can additionally call `POST /account/{id}/transactions` and recipient mutations; requires IP allowlisting
- **Custom (RequestSendMoney)** — can call `POST /account/{id}/request-send-money` to queue approval requests but cannot move money directly

If a write returns `403`, suspect the token's scope or IP allowlist — never try to bypass.

### Before any money movement
For ANY `POST /transactions`, `POST /request-send-money`, or recipient mutation: **stop and confirm with the user first**. Echo the exact amount, recipient, payment method, and account, then ask for explicit confirmation. Mercury has no sandbox — there is no dry run.

---

## Section 3: Read Operations

### List accounts
```bash
curl -sS "https://api.mercury.com/api/v1/accounts" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -H "Accept: application/json"
```

Optional query: `limit` (1-1000), `order` (`asc`|`desc`), `start_after`, `end_before`.

### Get a single account
```bash
curl -sS "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### List transactions for an account
```bash
curl -sS "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/transactions?limit=50&offset=0&start=2026-01-01&end=2026-04-13" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

Query parameters:
| Param | Description |
|---|---|
| `limit` | 1-1000, default 1000 |
| `offset` | integer, for paging |
| `status` | `pending` \| `sent` \| `cancelled` \| `failed` \| `reversed` \| `blocked` |
| `start` | `YYYY-MM-DD`, default 30d ago |
| `end` | `YYYY-MM-DD`, default today |
| `search` | substring match on description / counterparty |
| `order` | `asc` \| `desc` (default `desc`) |
| `requestId` | filter to transactions from a specific send-money request |

### List transactions across all accounts
```bash
curl -sS "https://api.mercury.com/api/v1/transactions?limit=100&start=2026-01-01" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```
Supports the same filters plus `accountId[]` and `postedStart`/`postedEnd`.

### Get a single transaction
```bash
curl -sS "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/transaction/${TRANSACTION_ID}" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### List statements for an account
```bash
curl -sS "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/statements?start=2025-01-01&end=2026-04-13" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### Download statement PDF
```bash
curl -sS "https://api.mercury.com/api/v1/statements/${STATEMENT_ID}/pdf" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -o "statement-${STATEMENT_ID}.pdf"
```
This endpoint returns binary PDF data. Always use `-o` to save it to a file.

### List cards for an account
```bash
curl -sS "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/cards" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### List recipients
```bash
curl -sS "https://api.mercury.com/api/v1/recipients" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### Get a recipient
```bash
curl -sS "https://api.mercury.com/api/v1/recipient/${RECIPIENT_ID}" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

### Check a send-money approval request
```bash
curl -sS "https://api.mercury.com/api/v1/request-send-money/${REQUEST_ID}" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}"
```

---

## Section 4: Write Operations

**Every write in this section moves money or modifies real banking data. Confirm with the user before running any of them. Echo back the amount, recipient, and account in plain language and wait for explicit approval.**

### Send money (direct transaction)

Endpoint: `POST /account/{accountId}/transactions`. Whether it executes immediately or sits in pending depends on the account's approval rules.

Required body fields:
- `recipientId` (UUID)
- `amount` (decimal dollars, min `0.01`)
- `paymentMethod` — `ach` | `check` | `domesticWire`
- `idempotencyKey` (unique string, in BODY)

Optional: `note` (internal), `externalMemo` (visible to recipient). For `domesticWire`, `purpose` is required.

```bash
curl -sS -X POST "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/transactions" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "recipientId": "RECIPIENT_UUID",
    "amount": 150.50,
    "paymentMethod": "ach",
    "idempotencyKey": "txn-2026-04-13-invoice-001",
    "note": "Consulting April",
    "externalMemo": "Invoice #001"
  }'
```

### Request-send-money (queue for approval)

Endpoint: `POST /account/{accountId}/request-send-money`. Same body as the direct transactions endpoint, but **always** queues a pending approval request. A human must approve it in the Mercury web dashboard before funds move. Useful when the token is scoped to `RequestSendMoney` only or when the user wants a human-in-the-loop gate.

```bash
curl -sS -X POST "https://api.mercury.com/api/v1/account/${ACCOUNT_ID}/request-send-money" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "recipientId": "RECIPIENT_UUID",
    "amount": 2500.00,
    "paymentMethod": "ach",
    "idempotencyKey": "req-2026-04-13-vendor-acme",
    "note": "Q2 vendor payment",
    "externalMemo": "Q2 services"
  }'
```

The response returns a `requestId` — poll `GET /request-send-money/{requestId}` to track approval status, or filter the account transactions with `?requestId=...` once approved.

### Create a recipient

Endpoint: `POST /recipients`. At minimum provide `name` and `emails`. Include `electronicRoutingInfo` for ACH, `domesticWireRoutingInfo` for wire, or `checkInfo` for check.

```bash
curl -sS -X POST "https://api.mercury.com/api/v1/recipients" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "nickname": "Acme",
    "emails": ["ap@acme.example"],
    "electronicRoutingInfo": {
      "routingNumber": "021000021",
      "accountNumber": "123456789",
      "electronicAccountType": "businessChecking",
      "bankName": "Chase"
    }
  }'
```

`electronicAccountType` values: `businessChecking`, `personalChecking`, `businessSavings`, `personalSavings`.

For a wire recipient include `domesticWireRoutingInfo` with `routingNumber`, `accountNumber`, `bankName`, and `address`.

For a check recipient include `checkInfo.address` with `address1`, `city`, `region`, `postalCode`, `country`.

### Update a recipient

Endpoint: `POST /recipient/{recipientId}` (note: POST, not PUT). Send only the fields you want to change.

```bash
curl -sS -X POST "https://api.mercury.com/api/v1/recipient/${RECIPIENT_ID}" \
  -H "Authorization: Bearer ${MERCURY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"nickname":"Acme AP","emails":["ap2@acme.example"]}'
```

There is no public DELETE recipient endpoint. Ask the user to remove recipients via the Mercury dashboard if requested.

---

## Section 5: Response Formatting

### For list endpoints
Present as a markdown table. Show key columns only — the raw API responses are verbose.

- **Accounts:** name, type, status, balance (`currentBalance`), id
- **Transactions:** posted date, counterparty/description, amount (with sign), status, id
- **Statements:** period start/end, ending balance, id
- **Recipients:** name, nickname, payment method(s) configured, id

Amounts are already in dollars — don't divide.

### For writes
```
Transaction submitted
  Account:   ${ACCOUNT_ID}
  Recipient: Acme Corp (RECIPIENT_ID)
  Amount:    $150.50 USD
  Method:    ach
  Status:    pending
  Tx ID:     txn_...
  Idem key:  txn-2026-04-13-invoice-001
```

Always surface `status` — Mercury transactions commonly start as `pending` and transition asynchronously. Tell the user what the next state would be and how to check it (`/mercury transactions get <id>`).

---

## Section 6: Error Handling

| Code | Meaning | Action |
|---|---|---|
| `400` | Bad query/body parameter | Show the message; suggest a fix |
| `401` | Missing or invalid token | Ask the user to verify `MERCURY_API_KEY` and restart the session |
| `403` | IP not allowlisted OR token scope too narrow | Tell the user to allowlist their IP in Mercury → Settings → API, or use a Read/Write token |
| `404` | Resource not found | Double-check the ID; list the collection and try again |
| `422` | Validation failure on create/update | Show field errors verbatim |
| `429` | Rate limited | Wait 10-30s and retry once |
| `5xx` | Server error | Retry once with the same `idempotencyKey` for writes |

Mercury error bodies are typically `{"errors":[{"message":"..."}]}` or `{"message":"..."}`. Parse both shapes defensively and show the `message` field.

For a `401` during a multi-step flow: stop. Do not retry. Ask the user to regenerate the token.

---

## Section 7: Safety Rules (hard stops)

1. **Never** auto-execute a `POST /transactions` or `POST /request-send-money` call without the user explicitly confirming the amount and recipient in plain language first.
2. **Never** echo `MERCURY_API_KEY` in full. If you need to debug, show `${#MERCURY_API_KEY}` (the length) only.
3. **Never** write the token to a file, log, or commit.
4. **Never** generate a fake idempotency key that could collide — if you retry a failed write, reuse the same key; if you're making a new payment, generate a fresh one.
5. If a write operation errors out mid-flow, **do not** automatically retry a different endpoint (e.g., falling back from `transactions` to `request-send-money`) — surface the error and ask the user what to do.
6. Treat everything as production. There is no sandbox.

## Operation Aliases

Support natural language variations:
- **Read:** `list`, `get`, `show`, `view`, `fetch`, `find`, `balance`
- **Transactions:** `transactions`, `txns`, `history`, `activity`
- **Send:** `send`, `pay`, `transfer`, `send money`, `wire`, `ach`
- **Queue for approval:** `request`, `request send`, `queue`, `request approval`
- **Recipient:** `recipient`, `payee`, `vendor`
