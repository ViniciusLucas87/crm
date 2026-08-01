import os, smtplib

host = "smtp.zoho.com"
user = os.getenv("SMTP_USER")
pwd = os.getenv("SMTP_PASS")

print(f"Host: {host}, User: {user}, Pass len: {len(pwd)}")

try:
    s = smtplib.SMTP(host, 587, timeout=15)
    s.starttls()
    s.login(user, pwd)
    print("AUTH OK!")
    s.quit()
except Exception as e:
    print(f"FAILED: {e}")
