import smtplib, os

hosts = ["smtppro.zoho.com", "smtp.zoho.com", "smtp.zoho.ca"]
user = os.environ.get("SMTP_USER", "")
pwd = os.environ.get("SMTP_PASS", "")

for h in hosts:
    try:
        s = smtplib.SMTP(h, 587, timeout=10)
        code, msg = s.ehlo()
        print(f"CONNECT {h} → {msg.decode()[:60]}")
        
        s.starttls()
        s.ehlo()
        print(f"  TLS OK, trying login as {user}...")
        s.login(user, pwd)
        print(f"  AUTH OK!")
        s.quit()
        break
    except smtplib.SMTPAuthenticationError as e:
        print(f"  AUTH FAIL: {e}")
    except Exception as e:
        print(f"  FAIL: {e}")
