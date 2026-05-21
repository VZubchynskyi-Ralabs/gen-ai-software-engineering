import csv, json

categories = ["account_access","technical_issue","billing_question","feature_request","bug_report","other"]
priorities = ["urgent","high","medium","low"]
statuses = ["new","in_progress","waiting_customer","resolved","closed"]
sources = ["web_form","email","api","chat","phone"]
devices = ["desktop","mobile","tablet"]

subjects = [
    "Cannot login to my account",
    "Password reset not working",
    "Invoice amount is incorrect",
    "App crashes on startup",
    "Feature request: dark mode",
    "Bug in payment flow",
    "How do I upgrade my plan",
    "Critical production is down",
    "Security breach detected",
    "Minor cosmetic issue in UI",
    "Suggestion for new dashboard",
    "Error 500 on checkout",
    "Account locked after failed attempts",
    "Refund not processed",
    "2FA not sending code",
    "Connection timeout on API",
    "ASAP blocking our release",
    "Wrong charge on credit card",
    "Please add CSV export",
    "Login fails with specific email",
    "Billing question about enterprise plan",
    "Need help with account access",
    "Technical issue with integrations",
    "Feature request: mobile app support",
    "Bug report: data corruption on save",
    "Cannot access admin panel",
    "Payment declined but money taken",
    "Enhancement: add bulk operations",
    "Application is very slow to load",
    "Incorrect invoice amount charged",
    "Login page not loading on Chrome",
    "Minor suggestion for UX improvement",
    "Error in report generation module",
    "Account deactivated unexpectedly",
    "Subscription renewal failed",
    "Important: API endpoints broken",
    "Data export feature request",
    "Incorrect behavior in search",
    "Password policy question",
    "Critical security vulnerability found",
    "Feature suggestion: add webhooks",
    "Invoice PDF not generating correctly",
    "Cannot change email address in profile",
    "Crash on mobile device when uploading",
    "Billing plan options are confusing",
    "Bug: table sorting not working",
    "ASAP fix needed for production auth",
    "Wrong device type shown in dashboard",
    "Two-factor authentication issue",
    "Nice to have: custom themes option",
    "Server error on large file upload",
]

descriptions = [
    "I cannot login to my account since yesterday. The error message says invalid credentials but I am sure my password is correct.",
    "The password reset email never arrives even after multiple attempts. This is blocking me from accessing my account.",
    "My latest invoice shows a charge of $200 but I should only be charged $150 according to my plan.",
    "The application crashes immediately when I try to open it on Windows 10. It shows an exception error.",
    "It would be really nice to have a dark mode option to reduce eye strain during night work.",
    "When checking out, the payment fails with a 500 server error. Steps to reproduce: add item to cart, click checkout, enter card details.",
    "I want to upgrade from Basic to Pro plan but cannot find the option in my account settings.",
    "CRITICAL: Our production environment is completely down. All users are affected. Need immediate assistance.",
    "We detected suspicious login attempts from unknown IP addresses. Possible security breach detected.",
    "The button alignment on the settings page is slightly off. Minor cosmetic issue but would be nice to fix.",
    "Would suggest adding a customizable dashboard with drag and drop widgets for better productivity.",
    "Getting 500 error on the checkout page. This is happening consistently for all users in our team.",
    "After 5 failed login attempts my account got locked and the unlock email is not arriving in inbox.",
    "I requested a refund 2 weeks ago but it has not been processed yet. Billing order ID is 12345.",
    "The two-factor authentication code is not being sent to my phone number anymore after update.",
    "The API is timing out after 30 seconds on all endpoints. Our integration is completely broken.",
    "This bug is blocking our entire release. ASAP fix needed for the authentication module today.",
    "I was charged $50 instead of $25 this month. Please check my billing and refund the difference.",
    "Please add the ability to export data as CSV format. This would greatly improve our daily workflow.",
    "Login fails when using an email with plus sign. Steps: use email user+tag@domain.com enter correct password click login.",
    "I have a billing question about the enterprise plan pricing and what features are included in it.",
    "Cannot access my admin panel after the recent system update. Getting access denied error on every page.",
    "There are technical issues with our third party integrations after the latest API update this week.",
    "A mobile app would be very useful for our team members who frequently work remotely from home.",
    "Found a critical bug that causes data corruption when saving large records over 5MB. Actual behavior is data loss.",
    "I cannot access the admin panel anymore. It redirects me to the login page repeatedly in a loop.",
    "My payment was declined but the money was actually charged from my account. Need urgent assistance.",
    "It would be great to have bulk operations for managing multiple items at once instead of one by one.",
    "The application has become very slow over the past week. Loading times now exceed 30 seconds per page.",
    "The invoice amount is incorrect. Expected to be charged $100 but was actually charged $150 this cycle.",
    "The login page is not loading on Chrome browser version 120. It shows a blank white screen only.",
    "Minor suggestion: the font size in the sidebar navigation could be slightly larger for better readability.",
    "Getting error in report generation module. The report fails to generate for date ranges over 30 days.",
    "My account was unexpectedly deactivated today. I did not request this and need immediate access restored.",
    "The subscription auto-renewal failed and now my account is showing as expired and features are locked.",
    "Important: the API endpoints for user management are all returning 401 errors blocking our integration.",
    "Please add a data export feature that supports multiple formats including JSON and XML and PDF.",
    "The search functionality returns incorrect results when using special characters in the search query.",
    "What is the password policy for new accounts? I cannot find this information in the documentation.",
    "Critical security vulnerability found in the authentication system. Needs immediate urgent attention.",
    "Feature suggestion: add webhook support so we can integrate with our event-driven microservices.",
    "The invoice PDF is not generating correctly. Some important fields are missing and layout is broken.",
    "I cannot change my email address in the profile settings page. The save button does absolutely nothing.",
    "App crashes on my Android device when I try to upload a profile picture from my photo gallery.",
    "I am confused about what features are included in each billing plan. The pricing page is not clear.",
    "Bug: the table sorting functionality is not working correctly for date columns in the main table.",
    "ASAP: our production environment needs an urgent fix for the authentication service failure today.",
    "The device type shown in my dashboard is wrong. It shows mobile but I am clearly using a desktop.",
    "The two-factor authentication is not working properly. The QR code scanning consistently fails.",
    "It would be nice to have custom themes for the interface. This is a low priority improvement suggestion.",
    "Getting a server error when uploading files larger than 10MB. The upload fails silently with no message.",
]

rows = []
for i in range(50):
    rows.append({
        "customer_id": f"CUST-{1000+i}",
        "customer_email": f"user{i+1}@example.com",
        "customer_name": f"Customer {i+1}",
        "subject": subjects[i % len(subjects)],
        "description": descriptions[i % len(descriptions)],
        "category": categories[i % len(categories)],
        "priority": priorities[i % len(priorities)],
        "status": statuses[i % len(statuses)],
        "source": sources[i % len(sources)],
        "browser": "Chrome",
        "device_type": devices[i % len(devices)],
        "tags": f"tag{i%5},tag{(i+1)%5}",
        "assigned_to": f"agent{(i%3)+1}@support.com" if i % 3 != 0 else "",
    })

# CSV (50 tickets)
fields = ["customer_id","customer_email","customer_name","subject","description",
          "category","priority","status","source","browser","device_type","tags","assigned_to"]
with open("tests/fixtures/sample_tickets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# JSON (20 tickets)
json_tickets = []
for r in rows[:20]:
    t = dict(r)
    t["tags"] = [tg for tg in r["tags"].split(",") if tg]
    t["metadata"] = {
        "source": t.pop("source"),
        "browser": t.pop("browser"),
        "device_type": t.pop("device_type"),
    }
    json_tickets.append(t)
with open("tests/fixtures/sample_tickets.json", "w") as f:
    json.dump({"tickets": json_tickets}, f, indent=2)

# XML (30 tickets)
lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<tickets>']
for r in rows[:30]:
    lines.append('  <ticket>')
    for k, v in r.items():
        if k == "tags":
            lines.append('    <tags>')
            for tg in v.split(","):
                if tg.strip():
                    lines.append(f'      <tag>{tg.strip()}</tag>')
            lines.append('    </tags>')
        elif k in ("source", "browser", "device_type"):
            pass
        else:
            safe_v = str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            lines.append(f'    <{k}>{safe_v}</{k}>')
    lines.append('    <metadata>')
    lines.append(f'      <source>{r["source"]}</source>')
    lines.append(f'      <browser>{r["browser"]}</browser>')
    lines.append(f'      <device_type>{r["device_type"]}</device_type>')
    lines.append('    </metadata>')
    lines.append('  </ticket>')
lines.append('</tickets>')
with open("tests/fixtures/sample_tickets.xml", "w") as f:
    f.write("\n".join(lines))

# Invalid CSV
with open("tests/fixtures/invalid_tickets.csv", "w") as f:
    f.write("customer_id,customer_email\n")
    f.write("CUST-999,not-an-email\n")
    f.write(",\n")

# Invalid JSON
with open("tests/fixtures/invalid_tickets.json", "w") as f:
    f.write('{"tickets": [{"customer_id": "X", "customer_email": "bad-email", "subject": "Hi"}]}')

# Invalid XML — unclosed tag
with open("tests/fixtures/invalid_tickets.xml", "w") as f:
    f.write('<tickets><ticket><customer_id>X</customer_id></ticket><unclosed>')

print("All fixtures created OK")
print(f"CSV rows: 50, JSON tickets: 20, XML tickets: 30")

