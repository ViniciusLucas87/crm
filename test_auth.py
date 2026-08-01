import smtplib, ssl, os

host = os.environ["SMTP_HOST"]
port = int(os.environ["SMTP_PORT"])
user = os.environ["SMTP_USER"]
pwd_present = bool(os.environ.get("SMTP_PASS"))

print(f"host={host} port={port} user={user} password_present={pwd_present}")

try:
    ctx = ssl.create_default_context()
    s = smtplib.SMTP_SSL(host, port, timeout=15, context=ctx)
    s.login(user, os.environ["SMTP_PASS"])
    print("authentication=success")
    s.quit()
except Exception as e:
    print(f"authentication=failure exception={type(e).__name__} error={str(e)[:120]}")
