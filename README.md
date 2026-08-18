# ProspectDialer

A cold-calling CRM for selling websites — styled after the Kixie PowerCall dialer.
Build a big list of numbers, call through them one by one, and sort each business
into outcome categories (Voicemail, Accepted, Picked Up, Callback, …).

Everything runs in your browser. **No server, no login, no install.** Your data
is saved in the browser's `localStorage` on your machine.

## Run it

Just open `caller/index.html` in any modern browser (Chrome/Edge/Safari/Firefox).

Optionally serve it locally so `tel:` links and file drops behave best:

```bash
cd caller
python3 -m http.server 8000
# then open http://localhost:8000
```

## Features

- **Import a big list** — paste rows or upload a CSV. Recognised columns:
  `name, phone, company, title, email, website, notes` (only `phone` is required).
  Headerless lists are auto-detected. Duplicate phone numbers are skipped.
- **Dialpad + call panel** — pick a lead, hit **Call**, and a live talk-time
  timer runs. **Save & Dial Next** logs the outcome and jumps to the next
  un-dialed lead so you keep momentum.
- **Sort after each call** — one-click category chips. Preset categories are
  fully editable (rename, recolor, add, delete) in **⚙ Settings**.
- **Live stats** — Queued / Dialed / Connected / Accepted / total Talk Time.
- **Search & filter** the list by name/company/number or by category.
- **Export CSV** anytime to back up or move your data.

## Calling modes

Set this in **⚙ Settings → Calling mode**.

### 1. Click-to-Call (default, works immediately)
Tapping **Call** opens your device's dialer via a `tel:` link — your phone,
Skype, or softphone places the call. You talk, then log the outcome. Zero setup.

### 2. Twilio Web Dialer (real in-browser audio)
Places the call with audio straight through the browser. This needs a Twilio
account **and** a tiny token server, because Twilio secrets can never live in
front-end code.

**One-time setup:**

1. Create a [Twilio](https://twilio.com) account, buy a phone number, and
   create a [TwiML App](https://www.twilio.com/console/voice/twiml/apps).
2. Deploy a token endpoint (any serverless host — Vercel, Netlify, Cloudflare,
   AWS Lambda). It returns a short-lived access token. Minimal Node version:

   ```js
   // /api/twilio-token  — returns { token }
   const twilio = require("twilio");
   module.exports = (req, res) => {
     const { AccessToken } = twilio.jwt;
     const VoiceGrant = AccessToken.VoiceGrant;
     const token = new AccessToken(
       process.env.TWILIO_ACCOUNT_SID,
       process.env.TWILIO_API_KEY,
       process.env.TWILIO_API_SECRET,
       { identity: "prospectdialer" }
     );
     token.addGrant(new VoiceGrant({
       outgoingApplicationSid: process.env.TWILIO_TWIML_APP_SID,
       incomingAllow: false,
     }));
     res.setHeader("Access-Control-Allow-Origin", "*");
     res.json({ token: token.toJwt() });
   };
   ```

   Your TwiML App's Voice URL should point at a function that dials the `To`
   parameter from your verified caller ID.
3. In **⚙ Settings**, choose **Twilio Web Dialer**, paste your token endpoint
   URL and caller ID. Done — **Call** now rings through the browser, and the
   dialpad sends DTMF tones during a live call.

If Twilio ever fails, ProspectDialer automatically falls back to click-to-call
so you never lose a dial.

## Data & privacy

All leads, notes, and categories live only in your browser. Clearing browser
data (or using **Settings → Delete all**) erases them. Use **Export CSV** to
keep backups. Nothing is ever sent to any server (except Twilio, if you enable it).
