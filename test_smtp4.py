import os, smtplib, ssl

user = os.getenv("SMTP_USER")
pwd = os.getenv("SMTP_PASS")

print(f"User: {user}, Pass: '{pwd}' len={len(pwd)}")

# Try 587 + STARTTLS
print("\n--- Port 587 + STARTTLS ---")
try:
    s = smtplib.SMTP("smtp.zoho.com", 587, timeout=15)
    s.set_debuglevel(1)
    s.starttls()
    s.login(user, pwd)
    print("AUTH OK!")
    s.quit()
except Exception as e:
    print(f"FAILED: {e}")

# Try 465 + SSL
print("\n--- Port 465 + SSL ---")
try:
    ctx = ssl.create_default_context()
    s = smtplib.SMTP_SSL("smtp.zoho.com", 465, timeout=15, context=ctx)
    s.set_debuglevel(1)
    s.login(user, pwd)
    print("AUTH OK!")
    s.quit()
except Exception as e:
    print(f"FAILED: {e}")
