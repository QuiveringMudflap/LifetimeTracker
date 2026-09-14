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
    <a href="/" class="nav-brand" aria-label="Maison Claire Healing home"><img src="/logo-navy.png" alt="Maison Claire Healing" width="432" height="186" /></a>
    <nav class="nav-links" aria-label="Primary">{items}</nav>
    <a href="/contact" class="nav-cta">Request a Consultation</a>
    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>"""

FOOTER = f"""<footer class="foot">
  <div class="container">
    <div class="foot-top">
      <div class="foot-brand-block">
        <img src="/logo-navy-light.png" alt="Maison Claire Healing" />
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
        <a href="/the-reset">The Reset</a>
        <a href="/the-shift">The Shift</a>
        <a href="/the-reconnection">The Reconnection</a>
        <a href="/the-next-chapter">The Next Chapter</a>
        <a href="/the-deep-dive">The Deep Dive</a>
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
                  "/mountains.jpg", "/grassland.jpg", "/horses.jpg"]:
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
      <a href="/contact" class="btn btn-primary">Request a Consultation</a>
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
    <p class="ph-eyebrow">A private space for deeper change</p>
    <h1 class="ph-title">Come back<br/>to yourself.</h1>
    <p class="ph-lead">Sometimes we know something isn&rsquo;t working, but we don&rsquo;t know why. Maison Claire offers a personalized approach to exploring the physical, emotional, and inner patterns that may be keeping you from feeling fully yourself.</p>
    <div class="hero-cta">
      <a href="/contact" class="btn btn-primary">Request a Private Consultation</a>
    </div>
  </div>
</section>

<section class="pad">
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

# ================================================================ JOURNEYS
JOURNEYS = [
    ("the-reset", "The Reset", "Return to balance.", "lighthouse-warm.jpg"),
    ("the-shift", "The Shift", "Change what keeps repeating.", "mountains.jpg"),
    ("the-reconnection", "The Reconnection", "Come back to yourself.", "hero.jpg"),
    ("the-next-chapter", "The Next Chapter", "Move consciously into what comes next.", "horses.jpg"),
    ("the-deep-dive", "The Deep Dive", "Go beneath the surface.", "lighthouse-blue.jpg"),
]

def journey_row(slug, name, tagline, img):
    return f"""<a class="journey-row" href="/{slug}">
      <span class="jr-img" style="background-image:url('/{img}')"></span>
      <span class="jr-text"><span class="jr-name">{name}</span><span class="jr-tag">{tagline}</span></span>
      <span class="jr-arrow" aria-hidden="true">&rarr;</span>
    </a>"""

journeys_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Journeys</p>
    <h1>Different places.<br/>The same destination: you.</h1>
    <p>Every journey at Maison Claire is private and personal. Explore the paths below, or begin with a conversation and we will find the one that fits.</p>
  </div>
</section>

<section class="pad">
  <div class="container narrow">
    <div class="journey-list">{''.join(journey_row(*j) for j in JOURNEYS)}</div>
  </div>
</section>

<section class="pad tint">
  <div class="container center">
    <h2 class="approach-title" style="max-width:640px;margin:0 auto 14px">Not sure which journey is yours?</h2>
    <p class="approach-lead">You do not have to decide before you arrive. We begin with a conversation.</p>
    <a href="/contact" class="btn btn-primary">Request a Private Consultation</a>
  </div>
</section>"""
journeys_ld = ('{"@context":"https://schema.org","@type":"ItemList","name":"Maison Claire Journeys","itemListElement":['
    + ",".join('{"@type":"ListItem","position":%d,"name":"%s","url":"%s/%s"}' % (i+1, j[1], BASE, j[0]) for i, j in enumerate(JOURNEYS))
    + "]}")
page("journeys", "Journeys | Maison Claire Healing with Stanislava",
     "Private, personal healing journeys with Stanislava at Maison Claire: The Reset, The Shift, The Reconnection, The Next Chapter, and The Deep Dive.",
     journeys_body, "/journeys", journeys_ld)

def journey_page(slug, name, tagline, img, whatis, includes, foryou, mtitle, mdesc):
    wp = "".join(f"<p>{p}</p>" for p in whatis)
    inc = "".join(f"<li>{x}</li>" for x in includes)
    fyi = "".join(f"<li>{x}</li>" for x in foryou)
    body = f"""<section class="photo-hero journey-hero" style="background-image:linear-gradient(90deg, rgba(22,38,58,0.82) 0%, rgba(22,38,58,0.40) 55%, rgba(22,38,58,0.08) 100%), url('/{img}');">
  <div class="container photo-hero-inner">
    <p class="ph-eyebrow">A Maison Claire Journey</p>
    <h1 class="ph-title">{name}</h1>
    <p class="ph-lead">{tagline}</p>
    <div class="hero-cta"><a href="/contact" class="btn btn-primary">Request a Private Consultation</a></div>
  </div>
</section>

<section class="pad">
  <div class="container split-approach">
    <div class="prose">{wp}</div>
    <div class="journey-include">
      <p class="eyebrow">Your journey may include</p>
      <ul>{inc}</ul>
      <p class="include-note">Every journey is individual. There is no predetermined formula, only what is right for you.</p>
    </div>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">This journey is for you if</p><div class="rule"></div></div>
    <ul class="foryou">{fyi}</ul>
  </div>
</section>

{cta_band()}"""
    ld = '{"@context":"https://schema.org","@type":"Service","serviceType":"%s","provider":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire"},"areaServed":"Bowen Island, British Columbia","description":"%s","url":"%s/%s"}' % (name, mdesc.replace('"', ''), BASE, slug)
    page(slug, mtitle, mdesc, body, "/journeys", ld)

journey_page("the-reset", "The Reset", "A return to balance, from the inside out.", "lighthouse-warm.jpg",
    ["Sometimes the body asks us to slow down before the mind is ready to listen. You may feel depleted, foggy, disconnected, or simply not quite like yourself.",
     "The Reset is a private, whole-person healing journey designed to support you from the inside out. Together we gently clear what has accumulated, physically, emotionally, and energetically, and create a healthier foundation for the next chapter."],
    ["Supportive cleansing and nutrition", "Sound and light", "Intuitive guidance", "Hypnotherapy", "Reiki and energy work", "Personalized practices"],
    ["You feel your energy and vitality have changed", "You feel physically or emotionally weighed down", "You want to make meaningful changes to the way you care for yourself", "You are curious about supporting your body through cleansing and healthier practices", "You feel disconnected from yourself and want to come back into balance"],
    "The Reset | Maison Claire Healing",
    "The Reset is a private, whole-person healing journey with Stanislava: a gentle return to balance through cleansing, energy work, and personalized care on Bowen Island.")

journey_page("the-shift", "The Shift", "Change what keeps repeating.", "mountains.jpg",
    ["Some patterns follow us for years: the same reactions, the same stories, the same quiet limits on what feels possible.",
     "The Shift works gently with hypnotherapy and intuitive guidance to loosen those patterns at the root, so you can meet life from a freer, clearer place."],
    ["Hypnotherapy", "Intuitive guidance", "Reiki and energy work", "Gentle inquiry and reflection", "Personalized practices"],
    ["You keep repeating a pattern you cannot seem to shift", "You feel held back by old beliefs or stories", "You are ready to respond to life differently", "You want lasting change, not a quick fix", "You are curious about what lies beneath the surface"],
    "The Shift | Maison Claire Healing",
    "The Shift uses hypnotherapy and intuitive guidance with Stanislava to release old patterns and beliefs at the root, for lasting, gentle change.")

journey_page("the-reconnection", "The Reconnection", "Come back to yourself.", "hero.jpg",
    ["Life can pull us far from our own centre. The Reconnection is a gentle way home: to your body, your intuition, and your sense of who you are.",
     "Through energy work, intuitive guidance, and time in stillness, we rebuild the quiet trust between you and yourself."],
    ["Reiki and energy work", "Intuitive guidance", "Grounding and nature-based practices", "Breath and stillness", "Personalized practices"],
    ["You feel disconnected from yourself", "You have been living in your head more than your body", "You long for more calm, clarity, and presence", "You want to hear your own inner voice again", "You are ready to feel at home in yourself"],
    "The Reconnection | Maison Claire Healing",
    "The Reconnection is a gentle journey back to yourself with Stanislava, rebuilding trust with your body and intuition through energy work and stillness.")

journey_page("the-next-chapter", "The Next Chapter", "Move consciously into what comes next.", "horses.jpg",
    ["Every threshold, a move, a loss, a new season, asks something of us. The Next Chapter offers steady, compassionate support as you move through change with intention.",
     "Rather than rushing forward, we make space to honour what is ending and to step consciously into what is beginning."],
    ["Intuitive guidance", "Hypnotherapy", "Reiki and energy work", "Reflection and ritual", "Personalized practices"],
    ["You are moving through a major life transition", "You feel between chapters and unsure of the way forward", "You want to move forward with clarity and intention", "You are ready to release what is complete", "You want support as you begin again"],
    "The Next Chapter | Maison Claire Healing",
    "The Next Chapter supports you through life transitions with Stanislava, moving consciously into what comes next with clarity, intention, and care.")

journey_page("the-deep-dive", "The Deep Dive", "Go beneath the surface.", "lighthouse-blue.jpg",
    ["For those who feel called to explore further, The Deep Dive opens into the spiritual dimension of healing, including mediumship and connection with spirit.",
     "The emphasis of this work is mediumship: making connections with, and delivering messages from, those who are no longer living to those who still are. Working as a mental medium, Stanislava receives messages through the clairs, hearing, seeing, knowing, and feeling, acting as a bridge between the spiritual and physical worlds, with the intention of healing both."],
    ["Mediumship and spirit connection", "Intuitive and spiritual guidance", "Reiki and energy work", "Connection with guides and ancestors", "Personalized practices"],
    ["You are seeking to connect with your spirit guides or loved ones on the other side", "You feel drawn to the spiritual side of healing", "You are looking for clarity, meaning, or closure", "You are open to messages that arrive with love", "You want to explore what lies beneath the surface"],
    "The Deep Dive | Maison Claire Healing",
    "The Deep Dive opens into the spiritual side of healing with Stanislava, including mediumship and connection with spirit guides, ancestors, and loved ones.")

# ================================================================ APPROACH
APPROACH_MOD = [
    ("spiral", "Root-Cause Exploration"),
    ("lotus", "Cleansing &amp; Nutrition"),
    ("sun2b", "Sound &amp; Light"),
    ("caduceus", "Hypnotherapy"),
    ("rays", "Reiki &amp; Energy Work"),
    ("eyeb", "Intuitive Guidance"),
    ("leaf", "Nature &amp; Environment"),
]
_AP_INLINE = {
 "sun2b": '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="9" fill="none" stroke="#fff" stroke-width="1.5"/><g stroke="#fff" stroke-width="1.4" stroke-linecap="round"><line x1="32" y1="10" x2="32" y2="17"/><line x1="32" y1="47" x2="32" y2="54"/><line x1="10" y1="32" x2="17" y2="32"/><line x1="47" y1="32" x2="54" y2="32"/><line x1="16" y1="16" x2="21" y2="21"/><line x1="43" y1="43" x2="48" y2="48"/><line x1="48" y1="16" x2="43" y2="21"/><line x1="21" y1="43" x2="16" y2="48"/></g></svg>',
 "eyeb": '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M12 32 Q32 16 52 32 Q32 48 12 32 Z" fill="none" stroke="#fff" stroke-width="1.5"/><circle cx="32" cy="32" r="6" fill="none" stroke="#fff" stroke-width="1.5"/></svg>',
}
def _apicon(key):
    return _AP_INLINE.get(key) or IC.get(key) or ""
approach_mods_html = "".join(
    f'<div class="apmod"><span class="apmod-ic">{_apicon(k)}</span><span>{n}</span></div>' for k, n in APPROACH_MOD)

APPROACH_STEPS = [
    ("Discover", "Look beneath the surface."),
    ("Clear", "Support the body&rsquo;s natural processes."),
    ("Rebalance", "Bring body, mind, and emotions into harmony."),
    ("Reconnect", "Work with intuition, light, and energy."),
    ("Restore", "Feel more whole, calm, and connected."),
]
approach_steps_html = "".join(
    f'<div class="step"><span class="step-num">0{i+1}</span><h3>{n}</h3><p>{d}</p></div>'
    for i, (n, d) in enumerate(APPROACH_STEPS))

approach_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">The Maison Claire Approach</p>
    <h1>Healing begins beneath the surface.</h1>
    <p>We look at the whole person, body, mind, and spirit, and the many influences that shape how you feel and live.</p>
  </div>
</section>

<section class="pad">
  <div class="container narrow prose center-prose">
    <p class="lead">Rather than focusing only on what is showing up on the surface, we explore what may be contributing to it at a deeper level.</p>
    <p>Our approach may draw from root-cause exploration, supportive cleansing and nutrition, sound and light, hypnotherapy, Reiki and energy work, intuitive guidance, and connection with nature. Each is simply a different doorway.</p>
  </div>
  <div class="container" style="margin-top:40px">
    <div class="apmods">{approach_mods_html}</div>
  </div>
</section>

<section class="pad tint">
  <div class="container center">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">How healing unfolds</p><div class="rule"></div></div>
    <div class="steps five">{approach_steps_html}</div>
  </div>
</section>

<section class="bms">
  <div class="container center">
    <p class="bms-line">Body &nbsp;&middot;&nbsp; Mind &nbsp;&middot;&nbsp; Spirit</p>
  </div>
</section>

{cta_band()}"""
approach_ld = '{"@context":"https://schema.org","@type":"MedicalWebPage","name":"The Maison Claire Approach","about":"Whole-person natural healing: root-cause exploration, cleansing and nutrition, sound and light, hypnotherapy, Reiki and energy work, intuitive guidance, and nature."}'
page("approach", "The Approach | Whole-Person Healing at Maison Claire",
     "The Maison Claire approach to whole-person healing with Stanislava: root-cause exploration, cleansing, sound and light, hypnotherapy, Reiki, intuitive guidance, and nature.",
     approach_body, "/approach", approach_ld)

# ================================================================ ABOUT
about_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">About</p>
    <h1>My path led me here.<br/>And yours can too.</h1>
    <p>Real healing is not about becoming someone new. It is about remembering who you already are.</p>
  </div>
</section>

<section class="pad">
  <div class="container split-about">
    <div class="about-photo"><img src="/portrait.jpg" alt="Stanislava, founder of Maison Claire Healing" width="1500" height="1000" /></div>
    <div class="prose">
      <p class="eyebrow">I&rsquo;m Stanislava</p>
      <h2 class="approach-title">A guide, and a fellow traveller.</h2>
      <p>For many years, I have been drawn to the healing power of nature, the wisdom of the body, and the invisible energies that shape our lives. My path has led me to bring together a range of complementary practices, not as a formula, but as a personalized approach to support each person who comes here.</p>
      <p>Maison Claire was born from a deep belief in the incredible capacity we all have to heal, to grow, and to come back to ourselves.</p>
    </div>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow prose">
    <p class="eyebrow">Mediumship</p>
    <h2>A bridge between two worlds.</h2>
    <p>The emphasis of my work is mediumship: making connections with, and delivering messages from, people who are no longer living to those who still are. I receive information primarily and directly from spirit guides, angels, and from those who have passed.</p>
    <p>While there are a number of forms of mediumship, I work as a mental medium, meaning I communicate with spirits through telepathy. Spirits impress my mind and body with thoughts and feelings that come in through the clairs. Mentally I hear (clairaudience), see (clairvoyance), know (claircognizance), and feel (clairsentience) messages from spirit.</p>
    <p>I act as the bridge between the spiritual and the physical world, with the intention of healing both.</p>
  </div>
</section>

<section class="pad quote">
  <div class="container">
    <blockquote><span class="mark" aria-hidden="true">&ldquo;</span>Healing is not about becoming someone different, but about removing what has obscured who you already are.</blockquote>
  </div>
</section>

<section class="pad testimonial-sec">
  <div class="container narrow center">
    <span class="mark" aria-hidden="true">&ldquo;</span>
    <blockquote class="testimonial">Stani is a natural intuitive. Her ability to connect to the Spirit World, to hear the clear messages from our passed ancestors and to relay them in a healing way is truly beautiful. If you are seeking to connect to your spirit guides, your family on the &lsquo;other side&rsquo; (human and animal), or just to get some clarity, I recommend a session with Stani.</blockquote>
    <cite>Andrea &middot; @nectaryoga</cite>
  </div>
</section>

{cta_band()}"""
about_ld = '{"@context":"https://schema.org","@type":"AboutPage","name":"About Maison Claire","about":{"@type":"Person","name":"Stanislava","jobTitle":"Healing Practitioner and Medium","worksFor":{"@type":"Organization","name":"Maison Claire Healing"}}}'
page("about", "About Stanislava | Maison Claire Healing",
     "Meet Stanislava, founder of Maison Claire Healing on Bowen Island. A whole-person healing practitioner and medium working with intuition, energy, and spirit.",
     about_body, "/about", about_ld)

# ================================================================ CONTACT
CONTACT_STEPS = [
    ("Reach Out", "Send a message or call to book your free consultation."),
    ("Connect", "We have a relaxed, private conversation about where you are."),
    ("Create", "Together we shape the journey that is right for you."),
]
contact_steps_html = "".join(
    f'<div class="step"><span class="step-num">0{i+1}</span><h3>{n}</h3><p>{d}</p></div>'
    for i, (n, d) in enumerate(CONTACT_STEPS))

contact_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Private Consultation</p>
    <h1>A conversation that<br/>can change everything.</h1>
    <p>Your first step is a free 15-minute conversation. No pressure, no need to have all the answers before reaching out.</p>
    <div class="hero-cta" style="justify-content:center;margin-top:26px">
      <a href="tel:{PHONE_TEL}" class="btn btn-primary">Call or Text {PHONE_DISPLAY}</a>
      <a href="mailto:{EMAIL}" class="btn btn-ghost">Email Stanislava</a>
    </div>
  </div>
</section>

<section class="pad">
  <div class="container narrow prose center-prose">
    <h2>Your first step</h2>
    <p>You do not need to arrive knowing exactly what you need. Your first private consultation is a confidential conversation about where you are, what has brought you here, and what you would like to change. From there, we can find the approach and journey that feel right for you.</p>
  </div>
  <div class="container center" style="margin-top:34px">
    <div class="steps">{contact_steps_html}</div>
  </div>
</section>

<section class="pad tint">
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
    <p class="contact-note">A more luminous you begins with a single conversation.</p>
  </div>
</section>"""
contact_ld = '{"@context":"https://schema.org","@type":"ContactPage","name":"Contact Maison Claire Healing","mainEntity":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire Healing","email":"%s","telephone":"%s","areaServed":"Bowen Island, British Columbia","url":"%s"}}' % (EMAIL, PHONE_DISPLAY, BASE)
page("contact", "Contact & Free Consultation | Maison Claire Healing",
     "Book a free 15-minute consultation with Stanislava at Maison Claire Healing. Call or text 604-841-4833, email booking@MaisonClaireHealing.com. Bowen Island, in-person and online.",
     contact_body, "/contact", contact_ld)

# ---------------------------------------------------------------- sitemap + robots
urls = ["/", "/journeys", "/the-reset", "/the-shift", "/the-reconnection",
        "/the-next-chapter", "/the-deep-dive", "/approach", "/about", "/contact"]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    pr = "1.0" if u == "/" else "0.8"
    sm += f"  <url><loc>{BASE}{u}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>\n"
sm += "</urlset>\n"
with open(os.path.join(HERE, "sitemap.xml"), "w") as f:
    f.write(sm)
with open(os.path.join(HERE, "robots.txt"), "w") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

# remove stale pages from the previous structure
for old in ["services", "reiki-healing", "hypnotherapy-intuitive-guidance",
            "liver-cleanse-detox", "root-cause-healing", "faq"]:
    p = os.path.join(HERE, old + ".html")
    if os.path.exists(p):
        os.remove(p)

print("Built:", ", ".join(urls))
print("Wrote sitemap.xml and robots.txt; removed stale pages")
