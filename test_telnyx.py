import asyncio, os, httpx
async def test():
    async with httpx.AsyncClient(
        base_url='https://api.telnyx.com/v2',
        headers={'Authorization': f'Bearer {os.environ[\"TELNYX_API_KEY\"]}', 'Content-Type': 'application/json'}
    ) as c:
        r = await c.post('/telephony_credentials', json={'connection_id': os.environ['TELNYX_CONNECTION_ID']})
        print('Status:', r.status_code)
        print('Body:', r.text[:2000])
asyncio.run(test())
