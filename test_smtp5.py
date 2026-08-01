import os, smtplib, ssl, time

user = os.getenv("SMTP_USER")
pwd = os.getenv("SMTP_PASS")

# Wait for password to propagate
print("Waiting 3s for propagation...")
time.sleep(3)

# Test 1: smtp.zoho.com:587 with ehlo() first, then starttls
print("\n=== smtp.zoho.com:587 (ehlo → starttls → login) ===")
try:
    s = smtplib.SMTP("smtp.zoho.com", 587, timeout=20)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(user, pwd)
    print("OK!")
    s.quit()
except Exception as e:
    print(f"FAIL: {e}")

# Test 2: smtp.zoho.com:465 SSL
print("\n=== smtp.zoho.com:465 (SSL) ===")
try:
    ctx = ssl.create_default_context()
    s = smtplib.SMTP_SSL("smtp.zoho.com", 465, timeout=20, context=ctx)
    s.login(user, pwd)
    print("OK!")
    s.quit()
except Exception as e:
    print(f"FAIL: {e}")
