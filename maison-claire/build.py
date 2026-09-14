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
    ("About", "/about"),
    ("Services", "/services"),
    ("Reiki Healing", "/reiki-healing"),
    ("FAQ", "/faq"),
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
        <a href="/about">About</a>
        <a href="/services">Services</a>
        <a href="/faq">FAQ</a>
        <a href="/contact">Contact</a>
      </div>
      <div class="foot-col">
        <h4>Sessions</h4>
        <a href="/reiki-healing">Reiki Healing</a>
        <a href="/hypnotherapy-intuitive-guidance">Hypnotherapy &amp; Guidance</a>
        <a href="/liver-cleanse-detox">Liver Cleanse &amp; Detox</a>
        <a href="/root-cause-healing">Root Cause Healing</a>
        <a href="mailto:{EMAIL}">{EMAIL}</a>
        <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>
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
    <div class="center" style="margin-top:34px"><a href="/contact" class="btn btn-ghost">Explore the Journey</a></div>
  </div>
</section>

<section class="feature-band" style="background-image:linear-gradient(90deg, rgba(22,38,58,0.72), rgba(22,38,58,0.30)), url('/lighthouse-blue.jpg');">
  <div class="container feature-inner">
    <div class="feature-card">
      <p class="eyebrow" style="color:var(--gold-soft)">Healing from the inside out</p>
      <h2>We look deeper.<br/>Beyond the surface.</h2>
      <p>Because true healing is not just about what you can see. It is about what lies beneath, in the physical, emotional, and energetic patterns that shape how you feel and live.</p>
      <a href="/services" class="btn btn-ghost light">The Maison Claire Approach</a>
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

# ---- About
about_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">About Maison Claire</p>
    <h1>A gentle space to remember your wholeness.</h1>
    <p>Ancient wisdom and intuitive care, held together with warmth, so you can heal from the inside out.</p>
  </div>
</section>

<section class="pad">
  <div class="container narrow prose">
    <p class="lead">Maison Claire is a sanctuary for those who feel called to heal from the inside out. We hold space for the whole person, body, mind, and spirit, weaving together time honoured healing traditions with intuitive care.</p>
    <p>Every session is created around you: your story, your rhythm, and the quiet signals your body has been waiting to share. Together we uncover the root of what is asking to be released, so you can return to your natural state of clarity, energy, and light.</p>

    <h2>Meet Stanislava</h2>
    <p>Sessions at Maison Claire are guided by Stanislava, a natural healing practitioner devoted to helping people feel at home in themselves again. Her work blends Reiki, hypnotherapy, intuitive guidance, and gentle detox support into a calm, personal experience.</p>
    <p>Stanislava believes healing is not something done to you. It is a partnership. Her role is to hold a steady, compassionate space while your body remembers how to restore itself.</p>

    <h2>What we believe</h2>
    <ul>
      <li><strong>Treat the root, not only the symptom.</strong> Lasting change comes from understanding what lies beneath.</li>
      <li><strong>The body is wise.</strong> Given the right support, it knows how to return to balance.</li>
      <li><strong>Healing is holistic.</strong> Body, mind, and spirit move together, so we care for all three.</li>
      <li><strong>Gentleness is powerful.</strong> Real transformation can feel soft, safe, and unhurried.</li>
    </ul>
  </div>
</section>

<section class="pad tint">
  <div class="container center">
    <div class="section-head"><div class="rule"></div><p class="eyebrow">How Sessions Flow</p><div class="rule"></div></div>
    <div class="steps">
      <div class="step"><span class="step-num">01</span><h3>Listen</h3><p>A warm, unhurried conversation about how you feel and what you long to release.</p></div>
      <div class="step"><span class="step-num">02</span><h3>Uncover</h3><p>Energy work and intuitive guidance to look beneath the symptoms for the root cause.</p></div>
      <div class="step"><span class="step-num">03</span><h3>Restore</h3><p>You leave lighter, supported, and reconnected to your own natural knowing.</p></div>
    </div>
  </div>
</section>

{cta_band("Ready when you are", "Reach out to Stanislava to begin your natural path back to balance.")}"""

about_ld = """{"@context":"https://schema.org","@type":"AboutPage","name":"About Maison Claire","about":{"@type":"Person","name":"Stanislava","jobTitle":"Natural Healing Practitioner","worksFor":{"@type":"Organization","name":"Maison Claire"}}}"""

page("about", "About Maison Claire | Natural Healing with Stanislava",
     "Meet Stanislava and the philosophy behind Maison Claire: root cause healing that blends Reiki, hypnotherapy, and intuitive care for body, mind, and spirit.",
     about_body, "/about", about_ld)

# ---- Services hub
services_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Our Services</p>
    <h1>Ways we can heal together.</h1>
    <p>Each session is tailored to you. Explore the paths below, or reach out and we will find the right starting point together.</p>
  </div>
</section>

<section class="pad">
  <div class="container">
    {services_diamond(SERVICES, center='<em>Your Health.<br/>Your Power.<br/>Your Natural Path.</em>')}
  </div>
</section>

{cta_band()}"""

services_ld = """{"@context":"https://schema.org","@type":"ItemList","name":"Maison Claire Services","itemListElement":[{"@type":"ListItem","position":1,"name":"Reiki Healing","url":"%s/reiki-healing"},{"@type":"ListItem","position":2,"name":"Hypnotherapy and Intuitive Guidance","url":"%s/hypnotherapy-intuitive-guidance"},{"@type":"ListItem","position":3,"name":"Liver Cleanse and Detox","url":"%s/liver-cleanse-detox"},{"@type":"ListItem","position":4,"name":"Root Cause Healing","url":"%s/root-cause-healing"}]}""" % (BASE, BASE, BASE, BASE)

page("services", "Services | Reiki, Hypnotherapy, Detox & Root Cause Healing",
     "Explore Maison Claire services: Reiki healing, hypnotherapy and intuitive guidance, liver cleanse and detox, and root cause healing, each tailored to you.",
     services_body, "/services", services_ld)

# ---- Service detail template
def service_page(slug, icon, name_html, plain_name, title, desc, intro, whatis, helps, expect, ld_name):
    helps_li = "".join(f"<li>{h}</li>" for h in helps)
    body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Maison Claire Services</p>
    <h1>{name_html}</h1>
    <p>{intro}</p>
  </div>
</section>

<section class="pad-sm">
  <div class="container">
    <div class="split">
      <div class="prose">
        <h2>What it is</h2>
        <p>{whatis}</p>
        <h3>How it may help</h3>
        <ul>{helps_li}</ul>
      </div>
      <div class="media"><img class="crest-mark" src="/crest-mark.png" alt="" aria-hidden="true" /></div>
    </div>
  </div>
</section>

<section class="pad tint">
  <div class="container narrow prose">
    <h2>What to expect</h2>
    <p>{expect}</p>
    <p>Every session is gentle, personal, and paced to you. There is nothing to prepare and nothing to prove. You simply arrive as you are.</p>
  </div>
</section>

{cta_band("Book " + plain_name, "Reach out to Stanislava to arrange your session.")}"""
    jsonld = """{"@context":"https://schema.org","@type":"Service","serviceType":"%s","provider":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire"},"areaServed":"Greater Vancouver","description":"%s","url":"%s/%s"}""" % (ld_name, desc.replace('"',''), BASE, slug)
    page(slug, title, desc, body, "/reiki-healing" if slug=="reiki-healing" else "/services", jsonld)

service_page(
    "reiki-healing", "rays", "Reiki Healing", "Reiki Healing",
    "Reiki Healing | Maison Claire",
    "Reiki healing at Maison Claire helps restore energetic balance, reduce stress, and support your body&rsquo;s natural healing on every level.",
    "A calm, hands light energy practice that helps your whole system settle, so healing can begin.",
    "Reiki is a gentle energy healing practice. Through light, resting hand positions, it encourages your nervous system to soften out of stress and into a state where restoration becomes possible. Nothing is forced. The work simply supports the balance your body is always reaching for.",
    ["Reduce stress and quiet a busy mind",
     "Restore a sense of energetic balance and calm",
     "Ease tension held in the body",
     "Support rest, sleep, and emotional release",
     "Complement other healing and medical care"],
    "You rest fully clothed and comfortable while Stanislava works through a series of gentle hand positions. Many people feel warmth, a deep calm, or simply drift into rest. Afterwards there is space to sit quietly and return in your own time.",
    "Reiki Healing")

service_page(
    "hypnotherapy-intuitive-guidance", "caduceus", "Hypnotherapy &amp; Intuitive Guidance", "Hypnotherapy & Intuitive Guidance",
    "Hypnotherapy & Intuitive Guidance | Maison Claire",
    "Hypnotherapy and intuitive guidance at Maison Claire help you clear blocks, release old patterns, and reconnect with your inner wisdom for lasting transformation.",
    "Clear blocks, release old patterns, and reconnect with your inner wisdom for lasting transformation.",
    "Working with the calm, focused state of hypnosis alongside intuitive guidance, we gently explore the patterns and beliefs that keep you stuck. In this relaxed state, the mind becomes open and receptive, making it easier to release what no longer serves you and invite in what does.",
    ["Release limiting patterns and old stories",
     "Soften anxiety, overwhelm, and self doubt",
     "Reconnect with your intuition and inner wisdom",
     "Support meaningful, lasting change",
     "Bring clarity to a decision or a season of transition"],
    "You remain relaxed, aware, and fully in control throughout. Stanislava guides you into a calm, focused state and, with intuitive care, helps you gently work with what surfaces. Sessions are collaborative and always paced to your comfort.",
    "Hypnotherapy and Intuitive Guidance")

service_page(
    "liver-cleanse-detox", "lotus", "Liver Cleanse &amp; Detox", "Liver Cleanse & Detox",
    "Liver Cleanse & Detox | Maison Claire",
    "Liver cleanse and detox support at Maison Claire helps your body&rsquo;s natural detoxification, resets your energy, and restores balance.",
    "Support your body&rsquo;s natural detoxification, reset your energy, and restore balance.",
    "Your body is designed to cleanse itself. This gentle, guided support helps that natural process along, easing the load on your system so you can feel lighter, clearer, and more energised. It is a nourishing reset rather than a harsh regime.",
    ["Support the body&rsquo;s natural detoxification",
     "Reset and lift your everyday energy",
     "Ease bloating and heaviness",
     "Encourage clearer skin and brighter mornings",
     "Restore a sense of overall balance"],
    "We begin by understanding how you feel day to day, then create a supportive, realistic plan for your cleanse. You receive gentle guidance throughout, so the process feels steady and doable rather than overwhelming.",
    "Liver Cleanse and Detox")

service_page(
    "root-cause-healing", "spiral", "Root Cause Healing", "Root Cause Healing",
    "Root Cause Healing | Maison Claire",
    "Root cause healing at Maison Claire looks beneath the symptoms, so your body, mind, and spirit can return to their natural state of healing.",
    "Uncover the root cause, so your body, mind, and spirit can return to their natural state of healing.",
    "Symptoms are messengers. Root cause healing is the thread that runs through all of our work: rather than only quieting the surface, we look gently beneath it for what is truly asking to be addressed. When the root is cared for, the whole system can find its way back to balance.",
    ["Understand what lies beneath recurring symptoms",
     "Address the cause, not only the signs",
     "Bring body, mind, and spirit back into alignment",
     "Create change that lasts",
     "Feel truly heard and cared for as a whole person"],
    "Root cause healing weaves through your sessions. We take time to listen, notice patterns, and follow what your body and story reveal, then choose the supportive practices that fit you best.",
    "Root Cause Healing")

# ---- FAQ
faqs = [
    ("What happens in a first session?",
     "We start with a relaxed conversation about how you feel and what you hope for. From there, Stanislava tailors the session to you. There is nothing to prepare in advance."),
    ("Is Reiki or energy healing safe?",
     "Yes. Reiki is gentle and non invasive. You remain fully clothed and comfortable throughout. It is designed to complement, not replace, medical care."),
    ("Do I need to believe in it for it to work?",
     "No. You are welcome to arrive curious, unsure, or simply open. Many people feel calmer and lighter regardless of what they expected."),
    ("How many sessions will I need?",
     "That depends on you and what you are working with. Some people come for a single reset, others enjoy ongoing support. We will find a rhythm that suits you."),
    ("Is this a replacement for medical treatment?",
     "No. Maison Claire offers natural, complementary wellbeing support. Please continue to work with your doctor and follow their advice for medical concerns."),
    ("How do I book?",
     "Reach out by email at %s or call %s. We will find a time that works and answer any questions before you begin." % (EMAIL, PHONE_DISPLAY)),
]
faq_items = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
faq_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Questions &amp; Answers</p>
    <h1>Frequently asked questions.</h1>
    <p>A few things people often ask before their first visit. If your question is not here, we would love to hear from you.</p>
  </div>
</section>

<section class="pad">
  <div class="container">
    <div class="faq">{faq_items}</div>
  </div>
</section>

{cta_band("Still have a question?", "Reach out to Stanislava and we will be glad to help.")}"""
faq_ld = "{" + '"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + ",".join(
    '{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}' % (q, a.replace('"',''))
    for q, a in faqs) + "]}"
page("faq", "FAQ | Maison Claire Natural Healing",
     "Answers to common questions about Reiki, hypnotherapy, detox, and root cause healing at Maison Claire, and how to book with Stanislava.",
     faq_body, "/faq", faq_ld)

# ---- Contact
contact_body = f"""<section class="page-hero">
  <div class="container">
    <p class="eyebrow">Book Your Session</p>
    <h1>Begin your natural path.</h1>
    <p>Book a session with Stanislava or ask a question. We would love to hear from you and help you take the first gentle step.</p>
  </div>
</section>

<section class="pad">
  <div class="container">
    <div class="contact-grid">
      <a class="contact-card" href="mailto:{EMAIL}">
        <span class="contact-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M3 7l9 6 9-6"/></svg></span>
        <span class="contact-label">Email</span>
        <span class="contact-value">{EMAIL}</span>
      </a>
      <a class="contact-card" href="tel:{PHONE_TEL}">
        <span class="contact-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M5 4h3l2 5-2.5 1.5a12 12 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg></span>
        <span class="contact-label">Phone</span>
        <span class="contact-value">{PHONE_DISPLAY}</span>
      </a>
    </div>
    <p class="contact-note">Book your session with Stanislava. Every enquiry is welcome, whether you are ready to begin or simply exploring.</p>
  </div>
</section>

<section class="pad-sm quote">
  <div class="container">
    <blockquote><span class="mark" aria-hidden="true">&ldquo;</span>Your Health. Your Power. Your Natural Path.<cite>Maison Claire</cite></blockquote>
  </div>
</section>"""
contact_ld = """{"@context":"https://schema.org","@type":"ContactPage","name":"Contact Maison Claire","mainEntity":{"@type":"HealthAndBeautyBusiness","name":"Maison Claire","email":"%s","telephone":"%s","url":"%s"}}""" % (EMAIL, PHONE_DISPLAY, BASE)
page("contact", "Contact & Booking | Maison Claire",
     "Book a Reiki, hypnotherapy, detox, or root cause healing session with Stanislava at Maison Claire. Email booking@MaisonClaireHealing.com or call 604-841-4833.",
     contact_body, "/contact", contact_ld)

# ---------------------------------------------------------------- sitemap + robots
urls = ["/", "/about", "/services", "/reiki-healing", "/hypnotherapy-intuitive-guidance",
        "/liver-cleanse-detox", "/root-cause-healing", "/faq", "/contact"]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    pr = "1.0" if u == "/" else "0.8"
    sm += f"  <url><loc>{BASE}{u}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>\n"
sm += "</urlset>\n"
with open(os.path.join(HERE, "sitemap.xml"), "w") as f:
    f.write(sm)

with open(os.path.join(HERE, "robots.txt"), "w") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

print("Built:", ", ".join(urls))
print("Wrote sitemap.xml and robots.txt")
