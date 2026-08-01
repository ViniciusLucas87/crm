import httpx, json

# Check existing contacts for company 9
r = httpx.get('http://localhost:8000/api/v1/contacts?company_id=9&page_size=20')
print('Status:', r.status_code)
if r.status_code == 200:
    items = r.json().get('items', [])
    print(f'Found {len(items)} contacts')
    for c in items:
        print(f"  ID={c.get('id')}: {c.get('first_name')} {c.get('last_name')} phone={c.get('phone')} mobile={c.get('mobile')}")
else:
    print(r.text[:500])
