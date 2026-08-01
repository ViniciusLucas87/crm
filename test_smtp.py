import os, smtplib

host = os.getenv("SMTP_HOST", "smtp.zoho.ca")
port = int(os.getenv("SMTP_PORT", "587"))
user = os.getenv("SMTP_USER", "")
pwd = os.getenv("SMTP_PASS", "")

print(f"Host: {host}, User: {user}, Pass len: {len(pwd)}")

try:
    s = smtplib.SMTP(host, port, timeout=15)
    s.set_debuglevel(2)
    s.starttls()
    print("TLS OK")
    s.login(user, pwd)
    print("AUTH OK")
    s.quit()
except Exception as e:
    print(f"FAILED: {e}")
