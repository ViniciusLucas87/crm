# Search Engine Registration — Pacific North Systems

**Status**: Google verified; Bing imported | **Last updated**: 2026-08-03

## Google Search Console

### Step 1: Add Property
1. Go to https://search.google.com/search-console
2. Click "Add property"
3. Select "URL prefix"
4. Enter: `https://pacificnorthsystems.com`
5. Click "Continue"

### Step 2: Verify Ownership
Choose one verification method:

**DNS verification (recommended — survives deploys)**:
1. In Search Console, select "Domain name provider" or "DNS record"
2. Copy the TXT record value provided by Google
3. Add a TXT record to your DNS configuration:
   - Host/Name: `@` (or leave blank for apex)
   - Type: `TXT`
   - Value: `<google-site-verification=...>` (the value Google provides)
4. Wait for DNS propagation (typically 5-30 minutes)
5. Click "Verify" in Search Console

**HTML file upload**:
1. Download the HTML verification file from Search Console
2. Place it in `apps/marketing/public/`
3. Deploy the site
4. Click "Verify"

**HTML tag**:
1. Copy the meta tag from Search Console
2. Add to `apps/marketing/src/app/layout.tsx` in the `<head>` section
3. Deploy
4. Click "Verify"

### Step 3: Submit Sitemap
1. In Search Console, navigate to "Sitemaps" (left sidebar)
2. Under "Add a new sitemap", enter: `sitemap.xml`
3. Click "Submit"
4. The sitemap URL should be: `https://pacificnorthsystems.com/sitemap.xml`

### Step 4: Post-Registration Checks
- [ ] Sitemap submitted and shows "Success" status
- [ ] At least some pages discovered/indexed within 48 hours
- [ ] No manual actions or security issues reported
- [ ] "Page indexing" report shows no significant errors
- [ ] "Core Web Vitals" report is populated (may take several days)
- [ ] Set up email notifications for critical issues

---

## Bing Webmaster Tools

### Step 1: Add Site
1. Go to https://www.bing.com/webmasters
2. Sign in with Microsoft account
3. Click "Add a site"
4. Enter: `https://pacificnorthsystems.com`
5. Click "Add"

### Step 2: Verify Ownership
**Option A — Import from Google Search Console (easiest)**:
1. If Google Search Console is already verified, Bing can import verification
2. Click "Import" next to the Google Search Console option

**Option B — DNS verification**:
1. Copy the verification string from Bing
2. Add a CNAME record or TXT record as instructed
3. Wait for propagation and verify

### Step 3: Submit Sitemap
1. Navigate to "Sitemaps" in Bing Webmaster Tools
2. Click "Submit sitemap"
3. Enter: `https://pacificnorthsystems.com/sitemap.xml`
4. Click "Submit"

### Step 4: Post-Registration Checks
- [ ] Sitemap submitted successfully
- [ ] Pages being discovered
- [ ] No significant crawl errors
- [ ] SEO Reports generating data

---

## DNS Verification Options Summary

| Method | Provider | Record Type | Persists Across Deploys |
|---|---|---|---|
| TXT record | Google | TXT | Yes |
| TXT record | Bing | TXT | Yes |
| CNAME record | Bing | CNAME | Yes |
| HTML file | Google | N/A | Yes (in public/) |
| Meta tag | Google | N/A | Yes (in layout) |
| GSC import | Bing | N/A | Yes (after GSC verified) |

**Recommendation**: Use DNS TXT records for both. Add them once and they survive all code deploys and hosting changes.

---

## Quick Reference

- **Google Search Console**: https://search.google.com/search-console
- **Bing Webmaster Tools**: https://www.bing.com/webmasters
- **Sitemap URL**: https://pacificnorthsystems.com/sitemap.xml
- **Robots.txt**: https://pacificnorthsystems.com/robots.txt
