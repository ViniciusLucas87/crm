#!/bin/sh
echo "=== FILES CHECK ==="
echo "--- telephony routes ---"
ls -la app/presentation/api/v1/routes/telephony.py 2>&1
echo "--- conversations routes ---"
ls -la app/presentation/api/v1/routes/conversations.py 2>&1
echo "--- session manager ---"
ls -la app/application/telephony/session_manager.py 2>&1
echo "--- telnyx provider ---"
ls -la app/application/telephony/telnyx.py 2>&1
echo "--- middleware dir ---"
ls -la app/infrastructure/middleware/ 2>&1
echo "--- clerk auth ---"
ls -la app/infrastructure/auth/clerk.py 2>&1
echo "--- telephony init ---"
ls -la app/application/telephony/__init__.py 2>&1
echo ""
echo "=== ENV CHECK ==="
echo "TELEPHONY_PROVIDER=[$(printenv TELEPHONY_PROVIDER)]"
echo "TELNYX_API_KEY present=[$(if [ -n "$TELNYX_API_KEY" ]; then echo YES; else echo NO; fi)]"
echo "CLERK_ISSUER=[$(printenv CLERK_ISSUER)]"
echo "CLERK_JWKS_URL=[$(printenv CLERK_JWKS_URL)]"
echo "DEEPSEEK_API_KEY present=[$(if [ -n "$DEEPSEEK_API_KEY" ]; then echo YES; else echo NO; fi)]"
echo "TELNYX_APPLICATION_ID=[$(printenv TELNYX_APPLICATION_ID)]"
echo "TELNYX_PHONE_NUMBER=[$(printenv TELNYX_PHONE_NUMBER)]"
echo ""
echo "=== PYTHON CHECK ==="
python -c "
import os
print('CLERK_ISSUER from os.environ:', repr(os.environ.get('CLERK_ISSUER', 'NOT SET')))
print('CLERK_JWKS_URL from os.environ:', repr(os.environ.get('CLERK_JWKS_URL', 'NOT SET')))
print('TELEPHONY_PROVIDER from os.environ:', repr(os.environ.get('TELEPHONY_PROVIDER', 'NOT SET')))
"
echo ""
echo "=== IMAGE ID ==="
cat /proc/self/cgroup 2>/dev/null | head -1
