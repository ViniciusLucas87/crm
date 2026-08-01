import smtplib

pwd = "1ev7rYbyqyeR"

for user in ["vinidias@pacificnorthsystems.com", "hello@pacificnorthsystems.com"]:
    try:
        s = smtplib.SMTP("smtp.zoho.com", 587, timeout=15)
        s.starttls()
        s.login(user, pwd)
        print(f"AUTH OK as {user}!")
        s.quit()
        break
    except Exception as e:
        print(f"AUTH FAIL as {user}: {e}")
