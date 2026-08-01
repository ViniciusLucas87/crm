import smtplib

for host in ["smtp.zoho.com", "smtp.zoho.ca", "smtpmail.zoho.com"]:
    try:
        s = smtplib.SMTP(host, 587, timeout=10)
        code, msg = s.ehlo()
        print(f"OK {host} → {msg.decode()[:80]}")
        s.quit()
    except Exception as e:
        print(f"FAIL {host} → {e}")
