# Code Quality Review Report

**Date:** 2024-12-05  
**Reviewer:** AI Code Reviewer  
**Scope:** All execution scripts in `/execution/`

---

## Summary

- **Total Files Reviewed:** 4
- **Critical Issues:** 2
- **Important Issues:** 5
- **Nice-to-Have Improvements:** 8

---

## 1. google_sheets_auth.py

### ✅ Strengths
- Clear error messages with actionable steps
- Proper OAuth flow implementation
- Token refresh handling
- Directory creation for token storage

### ⚠️ Issues Found

#### Critical
**None**

#### Important
1. **Missing error handling for pickle load** (Line 66)
   - **Issue:** `pickle.load()` can raise exceptions for corrupted files
   - **Impact:** Script crashes if token file is corrupted
   - **Fix:** Wrap in try/except and handle gracefully

2. **No timeout for OAuth flow** (Line 94)
   - **Issue:** `run_local_server()` can hang indefinitely
   - **Impact:** Script may hang if browser doesn't open
   - **Fix:** Add timeout or user prompt

#### Nice-to-Have
1. **Import inside function** (Line 115)
   - **Issue:** `import gspread` inside `verify_connection()` function
   - **Impact:** Minor - should be at top level for consistency
   - **Fix:** Move to top-level imports

---

## 2. scrape_leads.py

### ✅ Strengths
- Comprehensive data normalization
- Good error handling structure
- Test mode implementation
- Batch Google Sheets updates

### ⚠️ Issues Found

#### Critical
1. **Missing wait for Apify actor completion** (Line 120)
   - **Issue:** `client.actor().call()` may return before actor finishes
   - **Impact:** May fetch incomplete results
   - **Fix:** Wait for actor run to complete using `wait_for_finish()` or polling

2. **No timeout for Apify actor run** (Line 120)
   - **Issue:** Actor run could hang indefinitely
   - **Impact:** Script may hang on long-running scrapes
   - **Fix:** Add timeout parameter or polling with max wait time

#### Important
1. **Hardcoded column range** (Line 322)
   - **Issue:** Uses `'A2:Z{end_row}'` - assumes max 26 columns
   - **Impact:** Will fail if SHEET_COLUMNS exceeds 26
   - **Fix:** Calculate end column dynamically: `f'A2:{gspread.utils.rowcol_to_a1(end_row, len(SHEET_COLUMNS))}'`

2. **No validation of Apify actor input** (Line 152-210)
   - **Issue:** `build_actor_input()` doesn't validate required fields
   - **Impact:** May send invalid requests to Apify
   - **Fix:** Add validation for minimum required fields

3. **Potential memory issue with large datasets** (Line 131)
   - **Issue:** `list(client.dataset().iterate_items())` loads all items into memory
   - **Impact:** May cause memory issues with 1000+ leads
   - **Fix:** Process items in batches or use generator

#### Nice-to-Have
1. **Unused import** (Line 22)
   - **Issue:** `time` imported but never used
   - **Fix:** Remove unused import

2. **Magic number** (Line 53-54)
   - **Issue:** Hardcoded lead counts
   - **Fix:** Make configurable via environment variable

3. **Error handling could be more specific** (Line 141-149)
   - **Issue:** Generic `Exception` catch-all
   - **Fix:** Catch specific exceptions (ApifyClientError, etc.)

---

## 3. enrich_leads_bulk.py

### ✅ Strengths
- Rate limiting implementation
- Batch processing
- Good progress reporting
- Handles empty data gracefully

### ⚠️ Issues Found

#### Critical
**None**

#### Important
1. **Incorrect Apollo API endpoint** (Line 164)
   - **Issue:** Uses `/people/match` endpoint - may not be correct for Apollo v1 API
   - **Impact:** API calls may fail
   - **Fix:** Verify correct endpoint (likely `/mixed_people/search` or `/people/match` with correct auth)

2. **API key in request body** (Line 160)
   - **Issue:** Apollo API typically uses header authentication, not body
   - **Impact:** Authentication may fail
   - **Fix:** Use `X-Api-Key` header instead: `headers["X-Api-Key"] = APOLLO_API_KEY`

3. **Rate limit handling too aggressive** (Line 175-176)
   - **Issue:** Waits full 60 seconds on 429, but already has delay between requests
   - **Impact:** Unnecessary delays
   - **Fix:** Use exponential backoff or check rate limit headers

4. **Batch size calculation issue** (Line 326)
   - **Issue:** `batch_size * 5` assumes 5 fields per lead, but actual fields vary
   - **Impact:** May batch update too frequently or not frequently enough
   - **Fix:** Track actual update count per row

#### Nice-to-Have
1. **Missing timeout for requests** (Line 167)
   - **Issue:** Timeout is set but could be configurable
   - **Fix:** Make timeout configurable via parameter

2. **No retry logic for transient failures** (Line 162-184)
   - **Issue:** Network errors cause immediate failure
   - **Fix:** Add retry logic with exponential backoff

3. **Progress updates could be more informative** (Line 335-336)
   - **Issue:** Only shows every 10 rows
   - **Fix:** Show percentage complete

---

## 4. casualize_company_names_batch.py

### ✅ Strengths
- Comprehensive regex patterns
- Handles edge cases well
- Good test function included
- Batch updates for efficiency

### ⚠️ Issues Found

#### Critical
**None**

#### Important
1. **Regex pattern order matters** (Line 41-105)
   - **Issue:** Some patterns may match before more specific ones
   - **Impact:** May incorrectly remove parts of company names
   - **Fix:** Order patterns from most specific to least specific, or use word boundaries more carefully

2. **No validation of company_name before processing** (Line 274)
   - **Issue:** Empty strings, None, or non-string types not validated
   - **Impact:** May cause errors or incorrect results
   - **Fix:** Add type checking and validation

#### Nice-to-Have
1. **Hardcoded sample count** (Line 298)
   - **Issue:** Shows only 10 samples
   - **Fix:** Make configurable or show more

2. **Could use logging instead of print** (Throughout)
   - **Issue:** All scripts use print statements
   - **Fix:** Use Python logging module for better control

---

## Cross-Cutting Issues

### Security
1. **API keys in environment variables** ✅ Good
2. **OAuth tokens stored securely** ✅ Good (pickle file)
3. **No API keys in logs** ✅ Good (checked all print statements)

### Error Handling
1. **Most scripts handle errors well** ✅
2. **Some generic Exception catches** ⚠️ (scrape_leads.py line 141)
3. **Missing specific exception types** ⚠️ (should catch API-specific exceptions)

### Performance
1. **Batch operations used** ✅ Good
2. **Rate limiting implemented** ✅ Good (enrich_leads_bulk.py)
3. **Memory concerns with large datasets** ⚠️ (scrape_leads.py line 131)

### Code Quality
1. **PEP 8 compliance** ✅ Generally good
2. **Docstrings present** ✅ Good
3. **Type hints** ✅ Good
4. **Unused imports** ⚠️ (scrape_leads.py line 22)

---

## Priority Recommendations

### 🔴 Critical (Fix Immediately)
1. **scrape_leads.py Line 120:** Add wait/polling for Apify actor completion
2. **enrich_leads_bulk.py Line 160:** Fix Apollo API authentication (use header, not body)

### 🟡 Important (Fix Soon)
1. **scrape_leads.py Line 322:** Fix hardcoded column range
2. **enrich_leads_bulk.py Line 164:** Verify correct Apollo API endpoint
3. **scrape_leads.py Line 131:** Process leads in batches to avoid memory issues
4. **google_sheets_auth.py Line 66:** Add error handling for corrupted pickle files
5. **casualize_company_names_batch.py Line 274:** Add input validation

### 🟢 Nice-to-Have (Future Improvements)
1. Replace print statements with logging module
2. Add retry logic for network requests
3. Make magic numbers configurable
4. Add more specific exception handling
5. Add unit tests for normalization functions
6. Add progress bars for long operations
7. Add configuration file support
8. Add dry-run mode for testing

---

## Testing Recommendations

1. **Unit Tests Needed:**
   - `normalize_lead()` function (scrape_leads.py)
   - `casualize_company_name()` function (casualize_company_names_batch.py)
   - `extract_sheet_id()` function (multiple files)
   - `build_actor_input()` function (scrape_leads.py)

2. **Integration Tests Needed:**
   - Full scrape workflow with test mode
   - Enrichment workflow with mock Apollo API
   - Google Sheets read/write operations

3. **Edge Cases to Test:**
   - Empty sheets
   - Missing columns
   - Invalid JSON input
   - Network timeouts
   - API rate limits
   - Corrupted token files

---

## Conclusion

Overall code quality is **good** with solid structure and error handling. The main concerns are:
1. Missing wait logic for async Apify operations
2. Incorrect Apollo API authentication method
3. Some memory and performance optimizations needed

Most issues are straightforward fixes that can be implemented quickly.


