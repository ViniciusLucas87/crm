import os, httpx, json
k = os.environ['TELNYX_API_KEY']
h = {'Authorization': 'Bearer ' + k}

# Check which connections are linked to each voice profile
for vp_id in ['3010796510133618550', '3009907602906679255']:
    r = httpx.get(f'https://api.telnyx.com/v2/outbound_voice_profiles/{vp_id}', headers=h)
    if r.status_code == 200:
        d = r.json()['data']
        print(f"VP {vp_id}: name={d.get('name')} connections={d.get('connections_count')}")
    r2 = httpx.get(f'https://api.telnyx.com/v2/connections?filter[outbound_voice_profile_id]={vp_id}', headers=h)
    conns = r2.json().get('data', [])
    for c in conns:
        print(f"  Linked to: ID={c['id']} name={c.get('connection_name')} type={c.get('record_type')}")

r3 = httpx.get(f'https://api.telnyx.com/v2/connections/{os.environ["TELNYX_CONNECTION_ID"]}', headers=h)
conn = r3.json()['data']
print(f"\nConnection 3010795094908340043:")
print(f"  outbound_voice_profile_id: {conn.get('outbound_voice_profile_id')}")
print(f"  record_type: {conn.get('record_type')}")
