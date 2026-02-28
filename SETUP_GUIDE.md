# 🚗 Insurance Quote Engine — Setup Guide

## What This Does
Your team opens one web link → enters 7 client details → hits submit → all 3 carriers
(Good2Go, NatGen, Bristol West) run simultaneously → results appear on screen and get
sent automatically to your WhatsApp team chat. No screenshots. No manual data entry.

---

## Files Included
```
insurance-quoter/
├── app.py                  ← Web server
├── notifications.py        ← WhatsApp sender
├── requirements.txt        ← Python dependencies
├── railway.toml            ← Deployment config
├── quoter/
│   └── engine.py           ← The 3-carrier automation bot
└── static/
    └── index.html          ← Your team's web interface
```

---

## Step 1 — Set Up GitHub (5 minutes)
1. Go to https://github.com and create a free account if you don't have one
2. Click "New repository" → name it `insurance-quoter` → click Create
3. Upload all the files from this folder into that repository

---

## Step 2 — Deploy on Railway (10 minutes)
1. Go to https://railway.app and sign up with your GitHub account
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `insurance-quoter` repository
4. Railway will automatically detect the settings and start deploying

---

## Step 3 — Add Your Credentials (5 minutes)
In Railway, go to your project → Variables tab → Add these one by one:

| Variable Name        | Value                          |
|---------------------|-------------------------------|
| GOOD2GO_USER        | Your Good2Go username          |
| GOOD2GO_PASS        | Your Good2Go password          |
| NATGEN_USER         | Your NatGen username           |
| NATGEN_PASS         | Your NatGen password           |
| BW_USER             | Your Bristol West username     |
| BW_PASS             | Your Bristol West password     |
| TWILIO_ACCOUNT_SID  | (from Step 4 below)            |
| TWILIO_AUTH_TOKEN   | (from Step 4 below)            |
| TWILIO_WHATSAPP_FROM| whatsapp:+14155238886          |
| WHATSAPP_GROUP_TO   | whatsapp:+1XXXXXXXXXX          |

---

## Step 4 — Set Up WhatsApp Notifications (15 minutes)
1. Go to https://twilio.com and create a free account
2. In your Twilio dashboard, find your Account SID and Auth Token
3. Go to Messaging → Try it out → Send a WhatsApp message
4. Follow Twilio's WhatsApp sandbox setup — you'll join a sandbox by texting a code
5. Have your whole team join the sandbox (each person texts the join code once)
6. Get your group's WhatsApp number and add it as WHATSAPP_GROUP_TO

> Note: Twilio's free trial gives you $15 credit which is enough to test.
> For production at 100-150 quotes/day, the paid plan costs ~$0.005/message (~$0.75/day)

---

## Step 5 — Share the Link With Your Team
Once Railway deploys successfully, it gives you a URL like:
`https://insurance-quoter-production.up.railway.app`

Share that link with your entire team. That's it. They bookmark it on their phone
or computer and use it for every quote from now on.

---

## How Your Team Uses It
1. Open the link
2. Fill in: First/Last Name, DOB, Gender, Address, ZIP, License #, Date Licensed, VIN
3. Hit "Run All 3 Quotes Simultaneously"
4. Wait ~2-3 minutes
5. See all 3 rates on screen + screenshots from each carrier
6. Results automatically sent to your WhatsApp group

---

## Important Notes

### The bot needs to be fine-tuned
The automation scripts are built based on the flow you described. However, since
every carrier website uses different HTML element names, the scripts may need minor
adjustments after you see them run for the first time. This is normal for browser
automation and is a one-time fix.

**To fine-tune:** When a carrier fails, Railway shows logs. Share those logs and I'll
fix the exact selectors for that carrier's form fields.

### Running 100-150 quotes/day
At this volume you may want to upgrade to Railway's $20/month Hobby plan for better
performance. The free tier has usage limits.

### Adding a 4th carrier later
Just add a new function to `quoter/engine.py` following the same pattern as the
existing 3, and add it to the `run_all_quotes` function. No other changes needed.

---

## Troubleshooting
- **Bot gets stuck on login:** Carrier may have added a CAPTCHA or changed their login
  flow. Share the error screenshot and I'll fix it.
- **WhatsApp not sending:** Double-check the TWILIO variables and make sure your team
  joined the WhatsApp sandbox.
- **Slow performance:** Upgrade Railway plan or reduce worker concurrency.

---

## Next Steps After This Is Running
Once Phase 1 is stable, we can build:
- **Phase 2:** GHL AI bot that collects client info automatically and triggers quotes
- **Phase 3:** Quote history dashboard with client records
- **Phase 4:** Auto-bind the best rate with one click
