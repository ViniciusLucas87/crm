import os, httpx, json

k = os.environ['TELNYX_API_KEY']
h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'}
cid = os.environ['TELNYX_CONNECTION_ID']
vp_id = '3009907602906679255'  # Pacific North Systems Outbound

# Update connection to link outbound voice profile
payload = {
    'outbound_voice_profile_id': vp_id,
}
r = httpx.patch(f'https://api.telnyx.com/v2/connections/{cid}', json=payload, headers=h)
print(f'Update status: {r.status_code}')
if r.status_code in (200, 202):
    print('Success! Outbound voice profile linked.')
    data = r.json().get('data', {})
    print(f"  New outbound VP: {data.get('outbound_voice_profile_id')}")
else:
    print(f'Error: {r.text[:500]}')
