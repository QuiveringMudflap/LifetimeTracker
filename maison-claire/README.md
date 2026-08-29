# Maison Claire — Website

Multi-page static site for Maison Claire (Natural Healing • Higher Wellbeing • A Brighter You),
a root-cause healing practice with Stanislava offering Reiki, hypnotherapy, intuitive
guidance, liver cleanse & detox, and root cause healing.

## Pages
- `/` Home
- `/about` About + Stanislava
- `/services` Services hub
- `/reiki-healing`, `/hypnotherapy-intuitive-guidance`, `/liver-cleanse-detox`, `/root-cause-healing` service detail pages
- `/faq` FAQ (with FAQ structured data)
- `/contact` Booking / contact

## How it's built
Pages are generated from a single template so the header, footer, and SEO `<head>`
stay identical across the whole site. To change structure, nav, or shared copy:

1. Edit `build.py`
2. Run `python3 build.py` (needs Python 3)
3. Commit the regenerated `.html`, `sitemap.xml`, and `robots.txt`

Colours, fonts, and spacing live at the top of `styles.css` under `:root { ... }`.

## Brand assets
- `logo.png` — full logo, cropped from the printed poster (cream background #fcf8f0,
  which the hero background matches exactly so the image edges are invisible)
- `logo-sm.png` — nav logo · `logo-foot.png` — light logo for the dark footer
- `crest.png` / `crest-mark.png` — sunburst crest · `favicon.png` · `og.jpg` — social share image

## SEO
Every page has a unique title + meta description, canonical URL, Open Graph and Twitter
cards, and JSON-LD structured data. `sitemap.xml` and `robots.txt` are included.

## Deployment
Hosted on Vercel. Future edits are published by redeploying this folder.
