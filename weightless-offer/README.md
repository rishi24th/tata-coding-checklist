# Calm Body Reset — Deployment Package

## Files
- `index.html` — Sales/landing page (entry point)
- `thank-you.html` — Post-purchase download portal (protected)
- `assets/` — Reserved for any future images or custom CSS/JS

## Before You Deploy

### 1. Set Stripe Redirect URL (MANUAL STEP)
Go to: **Stripe Dashboard → Payment Links → select your link → Settings → After payment**

Set the redirect URL to:
```
https://YOUR-DOMAIN/thank-you.html
```
Stripe will automatically append `?session_id={CHECKOUT_SESSION_ID}` — this is what unlocks the thank-you page.

### 2. Deploy the Site
Upload the entire `weightless-offer/` folder to any static host:

| Host | How |
|------|-----|
| **Netlify** | Drag & drop the folder at netlify.com/drop |
| **Vercel** | `vercel deploy` or connect GitHub repo |
| **Cloudflare Pages** | Connect repo or upload via dashboard |
| **GitHub Pages** | Push to a repo, enable Pages in Settings |

All are free for static HTML sites.

### 3. After Deploy
1. Copy your live domain (e.g. `https://calmbodyreset.netlify.app`)
2. Update the Stripe redirect URL with the real domain
3. Test end-to-end: buy → Stripe redirects → thank-you page loads with downloads visible

## How the Protection Works
`thank-you.html` checks for `?session_id=` in the URL on page load.
- **With** `session_id` → shows all 17 download buttons
- **Without** `session_id` → shows "Access Required" message with link back to `index.html`

> Note: This is a lightweight client-side check. It prevents casual access but is not a substitute for server-side verification. For a more secure delivery, consider a platform like Gumroad, Payhip, or ThriveCart.

## Stripe Payment Link
`https://buy.stripe.com/dRm8wPcframY9Z3bdV2go0P`
