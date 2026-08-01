import smtplib, os

host = os.environ["SMTP_HOST"]
port = int(os.environ["SMTP_PORT"])
user = os.environ["SMTP_USER"]
pwd = os.environ["SMTP_PASS"]

print(f"Host: {host}, Port: {port}, User: {user}")
try:
    s = smtplib.SMTP(host, port, timeout=15)
    code, msg = s.ehlo()
    print(f"EHLO: {msg.decode()[:80]}")
    s.starttls()
    s.ehlo()
    s.login(user, pwd)
    print("AUTH OK!")
    s.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"AUTH FAIL: {e}")
    # Fallback: try vinidias@ (primary account)
    print("Trying fallback: vinidias@pacificnorthsystems.com...")
    try:
        s2 = smtplib.SMTP(host, port, timeout=15)
        s2.starttls()
        s2.ehlo()
        s2.login("vinidias@pacificnorthsystems.com", pwd)
        print("AUTH OK as vinidias@!")
        s2.quit()
    except Exception as e2:
        print(f"FALLBACK FAIL: {e2}")
except Exception as e:
    print(f"ERROR: {e}")
