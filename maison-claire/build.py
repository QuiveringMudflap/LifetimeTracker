#!/usr/bin/env python3
"""Static site generator for Maison Claire.

Every page shares one header, footer, and SEO <head> so the site stays
consistent. Edit the CONTENT blocks below (or the templates) and run:

    python3 build.py

It writes the .html files, sitemap.xml and robots.txt into this folder.
"""
import os, time

VER = str(int(time.time()))  # cache-buster, bumped every build
BASE = "https://maisonclaire-mauve.vercel.app"
OG = BASE + "/og.jpg"
EMAIL = "booking@MaisonClaireHealing.com"
# Web3Forms access key registered to EMAIL. Empty -> forms fall back to a
# pre-filled email draft. Paste the free key here to enable automatic sending.
FORM_ACCESS_KEY = "9aeb12de-1e7e-406d-a737-f719e657739d"
PHONE_DISPLAY = "604-841-4833"
PHONE_TEL = "+16048414833"
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- icons
IC = {
"lotus": """<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 47 C22 41 18 33 22 27 C26 23 30 27 32 31 C34 27 38 23 42 27 C46 33 42 41 32 47 Z" fill="none" stroke="#fff" stroke-width="1.7"/><path d="M32 47 C28 41 26 35 28 29" fill="none" stroke="#fff" stroke-width="1"/><path d="M32 47 C36 41 38 35 36 29" fill="none" stroke="#fff" stroke-width="1"/><path d="M32 47 C24 43 17 43 13 39 C18 34 25 37 32 44" fill="none" stroke="#fff" stroke-width="1"/><path d="M32 47 C40 43 47 43 51 39 C46 34 39 37 32 44" fill="none" stroke="#fff" stroke-width="1"/></svg>""",
"caduceus": """<svg viewBox="0 0 64 64" aria-hidden="true"><line x1="32" y1="12" x2="32" y2="52" stroke="#fff" stroke-width="1.5"/><path d="M32 24 C22 27 22 35 32 38 C42 35 42 27 32 24 Z" fill="none" stroke="#fff" stroke-width="1.4"/><path d="M32 31 C24 31 22 37 26 45" fill="none" stroke="#fff" stroke-width="1.2"/><path d="M32 31 C40 31 42 37 38 45" fill="none" stroke="#fff" stroke-width="1.2"/><g stroke="#fff" stroke-width="0.9" stroke-linecap="round" opacity="0.85"><line x1="32" y1="6" x2="32" y2="12"/><line x1="21" y1="9" x2="25" y2="15"/><line x1="43" y1="9" x2="39" y2="15"/><line x1="15" y1="19" x2="21" y2="21"/><line x1="49" y1="19" x2="43" y2="21"/></g><circle cx="32" cy="10" r="1.4" fill="#fff"/></svg>""",
"spiral": """<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 32 m-2 0 a2 2 0 1 1 4 0 a2 2 0 1 1 -4 0 M32 32 m-6 0 a6 6 0 1 1 12 0 M32 32 m-10 0 a10 10 0 1 1 20 0 a10 10 0 1 1 -18 4 M32 32 m-14 0 a14 14 0 1 1 28 0 a14 14 0 1 1 -26 6" fill="none" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/></svg>""",
"rays": """<svg viewBox="0 0 64 64" aria-hidden="true"><g stroke="#fff" stroke-width="1.3" stroke-linecap="round"><line x1="32" y1="14" x2="32" y2="24"/><line x1="45" y1="19" x2="40" y2="27"/><line x1="19" y1="19" x2="24" y2="27"/><line x1="50" y1="32" x2="42" y2="32"/><line x1="14" y1="32" x2="22" y2="32"/><line x1="45" y1="45" x2="40" y2="37"/><line x1="19" y1="45" x2="24" y2="37"/></g><circle cx="32" cy="32" r="7" fill="none" stroke="#fff" stroke-width="1.5"/><path d="M23 46 C27 42 37 42 41 46" fill="none" stroke="#fff" stroke-width="1.3"/></svg>""",
}

MOUNTAINS = """<div class="hero-mountains" aria-hidden="true"><svg viewBox="0 0 1440 240" preserveAspectRatio="none"><path d="M0,180 C220,120 360,200 560,160 C760,120 900,200 1120,150 C1280,115 1360,170 1440,150 L1440,240 L0,240 Z" fill="#e9dfc9" opacity="0.55"/><path d="M0,200 C260,150 420,215 640,190 C860,165 980,220 1200,190 C1320,175 1400,205 1440,195 L1440,240 L0,240 Z" fill="#d8c9a4" opacity="0.55"/><path d="M0,180 Q360,140 720,170 T1440,170" fill="none" stroke="#b28c4d" stroke-width="1" opacity="0.6"/><path d="M0,205 Q400,175 800,195 T1440,195" fill="none" stroke="#b28c4d" stroke-width="1" opacity="0.4"/></svg></div>"""

# ---------------------------------------------------------------- nav / footer
NAVLINKS = [
    ("Home", "/"),
    ("Journeys", "/journeys"),
    ("Approach", "/approach"),
    ("About", "/about"),
    ("Contact", "/contact"),
]

def nav(active):
    parts = []
    for label, url in NAVLINKS:
        cls = ' class="active"' if url == active else ''
        parts.append(f'<a href="{url}"{cls}>{label}</a>')
    items = "".join(parts)
    return f"""<header class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-brand" aria-label="Maison Claire Healing home"><img src="/maison-claire-logo.svg" alt="Maison Claire Healing" width="1200" height="520" /></a>
    <nav class="nav-links" aria-label="Primary">{items}</nav>
    <a href="/consultation" class="nav-cta">Request a Consultation</a>
    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>"""

FOOTER = f"""<footer class="foot">
  <div class="container">
    <div class="foot-top">
      <div class="foot-brand-block">
        <img src="/maison-claire-logo-light.svg" alt="Maison Claire Healing" />
        <p class="foot-tag">A Clearer You &nbsp;&bull;&nbsp; A Brighter Tomorrow</p>
        <p class="foot-desc">A private space for deeper change with Stanislava, a whole-person healing practice on Bowen Island, British Columbia. In-person &amp; online.</p>
      </div>
      <div class="foot-col">
        <h4>Explore</h4>
        <a href="/">Home</a>
        <a href="/journeys">Journeys</a>
        <a href="/approach">Approach</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
      </div>
      <div class="foot-col">
        <h4>Journeys</h4>
        <a href="/the-first-step">The First Step</a>
        <a href="/the-reset">The Reset</a>
        <a href="/the-root">The Root</a>
        <a href="/restore">Restore</a>
        <a href="/the-private-journey">The Private Journey</a>
        <a href="mailto:{EMAIL}">{EMAIL}</a>
      </div>
    </div>
    <div class="foot-bottom">
      <p class="heal">Listen &nbsp;&bull;&nbsp; Heal &nbsp;&bull;&nbsp; Live Fully</p>
      <p>&copy; <span id="year"></span> Maison Claire Healing &middot; Bowen Island, BC. All rights reserved.</p>
    </div>
  </div>
</footer>
""" + """<script>
  var y=document.getElementById('year'); if(y) y.textContent=new Date().getFullYear();
  var t=document.querySelector('.nav-toggle'), l=document.querySelector('.nav-links');
  if(t&&l){t.addEventListener('click',function(){var o=l.classList.toggle('open');t.setAttribute('aria-expanded',o);});
  l.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){l.classList.remove('open');t.setAttribute('aria-expanded',false);});});}
</script>"""

def page(path, title, desc, body, active, jsonld=""):
    canonical = BASE + ("/" if path == "index" else "/" + path)
    ld = f'\n<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<link rel="canonical" href="{canonical}" />
<meta name="theme-color" content="#fcf8f0" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Maison Claire" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{OG}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{OG}" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css" />
<link rel="icon" type="image/png" href="/favicon.png" />
<link rel="apple-touch-icon" href="/crest.png" />{ld}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{nav(active)}
<main id="main">
{body}
</main>
{FOOTER}
</body>
</html>
"""
    # Cache-busting: version every local asset so redeploys always refresh
    for asset in ["/styles.css", "/logo.png", "/logo-sm.png", "/logo-foot.png",
                  "/logo-navy.png", "/logo-navy-light.png", "/crest.png", "/crest-navy.png",
                  "/crest-mark.png", "/favicon.png", "/og.jpg",
                  "/hero.jpg", "/portrait.jpg", "/lighthouse-warm.jpg", "/lighthouse-blue.jpg",
                  "/mountains.jpg", "/grassland.jpg", "/horses.jpg",
                  "/banner-waterfall.jpg", "/banner-village.jpg", "/banner-seatree.jpg",
                  "/banner-mistlake.jpg", "/banner-greenhills.jpg", "/portrait-bw.jpg",
                  "/window.jpg", "/nature-shore.jpg", "/nature-lake.jpg", "/nature-icecap.jpg",
                  "/maison-claire-logo.svg", "/maison-claire-logo-light.svg"]:
        html = html.replace(asset, asset + "?v=" + VER)
    fn = os.path.join(HERE, ("index" if path == "index" else path) + ".html")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    return path

# ---------------------------------------------------------------- shared blocks
def cta_band(heading="Your first step is a conversation", text="A free 15-minute introductory consultation. A simple, no-pressure conversation to share what&rsquo;s happening, ask questions, and discover whether working together feels right for you."):
    return f"""<section class="pad cta-band"><div class="container center">
    <h2>{heading}</h2>
    <p>{text}</p>
    <div class="hero-cta" style="justify-content:center">
      <a href="/consultation" class="btn btn-primary">Request a Consultation</a>
      <a href="tel:{PHONE_TEL}" class="btn btn-ghost">Call {PHONE_DISPLAY}</a>
    </div>
  </div></section>"""

SERVICES = [
    ("reiki-healing", "rays", "Reiki Healing",
     "Restore energetic balance, reduce stress, and support your natural healing on every level."),
    ("hypnotherapy-intuitive-guidance", "caduceus", "Hypnotherapy &amp; Intuitive Guidance",
     "Clear blocks, release old patterns, and reconnect with your inner wisdom for lasting transformation."),
    ("liver-cleanse-detox", "lotus", "Liver Cleanse &amp; Detox",
     "Support your body&rsquo;s natural detoxification, reset your energy, and restore balance."),
    ("root-cause-healing", "spiral", "Root Cause Healing",
     "Uncover the root cause, so your body, mind, and spirit can return to their natural state of healing."),
]

def _card(slug, icon, name, blurb, pos):
    return f"""<article class="service s-{pos}">
        <div class="service-icon">{IC[icon]}</div>
        <h3>{name}</h3>
        <p>{blurb}</p>
        <a class="more" href="/{slug}">Learn more</a>
      </article>"""

def services_grid(items):
    return "".join(_card(s, i, n, b, "flow") for s, i, n, b in items)

def services_diamond(items, center=""):
    # items in order: top, left, right, bottom
    positions = ["top", "left", "right", "bottom"]
    cards = "".join(_card(items[k][0], items[k][1], items[k][2], items[k][3], positions[k]) for k in range(4))
    mid = f'<div class="diamond-center">{center}</div>' if center else ''
    return f'<div class="service-diamond">{cards}{mid}</div>'

# ================================================================ PAGES

# ---- Home
PROMPTS = [
    ("star", "You&rsquo;re moving through a major life transition."),
    ("waves", "You feel disconnected from yourself."),
    ("rings", "You&rsquo;re repeating a pattern you can&rsquo;t seem to shift."),
    ("lotus2", "You carry emotional weight that no longer serves you."),
    ("eye", "You&rsquo;re searching for greater clarity and direction."),
    ("sun2", "You want a deeper understanding of yourself."),
]
PIC = {
"star": '<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="15" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M24 9 L26 22 L39 24 L26 26 L24 39 L22 26 L9 24 L22 22 Z" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round"/></svg>',
"waves": '<svg viewBox="0 0 48 48"><path d="M8 20 Q16 14 24 20 T40 20 M8 28 Q16 22 24 28 T40 28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
"rings": '<svg viewBox="0 0 48 48"><circle cx="19" cy="24" r="11" fill="none" stroke="currentColor" stroke-width="1.1"/><circle cx="29" cy="24" r="11" fill="none" stroke="currentColor" stroke-width="1.1"/></svg>',
"lotus2": '<svg viewBox="0 0 48 48"><path d="M24 36 C16 31 13 25 16 20 C20 17 23 21 24 25 C25 21 28 17 32 20 C35 25 32 31 24 36 Z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M24 36 C20 31 19 26 20 22 M24 36 C28 31 29 26 28 22" fill="none" stroke="currentColor" stroke-width="0.9"/></svg>',
"eye": '<svg viewBox="0 0 48 48"><path d="M9 24 Q24 12 39 24 Q24 36 9 24 Z" fill="none" stroke="currentColor" stroke-width="1.1"/><circle cx="24" cy="24" r="4.5" fill="none" stroke="currentColor" stroke-width="1.1"/></svg>',
"sun2": '<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="7" fill="none" stroke="currentColor" stroke-width="1.2"/><g stroke="currentColor" stroke-width="1.1" stroke-linecap="round"><line x1="24" y1="8" x2="24" y2="13"/><line x1="24" y1="35" x2="24" y2="40"/><line x1="8" y1="24" x2="13" y2="24"/><line x1="35" y1="24" x2="40" y2="24"/><line x1="13" y1="13" x2="16.5" y2="16.5"/><line x1="31.5" y1="31.5" x2="35" y2="35"/><line x1="35" y1="13" x2="31.5" y2="16.5"/><line x1="16.5" y1="31.5" x2="13" y2="35"/></g></svg>',
}
prompts_html = "".join(f'<div class="prompt"><span class="prompt-ic">{PIC[i]}</span><p>{t}</p></div>' for i, t in PROMPTS)

MODALITIES = [
    ("rays", "Intuitive Guidance"),
    ("caduceus", "Hypnotherapy"),
    ("spiral", "Reiki &amp; Energy Work"),
    ("lotus", "Personalized Practices"),
]
modalities_html = "".join(f'<div class="modality"><span class="modality-ic">{IC[i]}</span><span>{n}</span></div>' for i, n in MODALITIES)

home_body = f"""<section class="photo-hero" style="background-image:linear-gradient(90deg, rgba(22,38,58,0.78) 0%, rgba(22,38,58,0.42) 42%, rgba(22,38,58,0.10) 70%, rgba(22,38,58,0) 100%), url('/hero.jpg');">
  <div class="container photo-hero-inner">
    <p class="ph-eyebrow">A whole-person approach to healing</p>
    <h1 class="ph-title">Come back<br/>to yourself.</h1>
    <p class="ph-lead">When something doesn&rsquo;t feel right, there is often more to the story than what we see on the surface.</p>
    <div class="hero-cta">
      <a href="/consultation" class="btn btn-primary">Request a Consultation</a>
    </div>
  </div>
</section>

<section class="pad">
  <div class="container narrow intro-lede">
    <p class="lead">At Maison Claire, we take the time to look at the whole picture: body, mind, lifestyle and environment, and explore what may be contributing to the way you feel.</p>
    <p>My approach combines natural health coaching, nutrition, cleansing and detox support, hypnotherapy, Reiki and complementary healing practices.</p>
    <p class="statement">There is no standard protocol.</p>
    <p class="statement-sub">We begin with you. We look deeper. And we start where it makes sense.</p>
  </div>
</section>

<section class="pad tint">
  <div class="container">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">Is something asking to change?</p><div class="rule"></div></div>
    <div class="prompts">{prompts_html}</div>
    <div class="center" style="margin-top:34px"><a href="/journeys" class="btn btn-ghost">Explore the Journey</a></div>
  </div>
</section>

<section class="feature-band" style="background-image:linear-gradient(90deg, rgba(22,38,58,0.72), rgba(22,38,58,0.30)), url('/lighthouse-blue.jpg');">
  <div class="container feature-inner">
    <div class="feature-card">
      <p class="eyebrow" style="color:var(--gold-soft)">Healing from the inside out</p>
      <h2>We look deeper.<br/>Beyond the surface.</h2>
      <p>Because true healing is not just about what you can see. It is about what lies beneath, in the physical, emotional, and energetic patterns that shape how you feel and live.</p>
      <a href="/approach" class="btn btn-ghost light">The Maison Claire Approach</a>
    </div>
  </div>
</section>

<section class="pad tint">
  <div class="container split-approach">
    <div>
      <p class="eyebrow">A personalized approach</p>
      <h2 class="approach-title">You are more than the patterns you have lived through.</h2>
      <p>Through intuitive guidance, hypnosis, Reiki, and complementary practices, each journey is shaped around the individual, not a predetermined formula.</p>
      <p>This is not about fixing you. It is about helping you explore what may already be within you, and giving you the space, perspective, and support to move forward with greater clarity, balance, and ease.</p>
      <p class="signature">Stanislava</p>
    </div>
    <div class="modalities">{modalities_html}</div>
  </div>
</section>

<section class="photo-band" style="background-image:linear-gradient(rgba(22,38,58,0.38), rgba(22,38,58,0.38)), url('/banner-waterfall.jpg');">
  <div class="container center"><p class="band-line">A more luminous you.</p></div>
</section>

<section class="pad testimonial-sec">
  <div class="container narrow center">
    <span class="mark" aria-hidden="true">&ldquo;</span>
    <blockquote class="testimonial">Stani is a natural intuitive. Her ability to connect to the Spirit World, to hear the clear messages from our passed ancestors and to relay them in a healing way is truly beautiful. If you are seeking to connect to your spirit guides, your family on the &lsquo;other side&rsquo; (human and animal), or just to get some clarity, I recommend a session with Stani.</blockquote>
    <cite>Andrea &middot; @nectaryoga</cite>
  </div>
</section>

{cta_band()}"""

home_ld = """{"@context":"https://schema.org","@type":"HealthAndBeautyBusiness","name":"Maison Claire","description":"Reiki healing, hypnotherapy, intuitive guidance, liver cleanse and detox, and root cause healing with Stanislava.","image":"%s","email":"%s","telephone":"%s","url":"%s","slogan":"Natural Healing, Higher Wellbeing, A Brighter You","priceRange":"$$","areaServed":"Greater Vancouver","founder":{"@type":"Person","name":"Stanislava"}}""" % (OG, EMAIL, PHONE_DISPLAY, BASE)

page("index", "Maison Claire | Reiki Healing & Natural Wellness with Stanislava",
     "Maison Claire offers Reiki healing, hypnotherapy, intuitive guidance, liver cleanse and detox, and root cause healing. Heal at the root and return to your natural state of balance with Stanislava.",
     home_body, "/", home_ld)


# ---- extra icons for approach
IC["leaf"] = '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M20 44 C20 28 34 18 46 18 C46 34 36 46 20 44 Z" fill="none" stroke="#fff" stroke-width="1.4"/><path d="M20 44 C26 38 34 32 44 26" fill="none" stroke="#fff" stroke-width="1.1"/></svg>'

DISCLAIMER = ("Maison Claire provides complementary health and wellness support and does not "
              "replace medical diagnosis or treatment.")

# ================================================================ JOURNEYS
JOURNEYS = [
    ("the-first-step", "01", "The First Step", "2 hours &middot; $250",
     "Where every Maison Claire journey begins.", "lighthouse-warm.jpg"),
    ("the-reset", "02", "The Reset", "3 weeks &middot; From $750",
     "Sometimes the body needs less, not more.", "mountains.jpg"),
    ("the-root", "03", "The Root", "6 weeks &middot; From $1,500",
     "When you are ready to look deeper.", "lighthouse-blue.jpg"),
    ("restore", "04", "Restore", "8-10 weeks &middot; From $2,500",
     "From understanding to rebuilding.", "horses.jpg"),
    ("the-private-journey", "05", "The Private Journey", "3-6 months &middot; By application &middot; From $4,500",
     "Maison Claire&rsquo;s most personal level of work.", "hero.jpg"),
]

def journey_row(slug, num, name, meta, tagline, img):
    return f"""<a class="journey-row" href="/{slug}">
      <span class="jr-img" style="background-image:url('/{img}')"></span>
      <span class="jr-text">
        <span class="jr-num">{num}</span>
        <span class="jr-name">{name}</span>
        <span class="jr-meta">{meta}</span>
        <span class="jr-tag">{tagline}</span>
      </span>
      <span class="jr-arrow" aria-hidden="true">&rarr;</span>
    </a>"""

journeys_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Journeys</p>
    <h1>Start where it<br/>makes sense.</h1>
    <p>Every journey at Maison Claire is private and personal. Begin with a single conversation, or go as deep as you wish.</p>
  </div>
</section>

<section class="photo-band tall" style="background-image:linear-gradient(rgba(22,38,58,0.16), rgba(22,38,58,0.16)), url('/banner-seatree.jpg');"></section>

<section class="pad">
  <div class="container narrow">
    <div class="journey-list">{''.join(journey_row(*j) for j in JOURNEYS)}</div>
    <p class="disclaimer-note">{DISCLAIMER}</p>
  </div>
</section>

<section class="pad tint">
  <div class="container center">
    <h2 class="approach-title" style="max-width:640px;margin:0 auto 14px">Not sure which journey is yours?</h2>
    <p class="approach-lead">You do not have to decide before you arrive. We begin with a conversation.</p>
    <a href="/consultation" class="btn btn-primary">Request a Consultation</a>
  </div>
</section>"""
journeys_ld = ('{"@context":"https://schema.org","@type":"ItemList","name":"Maison Claire Journeys","itemListElement":['
    + ",".join('{"@type":"ListItem","position":%d,"name":"%s","url":"%s/%s"}' % (i+1, j[2], BASE, j[0]) for i, j in enumerate(JOURNEYS))
    + "]}")
page("journeys", "Journeys & Pricing | Maison Claire Healing",
     "Maison Claire healing journeys with Stanislava: The First Step, The Reset, The Root, Restore, and The Private Journey. Durations, pricing, and what each involves.",
     journeys_body, "/journeys", journeys_ld)

def _blocks(items):
    out = []
    for kind, val in items:
        if kind == "p":
            out.append(f"<p>{val}</p>")
        elif kind == "s":
            out.append(f'<p class="statement">{val}</p>')
        elif kind == "list":
            out.append('<div class="word-list">' + "".join(f"<span>{v}</span>" for v in val) + "</div>")
    return "".join(out)

def journey_page(slug, num, name, meta, tagline, img, blocks, cta_label, cta_href, mtitle, mdesc, extra=""):
    body = f"""<section class="photo-hero journey-hero" style="background-image:linear-gradient(90deg, rgba(22,38,58,0.84) 0%, rgba(22,38,58,0.44) 55%, rgba(22,38,58,0.10) 100%), url('/{img}');">
  <div class="container photo-hero-inner">
    <p class="ph-eyebrow">{num} &nbsp;&middot;&nbsp; A Maison Claire Journey</p>
    <h1 class="ph-title">{name}</h1>
    <p class="ph-meta">{meta}</p>
    <p class="ph-lead">{tagline}</p>
    <div class="hero-cta"><a href="{cta_href}" class="btn btn-primary">{cta_label}</a></div>
  </div>
</section>

<section class="pad">
  <div class="container narrow prose journey-prose">{_blocks(blocks)}</div>
</section>
{extra}
<section class="pad tint">
  <div class="container center">
    <div class="price-panel">
      <p class="price-meta">{meta}</p>
      <a href="{cta_href}" class="btn btn-primary">{cta_label}</a>
      <p class="disclaimer-note">{DISCLAIMER}</p>
    </div>
  </div>
</section>"""
    ld = '{"@context":"https://schema.org","@type":"Service","serviceType":"%s","provider":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire Healing"},"areaServed":"Bowen Island, British Columbia","description":"%s","url":"%s/%s"}' % (name, mdesc.replace('"', ''), BASE, slug)
    page(slug, mtitle, mdesc, body, "/journeys", ld)

journey_page("the-first-step", "01", "The First Step", "2 hours &middot; $250",
    "Two unhurried hours dedicated to understanding you.", "lighthouse-warm.jpg",
    [("p", "This is where every Maison Claire journey begins."),
     ("p", "Before recommending a cleanse, supplement, healing practice or longer program, I want to understand what is actually happening in your life."),
     ("p", "We will talk about your health history, nutrition, digestion, sleep, energy, stress, environment, emotional wellbeing, medications and supplements, previous approaches you have tried, and what you would most like to change."),
     ("s", "We begin connecting the dots."),
     ("p", "There may be obvious areas to work on. There may be questions that require further investigation or a conversation with your physician or another qualified practitioner."),
     ("p", "You leave with a clearer picture and practical first steps.")],
    "Begin with The First Step", "/consultation",
    "The First Step | Maison Claire Healing",
    "The First Step is a two hour consultation with Stanislava at Maison Claire. $250. Understand your health history, nutrition, sleep, stress and environment, and leave with practical first steps.")

journey_page("the-reset", "02", "The Reset", "3 weeks &middot; From $750",
    "A cleaner, simpler foundation for wellbeing.", "mountains.jpg",
    [("p", "Sometimes the first thing the body needs is not more."),
     ("s", "It is less."),
     ("p", "The Reset focuses on creating a cleaner, simpler foundation for wellbeing."),
     ("p", "Depending on your individual situation, we may look at food, hydration, digestion, sleep, household and environmental exposures, stress, movement and daily habits."),
     ("p", "This is also where we can discuss whether a structured gut, liver or general body-cleansing approach is appropriate for you."),
     ("p", "Nothing is automatically prescribed simply because it is part of a program."),
     ("p", "We choose what makes sense for your body, your circumstances and your goals, and identify situations where medical guidance or testing should come first."),
     ("s", "Reduce unnecessary burden. Support healthy habits. Give the body a better environment in which to function.")],
    "Explore The Reset", "/consultation",
    "The Reset | Maison Claire Healing",
    "The Reset is a three week journey with Stanislava from $750: food, hydration, digestion, sleep, environment and stress, with cleansing support where appropriate.")

journey_page("the-root", "03", "The Root", "6 weeks &middot; From $1,500",
    "When you are ready to look deeper.", "lighthouse-blue.jpg",
    [("p", "Sometimes changing food or completing a cleanse is not the whole answer."),
     ("p", "This journey asks a different question:"),
     ("s", "What else could be contributing to the way you feel?"),
     ("p", "Together we look more closely at the different layers of your wellbeing: nutrition, digestion, lifestyle, environment, stress, emotional patterns and personal history."),
     ("p", "Where appropriate, our work may include education around gut and liver support, environmental and heavy-metal exposure, parasite concerns, nutrition and cleansing practices."),
     ("p", "When something requires diagnosis, laboratory investigation or medical treatment, that belongs with an appropriately licensed healthcare professional."),
     ("p", "Maison Claire&rsquo;s role is to help you see the whole picture, ask better questions and create practical changes around the factors within your control."),
     ("p", "We may also incorporate hypnotherapy, Reiki, sound, light, breath, meditation or intuitive work when these complement the physical work and resonate with you."),
     ("p", "Not everything has to be physical. Not everything has to be emotional. Often, several parts of our lives are speaking at once.")],
    "Explore The Root", "/consultation",
    "The Root | Maison Claire Healing",
    "The Root is a six week journey with Stanislava from $1,500, exploring the deeper layers of wellbeing: nutrition, digestion, environment, stress and emotional patterns.")

journey_page("restore", "04", "Restore", "8-10 weeks &middot; From $2,500",
    "From understanding to rebuilding.", "horses.jpg",
    [("p", "Once we have begun identifying the areas that need attention, the work becomes less about searching and more about creating a healthier way forward."),
     ("p", "Restore is a longer, highly personalized journey."),
     ("p", "We continue supporting the physical foundations (nutrition, gut and liver health, sleep, movement, environmental awareness and appropriate cleansing practices) while also addressing the patterns that influence how you live."),
     ("list", ["Stress", "Relationships", "Boundaries", "Beliefs", "Habits", "The way you speak to yourself", "The things you know you need to change but have not yet been able to"]),
     ("p", "Depending on your needs, sessions may incorporate health coaching, hypnotherapy, intuitive guidance, Reiki, sound, light and other complementary practices."),
     ("p", "The objective is not perfection. It is helping you create a way of living that supports your wellbeing long after our sessions end.")],
    "Explore Restore", "/consultation",
    "Restore | Maison Claire Healing",
    "Restore is an 8 to 10 week journey with Stanislava from $2,500, rebuilding physical foundations while addressing stress, boundaries, beliefs and daily patterns.")

journey_page("the-private-journey", "05", "The Private Journey", "3-6 months &middot; By application &middot; From $4,500",
    "Maison Claire&rsquo;s most personal level of work.", "hero.jpg",
    [("p", "This is not a predetermined program."),
     ("p", "It is an ongoing private relationship for someone who wants the time and space to explore their wellbeing more deeply."),
     ("p", "We begin with the physical foundations and follow what emerges."),
     ("list", ["Nutrition and lifestyle", "Gut and liver support", "Environmental exposures", "Cleansing when appropriate", "Stress and emotional wellbeing", "Patterns and beliefs", "Hypnotherapy", "Energy work", "Sound and light", "Intuition", "Nature"]),
     ("p", "And sometimes simply having a quiet, confidential place to stop and listen to what your body and your life have been trying to tell you."),
     ("p", "Some weeks may focus primarily on physical wellbeing. Others may have very little to do with it."),
     ("s", "The work follows the person rather than forcing the person into a program."),
     ("p", "When something falls outside my scope as a health coach or complementary practitioner, I will encourage you to involve the appropriate physician or healthcare professional."),
     ("p", "The goal is not dependency on Maison Claire. The goal is greater understanding of yourself, greater ownership of your wellbeing and a way forward that you can carry into the rest of your life.")],
    "By Application", "/apply",
    "The Private Journey | Maison Claire Healing",
    "The Private Journey is Maison Claire&rsquo;s most personal work with Stanislava: 3 to 6 months, by application, from $4,500. An ongoing private relationship that follows the person.",
    extra="""<section class="photo-band tall" style="background-image:linear-gradient(rgba(22,38,58,0.32), rgba(22,38,58,0.32)), url('/window.jpg');">
  <div class="container center"><p class="band-line">A quiet, confidential place to stop and listen.</p></div>
</section>""")

# ================================================================ APPROACH
EXPLORE_TAGS = ["Gut &amp; digestive health", "Liver support", "Nutrition", "Cleansing practices",
    "Environmental exposures", "Heavy-metal exposure awareness", "Parasite concerns", "Sleep",
    "Stress", "Emotional patterns", "Hypnotherapy", "Reiki", "Sound", "Light", "Breath",
    "Nature", "Intuitive guidance"]
tags_html = "".join(f"<span class='tag'>{t}</span>" for t in EXPLORE_TAGS)

FLOW = ["We start with where you are.", "We listen.", "We investigate what is within our scope.",
        "We make changes.", "We observe.",
        "And when necessary, we bring other qualified healthcare professionals into the picture.",
        "Then we take the next step."]
flow_html = "".join(f"<li>{f}</li>" for f in FLOW)

approach_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">The Maison Claire Approach</p>
    <h1>Look deeper.<br/>Keep it human.</h1>
    <p>Maison Claire is built around a simple idea.</p>
  </div>
</section>

<section class="pad">
  <div class="container narrow prose center-prose">
    <p class="lead">What we experience on the surface deserves attention, but so does what may be contributing underneath it.</p>
    <div class="not-only">
      <span>That means we don&rsquo;t look only at food.</span>
      <span>Or only at stress.</span>
      <span>Or only at the physical body.</span>
      <span>Or only at emotional and spiritual wellbeing.</span>
    </div>
    <p class="statement">We look at the person.</p>
    <p>My work as a Certified Natural Health Coach brings together health education, nutrition and lifestyle practices with complementary approaches to wellbeing.</p>
  </div>
  <div class="container narrow center" style="margin-top:clamp(46px,6vw,70px)">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">Our work may explore</p><div class="rule"></div></div>
    <div class="tags">{tags_html}</div>
    <p class="tags-note">Not everyone needs everything. In fact, most people don&rsquo;t.<br/><em>The art is discovering what deserves attention now.</em></p>
  </div>
</section>

<section class="bms" style="background-image:linear-gradient(rgba(22,48,74,0.62), rgba(22,48,74,0.62)), url('/banner-greenhills.jpg'); background-size:cover; background-position:center;">
  <div class="container center">
    <p class="bms-line">Body &nbsp;&middot;&nbsp; Mind &nbsp;&middot;&nbsp; Environment &nbsp;&middot;&nbsp; Self</p>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow center">
    <h2 class="approach-title" style="text-align:center">Healing is not a straight line.</h2>
    <ol class="flow">{flow_html}</ol>
    <p class="statement" style="margin-top:34px">That is the Maison Claire journey.</p>
    <p class="disclaimer-note">{DISCLAIMER}</p>
  </div>
</section>

{cta_band()}"""
approach_ld = '{"@context":"https://schema.org","@type":"MedicalWebPage","name":"The Maison Claire Approach","about":"Whole-person natural health coaching: gut and liver support, nutrition, cleansing practices, environmental exposures, sleep, stress, emotional patterns, hypnotherapy, Reiki, sound, light, breath, nature and intuitive guidance."}'
page("approach", "The Approach | Whole-Person Health Coaching at Maison Claire",
     "The Maison Claire approach with Stanislava, a Certified Natural Health Coach: look at the whole person, body, mind, environment and self, and discover what deserves attention now.",
     approach_body, "/approach", approach_ld)

# ================================================================ ABOUT
TESTIMONIALS = [
    ("Stanka is incredible at Mediumship! During our first session, she connected with a dear family member of mine who has long passed and channeled through loving and caring messages from my spirit team. I was able to gain clarity of thoughts in major areas of my life in the present moment all in one session. Stanka is straight forward and she also shares her own interpretations and wisdom to help me process the information at hand. I truly enjoyed my first session with her, and would definitely see her again.",
     "Shengyin &middot; Vancouver, BC"),
    ("Stani is a bright and clear channel through which the vibration of love emanates. She holds space for you in a crystalline manner, there is no static or noise when you are held in her field, just a familiar and grounded reassurance. In this way she helps you access the ancient wisdom and &lsquo;knowing&rsquo; that is always and has always been within you. To sit in session with Stani is to receive the affirmation of the divine soul being that you are, whether it be through mediumship or her own voice, that is where she will take you. Back to Love, back home to your Self.",
     "Rebecca &middot; @kashmikashmi"),
    ("My daughter thought I may benefit from a reading so I decided after a bit of thinking about it to make an appointment. Much to my pleasant surprise and ultimately to my greater ease in current life, the reading brought me to ask questions and get answers via Stani&rsquo;s ability to connect with spirit. All I can say is the reading was amazing. You helped me conclude so much that really had incompletion. Truly, for anyone who&rsquo;s wanting closure from those that have left this earthly planet, the spirit reading that Stani does will be one of the most amazing experiences of your life. Thank you Stani.",
     "K.T. &middot; Vancouver"),
    ("Stani is a natural intuitive. Her ability to connect to the Spirit World, to hear the clear messages from our passed ancestors and to relay them in a healing way is truly beautiful. If you are seeking to connect to your spirit guides, your family on the &lsquo;other side&rsquo; (human and animal), or just to get some clarity, I recommend a session with Stani.",
     "Andrea &middot; @nectaryoga"),
]
kind_words_html = '<div class="kind-words">' + "".join(
    f'<figure class="kw-card"><span class="mark" aria-hidden="true">&ldquo;</span>'
    f'<blockquote>{q}</blockquote><figcaption>{c}</figcaption></figure>'
    for q, c in TESTIMONIALS) + '</div>'

about_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">About Me</p>
    <h1>A guide, a practitioner,<br/>and a fellow traveller.</h1>
    <p>My name is Stanislava Oben.</p>
  </div>
</section>

<section class="pad">
  <div class="container split-about">
    <div class="about-photo"><img src="/portrait.jpg" alt="Stanislava Oben, founder of Maison Claire Healing" width="1500" height="1000" /></div>
    <div class="prose">
      <p>For much of my life, I have been curious about what lies beneath the surface of our health, our emotions, our patterns, and even our understanding of who we are.</p>
      <p>That curiosity has taken me in many directions.</p>
      <p>I have studied the physical body and natural approaches to health. I have explored hypnosis and the subconscious mind. I have worked with Reiki, intuition, energy and mediumship, and through all of it, I have become increasingly interested in one fundamental question:</p>
      <p class="statement" style="text-align:left">What is really asking for our attention?</p>
      <p>Maison Claire grew from that question.</p>
    </div>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow prose center-prose">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">A whole-person approach</p><div class="rule"></div></div>
    <p class="lead">I believe that we have an extraordinary capacity to heal, grow and come back into relationship with ourselves.</p>
    <p>But&hellip; I don&rsquo;t believe there is one formula for getting there.</p>
    <p>Sometimes we need to begin with the body: looking at nutrition, digestion, lifestyle, liver support, cleansing practices, our environment and the things we are exposed to every day.</p>
    <p>Sometimes we need to look at stress, emotions, beliefs or patterns we have carried for years.</p>
    <p>And sometimes the work takes us somewhere less tangible: into intuition, energy, consciousness and our connection to something beyond ourselves.</p>
    <p>My role is not to decide the answer before you arrive. My role is to listen, ask questions, look deeper and help you explore the different pieces of your own story.</p>
    <p>My training as a Certified Natural Health Coach, Certified Hypnotherapist and Reiki Practitioner, together with years of intuitive and mediumship work, allows me to draw from different approaches depending on the person sitting in front of me.</p>
    <p class="statement">Not everything is for everyone.</p>
    <p class="statement-sub">That is precisely the point.</p>
  </div>
</section>

<section class="pad">
  <div class="container split-about med">
    <div class="prose">
      <p class="eyebrow">Why Maison Claire?</p>
      <h2 class="approach-title">Where the different parts of my life finally came together.</h2>
      <div class="not-only">
        <span>The body and the mind.</span>
        <span>Science and intuition.</span>
        <span>Nature and energy.</span>
        <span>The practical and the unseen.</span>
      </div>
      <p>I don&rsquo;t ask anyone who comes through my door to believe what I believe. I simply ask that we remain curious.</p>
      <p>We begin with where you are, look at what may be contributing to the way you feel, and choose the practices that make sense for you.</p>
      <p>Sometimes that means making very practical changes. Sometimes it means going much deeper.</p>
      <p>And sometimes healing begins simply because, for the first time in a long time, we have given ourselves enough space to truly listen.</p>
      <p class="signature">Stanislava Oben</p>
      <p class="credentials">Certified Natural Health Coach &middot; Certified Hypnotherapist &middot; Reiki Practitioner<br/>Founder, Maison Claire Healing</p>
    </div>
    <div class="about-photo"><img src="/portrait-bw.jpg" alt="Stanislava Oben on the coast" width="1600" height="1089" /></div>
  </div>
</section>

<section class="pad quote">
  <div class="container">
    <blockquote><span class="mark" aria-hidden="true">&ldquo;</span>Healing is not about becoming someone different, but about removing what has obscured who you already are.</blockquote>
  </div>
</section>

<section class="pad-sm tint">
  <div class="container narrow prose">
    <p class="eyebrow">Mediumship</p>
    <h2>A bridge between two worlds.</h2>
    <p>The emphasis of my intuitive work is mediumship: making connections with, and delivering messages from, people who are no longer living to those who still are. I receive information primarily and directly from spirit guides, angels, and from those who have passed.</p>
    <p>While there are a number of forms of mediumship, I work as a mental medium, meaning I communicate with spirits through telepathy. Spirits impress my mind and body with thoughts and feelings that come in through the clairs. Mentally I hear (clairaudience), see (clairvoyance), know (claircognizance), and feel (clairsentience) messages from spirit.</p>
    <p>I act as the bridge between the spiritual and the physical world, with the intention of healing both.</p>
  </div>
</section>

<section class="pad-sm">
  <div class="container">
    <div class="gallery3">
      <img src="/nature-shore.jpg" alt="Golden light on a rocky shoreline" loading="lazy" />
      <img src="/nature-lake.jpg" alt="Still lake at sunset" loading="lazy" />
      <img src="/nature-icecap.jpg" alt="Arms raised at a glacier lagoon" loading="lazy" />
    </div>
  </div>
</section>

<section class="photo-band" style="background-image:linear-gradient(rgba(22,38,58,0.30), rgba(22,38,58,0.30)), url(\'/banner-mistlake.jpg\');">
  <div class="container center"><p class="band-line">Kind words</p></div>
</section>

<section class="pad kind-words-sec">
  <div class="container">
    {kind_words_html}
  </div>
</section>

{cta_band()}"""
about_ld = '{"@context":"https://schema.org","@type":"AboutPage","name":"About Stanislava Oben","about":{"@type":"Person","name":"Stanislava Oben","jobTitle":"Certified Natural Health Coach, Certified Hypnotherapist, Reiki Practitioner","worksFor":{"@type":"Organization","name":"Maison Claire Healing"}}}'
page("about", "About Stanislava Oben | Maison Claire Healing",
     "Meet Stanislava Oben, founder of Maison Claire Healing on Bowen Island: Certified Natural Health Coach, Certified Hypnotherapist and Reiki Practitioner, with years of intuitive and mediumship work.",
     about_body, "/about", about_ld)

# ================================================================ FORMS
AREA_OPTIONS = ["Energy &amp; overall wellbeing", "Digestion &amp; gut health", "Liver &amp; body cleansing",
    "Nutrition &amp; lifestyle", "Environmental exposures", "Stress &amp; emotional wellbeing",
    "Hypnotherapy &amp; patterns", "Reiki &amp; energy work", "Intuitive guidance", "I&rsquo;m not sure yet"]
SUPPORT_OPTIONS = ["I would like to begin with one session", "I am interested in a deeper healing journey",
    "I would like to understand my options first", "I&rsquo;m not sure, I would like your guidance"]

def checks(name, opts):
    return "".join(
        f'<label class="check"><input type="checkbox" name="{name}" value="{o}"/><span>{o}</span></label>'
        for o in opts)

def radios(name, opts):
    return "".join(
        f'<label class="check"><input type="radio" name="{name}" value="{o}"/><span>{o}</span></label>'
        for o in opts)

def field(label, name, kind="text", req=False, ph="", rows=4, hint=""):
    r = " required" if req else ""
    h = f'<span class="fhint">{hint}</span>' if hint else ""
    if kind == "textarea":
        inp = f'<textarea name="{name}" rows="{rows}" placeholder="{ph}"{r}></textarea>'
    else:
        inp = f'<input type="{kind}" name="{name}" placeholder="{ph}"{r}/>'
    return f'<div class="fgroup"><label class="flabel" for="{name}">{label}</label>{h}{inp}</div>'

FORM_JS = """<script>
(function(){
  var TO = "%s", KEY = "%s";
  document.querySelectorAll('form.mc-form').forEach(function(form){
    form.addEventListener('submit', function(ev){
      ev.preventDefault();
      if (form.querySelector('[name=_trap]') && form.querySelector('[name=_trap]').value) return;
      var fd = new FormData(form), groups = {}, order = [];
      fd.forEach(function(v, k){
        if (k.charAt(0) === '_') return;
        if (!(k in groups)) { groups[k] = []; order.push(k); }
        if (String(v).trim() !== '') groups[k].push(v);
      });
      var title = form.getAttribute('data-title') || 'Website enquiry';
      var lines = [title, '----------------------------------------', ''];
      order.forEach(function(k){
        var vals = groups[k];
        if (!vals.length) return;
        var el = form.querySelector('[data-label-for="' + k + '"]')
              || form.querySelector('label[for="' + k + '"]');
        var label = el ? el.textContent.trim()
                       : k.replace(/_/g, ' ').replace(/\\b\\w/g, function(c){ return c.toUpperCase(); });
        lines.push(/[?:]$/.test(label) ? label : label + ':');
        vals.forEach(function(v){ lines.push('  ' + String(v).trim()); });
        lines.push('');
      });
      lines.push('Sent from maisonclairehealing website');
      var body = lines.join('\\n');
      var status = form.querySelector('.form-status');
      function done(msg){
        form.querySelectorAll('input,textarea,button').forEach(function(e){e.disabled=true;});
        if (status) { status.textContent = msg; status.classList.add('show'); status.scrollIntoView({block:'center',behavior:'smooth'}); }
      }
      function fallback(){
        var href = 'mailto:' + TO + '?subject=' + encodeURIComponent(title)
                 + '&body=' + encodeURIComponent(body);
        window.location.href = href;
        if (status) {
          status.innerHTML = 'Your email app should open with your answers ready to send. '
            + 'If it does not, copy the text below and email it to <strong>' + TO + '</strong>.'
            + '<textarea class="fallback-box" readonly></textarea>';
          status.classList.add('show');
          status.querySelector('.fallback-box').value = body;
        }
      }
      if (KEY) {
        var payload = { access_key: KEY, subject: title, from_name: 'Maison Claire Website',
                        replyto: (groups.email && groups.email[0]) || '', message: body };
        fetch('https://api.web3forms.com/submit', {
          method: 'POST', headers: {'Content-Type':'application/json','Accept':'application/json'},
          body: JSON.stringify(payload)
        }).then(function(r){ return r.json(); })
          .then(function(d){ if (d && d.success) { done('Thank you. Your message has been sent to Stanislava. She will personally review it and be in touch soon.'); } else { fallback(); } })
          .catch(fallback);
      } else { fallback(); }
    });
  });
})();
</script>""" % (EMAIL, FORM_ACCESS_KEY)

WHAT_NEXT = f"""<section class="pad tint">
  <div class="container narrow center">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">What happens next</p><div class="rule"></div></div>
    <p class="approach-lead">I will personally review what you have shared before we speak.</p>
    <p class="approach-lead">Our consultation is simply a conversation to understand where you are, answer your questions and determine whether Maison Claire feels like the right place to begin.</p>
    <p class="disclaimer-note">{DISCLAIMER}</p>
  </div>
</section>"""

# ---- Consultation form (standard)
consult_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Request a Consultation</p>
    <h1>Let&rsquo;s begin with<br/>a conversation.</h1>
    <p>Tell me a little about what is bringing you to Maison Claire. You don&rsquo;t need to know exactly. That is something we can explore together.</p>
  </div>
</section>

<section class="pad">
  <div class="container narrow">
    <form class="mc-form" data-title="Consultation request (Maison Claire website)">
      <input type="text" name="_trap" class="trap" tabindex="-1" autocomplete="off" aria-hidden="true" />
      <div class="frow">
        {field("Name", "name", req=True)}
        {field("Email", "email", kind="email", req=True)}
      </div>
      {field("Phone", "phone", kind="tel")}
      {field("What brings you to Maison Claire at this time?", "what_brings_you", kind="textarea", req=True)}
      {field("What would you most like to change or improve?", "what_to_change", kind="textarea")}
      <div class="fgroup">
        <span class="flabel" data-label-for="areas">Which areas would you most like to explore?</span>
        <div class="checks">{checks("areas", AREA_OPTIONS)}</div>
      </div>
      <div class="fgroup">
        <span class="flabel" data-label-for="support">What kind of support are you looking for right now?</span>
        <div class="checks">{radios("support", SUPPORT_OPTIONS)}</div>
      </div>
      {field("Anything else you&rsquo;d like me to know?", "anything_else", kind="textarea")}
      <div class="fsubmit">
        <button type="submit" class="btn btn-primary">Request My Consultation</button>
      </div>
      <div class="form-status" role="status" aria-live="polite"></div>
    </form>
  </div>
</section>

{WHAT_NEXT}
{FORM_JS}"""
page("consultation", "Request a Consultation | Maison Claire Healing",
     "Request a consultation with Stanislava at Maison Claire Healing. Tell her what is bringing you here and she will personally review it before you speak.",
     consult_body, "/consultation",
     '{"@context":"https://schema.org","@type":"ContactPage","name":"Request a Consultation"}')

# ---- Private Journey application form
def form_section(title):
    return f'<div class="form-section"><span>{title}</span></div>'

APPLY_AREAS = ["Energy &amp; vitality", "Digestion &amp; gut health", "Liver &amp; body cleansing",
    "Nutrition", "Environmental exposures", "Heavy-metal exposure concerns", "Parasite concerns",
    "Sleep", "Stress &amp; overwhelm", "Emotional patterns", "Life transition", "Hypnotherapy",
    "Reiki &amp; energy work", "Intuitive guidance"]

apply_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">The Private Journey</p>
    <h1>A private 3 to 6<br/>month experience.</h1>
    <p class="apply-meta">From $4,500 &nbsp;&middot;&nbsp; By application</p>
    <p>The Private Journey is Maison Claire&rsquo;s most individualized offering. Before we begin, I would like to understand a little about you, what has brought you here, and what you are hoping to change.</p>
    <p class="apply-reassure"><em>There are no perfect answers. Simply tell me where you are right now.</em></p>
  </div>
</section>

<section class="pad">
  <div class="container narrow">
    <form class="mc-form" data-title="Private Journey application (Maison Claire website)">
      <input type="text" name="_trap" class="trap" tabindex="-1" autocomplete="off" aria-hidden="true" />

      {form_section("About You")}
      <div class="frow">
        {field("Name", "name", req=True)}
        {field("Email", "email", kind="email", req=True)}
      </div>
      <div class="frow">
        {field("Phone", "phone", kind="tel")}
        {field("Where are you located?", "location")}
      </div>
      {field("How did you hear about Maison Claire?", "referral")}

      {form_section("What Brings You Here?")}
      {field("1. What is happening in your life or wellbeing that has brought you to Maison Claire now?", "q1_bring_you", kind="textarea", req=True, rows=4)}
      {field("2. What would you most like help with?", "q2_help_with", kind="textarea", rows=4)}
      {field("3. How long have you been experiencing this?", "q3_how_long")}
      {field("4. What have you already tried?", "q4_tried", kind="textarea", rows=4, hint="What helped, and what did not?")}
      {field("5. Do you feel that your physical health, emotional wellbeing, lifestyle or environment may be connected?", "q5_connected", kind="textarea", rows=4, hint="If so, tell me a little about what you have noticed.")}

      {form_section("Your Health &amp; Wellbeing")}
      <div class="fgroup">
        <span class="flabel" data-label-for="q6_areas">6. Are there particular areas you would like to explore?</span>
        <div class="checks">{checks("q6_areas", APPLY_AREAS)}</div>
        {field("Other", "q6_other")}
      </div>
      <div class="fgroup">
        <span class="flabel" data-label-for="q7_care">7. Are you currently under the care of a physician or other healthcare practitioner for anything relevant to the reason you are applying?</span>
        <div class="checks tight">{radios("q7_care", ["Yes", "No"])}</div>
      </div>
      {field("If yes, you may briefly explain if you feel it is relevant.", "q7_care_detail", kind="textarea", rows=3)}

      {form_section("Going Deeper")}
      {field("8. If we looked beyond the immediate problem, what do you feel may be underneath it?", "q8_underneath", kind="textarea", rows=4, hint="It is completely fine if you don&rsquo;t know.")}
      {field("9. What would meaningful change look like for you six months from now?", "q9_change", kind="textarea", rows=4)}
      {field("10. What do you feel has been getting in the way of that change?", "q10_in_the_way", kind="textarea", rows=4)}
      <div class="fgroup">
        <span class="flabel" data-label-for="q11_open">11. Are you open to making changes to your daily habits, nutrition, lifestyle or environment when appropriate?</span>
        <div class="checks tight">{radios("q11_open", ["Yes", "Maybe", "Not at this time"])}</div>
      </div>

      {form_section("The Commitment")}
      <p class="form-note">The Private Journey is not a quick fix. It is intended for someone who is ready to participate actively in their own wellbeing.</p>
      {field("12. Why does this feel like the right time to do this work?", "q12_why_now", kind="textarea", rows=4)}
      <div class="fgroup">
        <span class="flabel" data-label-for="q13_dedicate">13. Are you able and willing to dedicate time between sessions to the practices or changes we agree upon?</span>
        <div class="checks tight">{radios("q13_dedicate", ["Yes", "I&rsquo;m not sure yet"])}</div>
      </div>
      <div class="fgroup">
        <span class="flabel" data-label-for="q14_investment">14. The Private Journey begins at $4,500 for 3 to 6 months, depending on the level of support we design together. If we both feel this is the right fit, are you comfortable with that level of investment?</span>
        <div class="checks tight">{radios("q14_investment", ["Yes", "I would like to discuss it", "Not at this time"])}</div>
      </div>

      {form_section("One Last Question")}
      {field("If you could ask your body, mind or deeper self one question right now, and receive a completely honest answer, what would you ask?", "q15_one_question", kind="textarea", rows=4)}

      <div class="fsubmit">
        <button type="submit" class="btn btn-primary">Apply for the Private Journey</button>
      </div>
      <div class="form-status" role="status" aria-live="polite"></div>
    </form>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow center">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">What happens next</p><div class="rule"></div></div>
    <p class="approach-lead">After I personally review your application, I will contact you if I believe the Private Journey may be a good fit.</p>
    <p class="approach-lead">We will begin with a private conversation before deciding whether to work together. Submitting an application does not commit you to the program.</p>
    <p class="disclaimer-note">Maison Claire provides complementary health and wellness support. It does not diagnose or treat medical conditions and is not a replacement for care from a licensed healthcare professional.</p>
  </div>
</section>
{FORM_JS}"""
page("apply", "Apply for the Private Journey | Maison Claire Healing",
     "Apply for The Private Journey with Stanislava at Maison Claire Healing: a private 3 to 6 month experience from $4,500, by application. She personally reviews every application.",
     apply_body, "/journeys",
     '{"@context":"https://schema.org","@type":"ContactPage","name":"Private Journey Application"}')

# ================================================================ CONTACT
contact_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Contact</p>
    <h1>A conversation that<br/>can change everything.</h1>
    <p>Your first step is a conversation. No pressure, no need to have all the answers before reaching out.</p>
    <div class="hero-cta" style="justify-content:center;margin-top:26px">
      <a href="/consultation" class="btn btn-primary">Request a Consultation</a>
      <a href="tel:{PHONE_TEL}" class="btn btn-ghost">Call or Text {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>

<section class="pad">
  <div class="container">
    <div class="contact-grid three">
      <a class="contact-card" href="tel:{PHONE_TEL}">
        <span class="contact-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M5 4h3l2 5-2.5 1.5a12 12 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg></span>
        <span class="contact-label">Call or Text Stanislava</span>
        <span class="contact-value">{PHONE_DISPLAY}</span>
      </a>
      <a class="contact-card" href="mailto:{EMAIL}">
        <span class="contact-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M3 7l9 6 9-6"/></svg></span>
        <span class="contact-label">Email</span>
        <span class="contact-value">{EMAIL}</span>
      </a>
      <div class="contact-card">
        <span class="contact-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M12 21s-7-6.4-7-11a7 7 0 0 1 14 0c0 4.6-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg></span>
        <span class="contact-label">Where</span>
        <span class="contact-value">Bowen Island, BC<br/>In-person &amp; online</span>
      </div>
    </div>
    <p class="disclaimer-note">{DISCLAIMER}</p>
  </div>
</section>

<section class="photo-band tall" style="background-image:linear-gradient(rgba(22,38,58,0.34), rgba(22,38,58,0.34)), url('/banner-village.jpg');">
  <div class="container center"><p class="band-line">A more luminous you begins with a single conversation.</p></div>
</section>"""
contact_ld = '{"@context":"https://schema.org","@type":"ContactPage","name":"Contact Maison Claire Healing","mainEntity":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire Healing","email":"%s","telephone":"%s","areaServed":"Bowen Island, British Columbia","url":"%s"}}' % (EMAIL, PHONE_DISPLAY, BASE)
page("contact", "Contact | Maison Claire Healing, Bowen Island",
     "Contact Stanislava at Maison Claire Healing. Call or text 604-841-4833, email booking@MaisonClaireHealing.com. Bowen Island, in-person and online.",
     contact_body, "/contact", contact_ld)

# ---------------------------------------------------------------- sitemap + robots
urls = ["/", "/journeys", "/the-first-step", "/the-reset", "/the-root", "/restore",
        "/the-private-journey", "/approach", "/about", "/consultation", "/apply", "/contact"]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    pr = "1.0" if u == "/" else "0.8"
    sm += f"  <url><loc>{BASE}{u}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>\n"
sm += "</urlset>\n"
with open(os.path.join(HERE, "sitemap.xml"), "w") as f:
    f.write(sm)
with open(os.path.join(HERE, "robots.txt"), "w") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

# remove stale pages from previous structures
for old in ["services", "reiki-healing", "hypnotherapy-intuitive-guidance", "liver-cleanse-detox",
            "root-cause-healing", "faq", "the-shift", "the-reconnection", "the-next-chapter",
            "the-deep-dive"]:
    p = os.path.join(HERE, old + ".html")
    if os.path.exists(p):
        os.remove(p)

print("Built:", ", ".join(urls))
print("Wrote sitemap.xml and robots.txt; removed stale pages")
