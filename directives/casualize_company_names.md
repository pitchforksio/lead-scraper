# Casualize Company Names Workflow

**description:** Convert formal company names to casual versions for cold email personalization

---

## Overview

This workflow processes a Google Sheet and converts formal company names into casual, friendly versions suitable for cold email outreach. Using casual names makes emails feel more personal and less templated.

---

## Examples

| Formal Name | Casual Name |
|------------|-------------|
| CKJ & Associates LLC | CKJ |
| Johnson Medical Group Inc. | Johnson Medical |
| ABC Technologies Corporation | ABC Technologies |
| The Smith Company | Smith |
| First National Bank | First National |
| Dr. Williams Dental Practice PC | Dr. Williams Dental |
| Thompson & Thompson Law Firm LLP | Thompson & Thompson |
| Summit Real Estate Group | Summit Real Estate |
| Premier Auto Sales, Inc. | Premier Auto |
| Metro Construction Co. | Metro Construction |

---

## Workflow Steps

### 1. Gather Requirements

Ask the user for:
- Google Sheet URL containing leads with company names
- The sheet must have a `company_name` column

### 2. Execute Casualization

Run the script:

```bash
python execution/casualize_company_names_batch.py <<'EOF'
{
    "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"
}
EOF
```

### 3. What the Script Does

1. Opens the Google Sheet
2. Finds the `company_name` column
3. Creates/updates `casual_company_name` column if not present
4. For each row:
   - Reads the formal company name
   - Applies casualization rules
   - Writes the casual version
5. Saves all changes

### 4. Report Results

After completion, report:
- Number of rows processed
- Link to updated Google Sheet
- Sample conversions for review

---

## Script Reference

**Script:** `execution/casualize_company_names_batch.py`

**Input (JSON via stdin):**
```json
{
  "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"
}
```

**Output:**
- Console: Sample conversions and summary
- Google Sheet: Updated with `casual_company_name` column
- JSON result for orchestration

---

## Casualization Rules

The script applies these transformations in order:

### 1. Remove Business Suffixes
- LLC, L.L.C., Limited Liability Company
- Inc, Inc., Incorporated
- Corp, Corp., Corporation
- Ltd, Ltd., Limited
- Co, Co., Company
- LLP, LP, Partnership
- PC, P.C., Professional Corporation
- PLLC, Professional Limited Liability Company
- GmbH, AG, S.A., B.V., etc. (international)

### 2. Remove Generic Terms
- Associates
- Enterprises
- Holdings
- Group (in some contexts)
- Solutions
- Services
- Consulting
- International
- Global
- Worldwide

### 3. Remove Prefixes
- "The" at the beginning

### 4. Preserve Important Descriptors
These words are kept because they're meaningful:
- Medical, Dental, Legal, Law
- Tech, Digital, Creative
- Financial, Insurance
- Real Estate, Realty, Property
- Construction, Engineering, Design
- Marketing, Media
- Health, Wellness, Fitness

### 5. Clean Up
- Remove trailing punctuation
- Remove trailing ampersands
- Normalize whitespace

---

## Testing

You can test the casualization logic without a sheet:

```bash
python execution/casualize_company_names_batch.py --test
```

This prints sample conversions to verify the rules work correctly.

---

## When to Use

**Use casualization when:**
- Preparing cold email campaigns
- Personalizing outreach templates
- Making communications feel more natural

**Run this workflow:**
- After scraping leads
- After enriching leads
- Before exporting to email tools

---

## Troubleshooting

**"Column 'company_name' not found":**
- Check that your sheet has a column named exactly `company_name`
- Column names are case-insensitive

**Strange results:**
- Review the sample conversions shown in output
- Some company names may be unusual
- Manual review recommended for important campaigns

**No changes made:**
- If `casual_company_name` already has values, they won't be overwritten
- Clear the column if you want to regenerate

