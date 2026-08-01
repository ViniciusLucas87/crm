import os, httpx, json
k = os.environ['TELNYX_API_KEY']
h = {'Authorization': 'Bearer ' + k}
r = httpx.get('https://api.telnyx.com/v2/connections?page[size]=10', headers=h)
print('Status:', r.status_code)
for d in r.json().get('data', []):
    print(f"  ID={d['id']} name={d.get('connection_name')} type={d.get('record_type')} vp={d.get('outbound_voice_profile_id')}")
