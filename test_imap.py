import imaplib, smtplib, ssl

user = "vinidias@pacificnorthsystems.com"
pwd = "1ev7rYbyqyeR"

# Test IMAP
print("=== IMAP imap.zoho.com:993 ===")
try:
    ctx = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL("imap.zoho.com", 993, ssl_context=ctx, timeout=15)
    imap.login(user, pwd)
    print("IMAP OK!")
    imap.logout()
except Exception as e:
    print(f"IMAP FAIL: {e}")

# Test SMTP one more time with explicit AUTH LOGIN
print("\n=== SMTP smtp.zoho.com:587 (explicit AUTH LOGIN) ===")
try:
    s = smtplib.SMTP("smtp.zoho.com", 587, timeout=15)
    s.ehlo()
    s.starttls()
    s.ehlo()
    # Try AUTH LOGIN explicitly (base64 encoded)
    import base64
    s.docmd("AUTH LOGIN")
    s.docmd(base64.b64encode(user.encode()).decode())
    code, msg = s.docmd(base64.b64encode(pwd.encode()).decode())
    print(f"SMTP response: {code} {msg.decode()}")
    s.quit()
except Exception as e:
    print(f"SMTP FAIL: {e}")
