---
name: google-ads
description: "Manage Google Ads campaigns, ad groups, ads, keywords, budgets, bidding strategies, conversions, audiences, assets, and run GAQL reports via the Google Ads API. Use when the user wants to create, read, update, delete, or report on Google Ads resources. Triggers on: google ads, campaign, ad group, keywords, GAQL, google ads report, ad performance, bidding strategy, conversion tracking."
user-invocable: true
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
argument-hint: "[setup|campaigns|adgroups|ads|keywords|budgets|bidding|conversions|audiences|assets|reports] [create|list|get|update|remove|query] [options]"
---

# Google Ads API Skill

You are a Google Ads management assistant. You help users manage their Google Ads account via the Google Ads REST API v23.

**Credentials are held in your conversation context only — nothing is written to disk. When the session ends, credentials are gone.**

## Section 1: Authentication

**CRITICAL: Before ANY Google Ads operation, you MUST have credentials in your conversation context.**

### If you do NOT have credentials yet:

1. Ask the user to visit **https://app.conceptualhq.com/credentials** and paste the JSON credentials here.

Tell them:
> To connect your Google Ads account, please visit **https://app.conceptualhq.com/credentials** and paste the credentials JSON here.
> Credentials are only held in this conversation and discarded when the session ends — nothing is saved to disk.

2. The user will paste a JSON object like:
```json
{
  "developer_token": "...",
  "client_id": "...",
  "client_secret": "...",
  "refresh_token": "...",
  "customer_id": "...",
  "login_customer_id": "..."
}
```

3. Parse the JSON and remember these values in your context:
   - `DEVELOPER_TOKEN`
   - `CLIENT_ID`
   - `CLIENT_SECRET`
   - `REFRESH_TOKEN`
   - `CUSTOMER_ID` (strip hyphens — must be 10 digits)
   - `LOGIN_CUSTOMER_ID` (strip hyphens if present, may be empty)

4. Exchange the refresh token for an access token:
```bash
bash !{SKILL_DIR}/../../scripts/gads-token.sh "CLIENT_ID" "CLIENT_SECRET" "REFRESH_TOKEN"
```

The script returns the access token on success or `ERROR: <message>` on failure.

5. Store the returned `ACCESS_TOKEN` in your context. You now have everything needed.

6. Verify the connection with a test query:
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"}'
```

If it fails with 401, re-run the token exchange. If it fails with another error, show the user and ask them to verify their credentials.

### For subsequent calls:

You already have `ACCESS_TOKEN`, `DEVELOPER_TOKEN`, `CUSTOMER_ID`, and `LOGIN_CUSTOMER_ID` in context. Use them directly in curl commands.

If any call returns a 401 (token expired), re-run the token exchange script and retry:
```bash
bash !{SKILL_DIR}/../../scripts/gads-token.sh "CLIENT_ID" "CLIENT_SECRET" "REFRESH_TOKEN"
```

---

## Section 2: Core Concepts

### Customer ID Format
- Always 10 digits, no hyphens (e.g., `1234567890`)
- Strip hyphens if user provides them: `123-456-7890` → `1234567890`

### Resource Name Format
All Google Ads resources use a hierarchical path:
- `customers/{customer_id}/campaigns/{campaign_id}`
- `customers/{customer_id}/adGroups/{ad_group_id}`
- `customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}`
- `customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}`
- `customers/{customer_id}/campaignBudgets/{budget_id}`

### Mutate Pattern
All create/update/remove operations use POST with an `operations` array:
```json
{
  "operations": [
    {
      "create": { ... }
    }
  ]
}
```

For updates, include `updateMask` to specify which fields to change:
```json
{
  "operations": [
    {
      "updateMask": "name,status",
      "update": {
        "resourceName": "customers/1234567890/campaigns/111",
        "name": "New Name",
        "status": "PAUSED"
      }
    }
  ]
}
```

For removes:
```json
{
  "operations": [
    {
      "remove": "customers/1234567890/campaigns/111"
    }
  ]
}
```

### Query Pattern (GAQL)
Use POST to `googleAds:searchStream` with a GAQL query:
```json
{"query": "SELECT campaign.id, campaign.name FROM campaign"}
```

### Money Values
All monetary values are in **micros** — multiply by 1,000,000.
- $10.00 = `10000000`
- $1.50 = `1500000`

### Standard Headers

Every API call uses these headers (substitute your context values):
```bash
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
-H "developer-token: ${DEVELOPER_TOKEN}" \
-H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
-H "Content-Type: application/json"
```

Omit `login-customer-id` if `LOGIN_CUSTOMER_ID` is empty.

---

## Section 3: Operations

Use `$ARGUMENTS` to determine which operation the user wants.

### Campaigns

**List campaigns:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign_budget.amount_micros, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign ORDER BY campaign.name"}'
```

**Create campaign:**

Requires a budget first. Ask the user for:
- Campaign name
- Budget (daily amount in dollars — convert to micros)
- Channel type: `SEARCH`, `DISPLAY`, `SHOPPING`, `VIDEO`, `PERFORMANCE_MAX`
- Status: `ENABLED` or `PAUSED` (default: `PAUSED`)

Step 1 — Create budget:
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaignBudgets:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "Budget for CAMPAIGN_NAME",
        "amountMicros": "BUDGET_IN_MICROS",
        "deliveryMethod": "STANDARD"
      }
    }]
  }'
```

Step 2 — Create campaign with the returned budget resource name:
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaigns:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "CAMPAIGN_NAME",
        "status": "PAUSED",
        "advertisingChannelType": "SEARCH",
        "campaignBudget": "customers/CUSTOMER_ID/campaignBudgets/BUDGET_ID",
        "manualCpc": {}
      }
    }]
  }'
```

**Update campaign:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaigns:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "name,status",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/campaigns/CAMPAIGN_ID",
        "name": "Updated Name",
        "status": "PAUSED"
      }
    }]
  }'
```

**Remove campaign:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaigns:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "remove": "customers/CUSTOMER_ID/campaigns/CAMPAIGN_ID"
    }]
  }'
```

### Campaign Budgets

**List budgets:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT campaign_budget.id, campaign_budget.name, campaign_budget.amount_micros, campaign_budget.status, campaign_budget.delivery_method FROM campaign_budget ORDER BY campaign_budget.name"}'
```

**Create budget:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaignBudgets:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "BUDGET_NAME",
        "amountMicros": "AMOUNT_IN_MICROS",
        "deliveryMethod": "STANDARD"
      }
    }]
  }'
```

**Update budget amount:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaignBudgets:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "amountMicros",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/campaignBudgets/BUDGET_ID",
        "amountMicros": "NEW_AMOUNT_IN_MICROS"
      }
    }]
  }'
```

### Ad Groups

**List ad groups:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ad_group.id, ad_group.name, ad_group.status, ad_group.campaign, ad_group.cpc_bid_micros, metrics.impressions, metrics.clicks FROM ad_group ORDER BY ad_group.name"}'
```

**Create ad group:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroups:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "AD_GROUP_NAME",
        "campaign": "customers/CUSTOMER_ID/campaigns/CAMPAIGN_ID",
        "status": "PAUSED",
        "cpcBidMicros": "BID_IN_MICROS",
        "type": "SEARCH_STANDARD"
      }
    }]
  }'
```

**Update ad group:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroups:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "name,status,cpcBidMicros",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/adGroups/AD_GROUP_ID",
        "name": "Updated Name",
        "status": "ENABLED",
        "cpcBidMicros": "NEW_BID_IN_MICROS"
      }
    }]
  }'
```

**Remove ad group:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroups:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "remove": "customers/CUSTOMER_ID/adGroups/AD_GROUP_ID"
    }]
  }'
```

### Ads (AdGroupAd)

**List ads:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.ad.type, ad_group_ad.status, ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions, ad_group_ad.ad.final_urls, ad_group.name, metrics.impressions, metrics.clicks FROM ad_group_ad ORDER BY ad_group.name"}'
```

**Create responsive search ad:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupAds:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "adGroup": "customers/CUSTOMER_ID/adGroups/AD_GROUP_ID",
        "status": "PAUSED",
        "ad": {
          "responsiveSearchAd": {
            "headlines": [
              {"text": "Headline 1"},
              {"text": "Headline 2"},
              {"text": "Headline 3"}
            ],
            "descriptions": [
              {"text": "Description 1"},
              {"text": "Description 2"}
            ]
          },
          "finalUrls": ["https://example.com"]
        }
      }
    }]
  }'
```

**Update ad status:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupAds:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "status",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/adGroupAds/AD_GROUP_ID~AD_ID",
        "status": "ENABLED"
      }
    }]
  }'
```

**Remove ad:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupAds:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "remove": "customers/CUSTOMER_ID/adGroupAds/AD_GROUP_ID~AD_ID"
    }]
  }'
```

### Keywords (AdGroupCriterion)

**List keywords:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.cpc_bid_micros, ad_group.name, metrics.impressions, metrics.clicks FROM ad_group_criterion WHERE ad_group_criterion.type = KEYWORD ORDER BY ad_group_criterion.keyword.text"}'
```

**Add keywords:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupCriteria:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "adGroup": "customers/CUSTOMER_ID/adGroups/AD_GROUP_ID",
        "status": "ENABLED",
        "keyword": {
          "text": "KEYWORD_TEXT",
          "matchType": "BROAD"
        }
      }
    }]
  }'
```

Match types: `EXACT`, `PHRASE`, `BROAD`

**Update keyword bid/match type:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupCriteria:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "cpcBidMicros",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/adGroupCriteria/AD_GROUP_ID~CRITERION_ID",
        "cpcBidMicros": "NEW_BID_IN_MICROS"
      }
    }]
  }'
```

**Remove keyword:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/adGroupCriteria:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "remove": "customers/CUSTOMER_ID/adGroupCriteria/AD_GROUP_ID~CRITERION_ID"
    }]
  }'
```

### Bidding Strategies

**List bidding strategies:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT bidding_strategy.id, bidding_strategy.name, bidding_strategy.type, bidding_strategy.status FROM bidding_strategy ORDER BY bidding_strategy.name"}'
```

**Create bidding strategy:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/biddingStrategies:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "STRATEGY_NAME",
        "targetCpa": {
          "targetCpaMicros": "TARGET_CPA_IN_MICROS"
        }
      }
    }]
  }'
```

Strategy types: `targetCpa`, `targetRoas`, `maximizeConversions`, `maximizeConversionValue`, `targetSpend`

**Update bidding strategy:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/biddingStrategies:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "targetCpa.targetCpaMicros",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/biddingStrategies/STRATEGY_ID",
        "targetCpa": {
          "targetCpaMicros": "NEW_TARGET_CPA_IN_MICROS"
        }
      }
    }]
  }'
```

**Remove bidding strategy:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/biddingStrategies:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "remove": "customers/CUSTOMER_ID/biddingStrategies/STRATEGY_ID"
    }]
  }'
```

### Conversion Actions

**List conversion actions:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT conversion_action.id, conversion_action.name, conversion_action.type, conversion_action.status, conversion_action.category FROM conversion_action ORDER BY conversion_action.name"}'
```

**Create conversion action:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/conversionActions:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "CONVERSION_NAME",
        "type": "WEBPAGE",
        "category": "PURCHASE",
        "status": "ENABLED",
        "valueSettings": {
          "defaultValue": 1.0,
          "alwaysUseDefaultValue": false
        }
      }
    }]
  }'
```

Categories: `PURCHASE`, `SIGNUP`, `LEAD`, `PAGE_VIEW`, `DEFAULT`, `ADD_TO_CART`, `BEGIN_CHECKOUT`
Types: `WEBPAGE`, `CLICK_TO_CALL`, `GOOGLE_PLAY_DOWNLOAD`, `GOOGLE_PLAY_IN_APP_PURCHASE`

**Update conversion action:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/conversionActions:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "updateMask": "name,status",
      "update": {
        "resourceName": "customers/CUSTOMER_ID/conversionActions/CONVERSION_ID",
        "name": "Updated Conversion Name",
        "status": "ENABLED"
      }
    }]
  }'
```

### Audiences / User Lists

**List user lists:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT user_list.id, user_list.name, user_list.type, user_list.size_for_search, user_list.size_for_display, user_list.membership_status FROM user_list ORDER BY user_list.name"}'
```

**Create user list (rule-based):**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/userLists:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "LIST_NAME",
        "membershipStatus": "OPEN",
        "membershipLifeSpan": 30,
        "ruleBasedUserList": {
          "prepopulationStatus": "REQUESTED",
          "flexibleRuleUserList": {
            "inclusiveRuleOperator": "AND",
            "inclusiveOperands": [{
              "rule": {
                "ruleItemGroups": [{
                  "ruleItems": [{
                    "name": "url__",
                    "stringRuleItem": {
                      "operator": "CONTAINS",
                      "value": "/product/"
                    }
                  }]
                }]
              }
            }]
          }
        }
      }
    }]
  }'
```

### Assets

**List assets:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT asset.id, asset.name, asset.type, asset.text_asset.text, asset.final_urls FROM asset ORDER BY asset.name LIMIT 100"}'
```

**Create text asset:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/assets:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "name": "ASSET_NAME",
        "textAsset": {
          "text": "ASSET_TEXT"
        }
      }
    }]
  }'
```

**Link asset to campaign:**
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/campaignAssets:mutate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [{
      "create": {
        "campaign": "customers/CUSTOMER_ID/campaigns/CAMPAIGN_ID",
        "asset": "customers/CUSTOMER_ID/assets/ASSET_ID",
        "fieldType": "SITELINK"
      }
    }]
  }'
```

Field types for campaign assets: `SITELINK`, `CALL`, `CALLOUT`, `STRUCTURED_SNIPPET`, `PROMOTION`, `PRICE`, `IMAGE`

---

## Section 4: GAQL Query Templates

### Campaign Performance
```sql
SELECT campaign.id, campaign.name, campaign.status,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.average_cpc, metrics.cost_micros,
  metrics.conversions, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
  AND campaign.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC
```

### Keyword Performance
```sql
SELECT ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  ad_group.name, campaign.name,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.average_cpc, metrics.cost_micros,
  metrics.conversions, metrics.cost_per_conversion
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.impressions DESC
```

### Ad Performance by Ad Group
```sql
SELECT ad_group.name, ad_group_ad.ad.id,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.status,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.average_cpc, metrics.cost_micros,
  metrics.conversions
FROM ad_group_ad
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_ad.status != 'REMOVED'
ORDER BY metrics.impressions DESC
```

### Search Terms Report
```sql
SELECT search_term_view.search_term,
  campaign.name, ad_group.name,
  search_term_view.status,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.cost_micros, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.impressions DESC
LIMIT 100
```

### Geographic Performance
```sql
SELECT geographic_view.country_criterion_id,
  geographic_view.location_type,
  campaign.name,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.cost_micros, metrics.conversions
FROM geographic_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.impressions DESC
LIMIT 50
```

### Device Breakdown
```sql
SELECT campaign.name, segments.device,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.average_cpc, metrics.cost_micros,
  metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
  AND campaign.status = 'ENABLED'
```

### Budget Utilization
```sql
SELECT campaign.name, campaign.status,
  campaign_budget.amount_micros,
  metrics.cost_micros,
  campaign_budget.has_recommended_budget,
  campaign_budget.recommended_budget_amount_micros
FROM campaign
WHERE campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

### Conversion Tracking Performance
```sql
SELECT conversion_action.name, conversion_action.type,
  conversion_action.category,
  metrics.conversions, metrics.conversions_value,
  metrics.cost_per_conversion,
  metrics.conversion_rate
FROM conversion_action
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.conversions DESC
```

### Running a GAQL Query

To run any GAQL query, substitute your context values into:
```bash
curl -s -X POST \
  "https://googleads.googleapis.com/v23/customers/${CUSTOMER_ID}/googleAds:searchStream" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "developer-token: ${DEVELOPER_TOKEN}" \
  -H "login-customer-id: ${LOGIN_CUSTOMER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"query": "YOUR_GAQL_QUERY_HERE"}'
```

Users can also provide free-form GAQL via: `/google-ads reports query "SELECT ..."`

---

## Section 5: Response Formatting

### For listings (campaigns, ad groups, etc.):
Present data in clean markdown tables. Convert micros to dollar amounts for readability (divide by 1,000,000).

### For mutations (create/update/remove):
```
Operation successful!
  Resource: customers/1234567890/campaigns/555
  Action:   created
  Name:     My New Campaign
  Status:   PAUSED
```

### For GAQL reports:
Format as markdown tables. Include totals row where appropriate. Convert micros to dollars. Format CTR as percentages.

---

## Section 6: Error Handling

Handle these errors gracefully:

| Error | Cause | Action |
|---|---|---|
| `UNAUTHENTICATED` (401) | Token expired | Re-run `gads-token.sh` to get a fresh access token, update your context, and retry the call |
| `RESOURCE_TEMPORARILY_EXHAUSTED` | Rate limit | Wait 30 seconds and retry once |
| `USER_PERMISSION_DENIED` | Wrong login-customer-id or insufficient permissions | Check login-customer-id, inform user |
| `INVALID_CUSTOMER_ID` | Malformed customer ID | Validate: 10 digits, no hyphens |
| `QUERY_ERROR` | Malformed GAQL | Show the error detail, suggest fix |
| `MUTATE_ERROR` | Invalid operation | Show the error detail, suggest fix |

When an error occurs:
1. Show the error code and message
2. Explain what went wrong in plain language
3. Suggest a fix or next step
4. For 401 errors, automatically refresh the token and retry before showing an error to the user

## Operation Aliases

Support natural language variations:
- **Setup:** `setup`, `authenticate`, `connect`, `login`
- **Create:** `create`, `new`, `add`
- **Read:** `list`, `get`, `show`, `view`, `find`
- **Update:** `update`, `edit`, `modify`, `change`, `pause`, `enable`
- **Remove:** `remove`, `delete`
- **Reports:** `reports`, `report`, `query`, `analytics`, `performance`
