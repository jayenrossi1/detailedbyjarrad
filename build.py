#!/usr/bin/env python3
"""Assemble index.html from the _src parts, data.json and the inlined assets.

    python3 build.py          draft preview: banner and noindex (default)
    python3 build.py --live   live site: no banner, indexable

Everything is inlined (font, logo, CSS, JS), so the page makes no requests
of its own after it loads.
"""
import base64
import datetime as dt
import html
import json
import pathlib
from urllib.parse import quote
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "_src"
LIVE = "--live" in sys.argv[1:]


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def data_uri(relative, mime):
    raw = (ROOT / relative).read_bytes()
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def esc(value):
    return html.escape(str(value or "").strip(), quote=True)


def tel(number):
    return "tel:" + "".join(ch for ch in number if ch.isdigit() or ch == "+")


def intl_digits(number):
    """Australian number to international digits for WhatsApp: 0412 345 678 -> 61412345678."""
    digits = "".join(ch for ch in number if ch.isdigit())
    if number.strip().startswith("+"):
        return digits
    if digits.startswith("0"):
        return "61" + digits[1:]
    return digits


def stamp(moment):
    hour = moment.hour % 12 or 12
    ampm = "am" if moment.hour < 12 else "pm"
    return f"{moment:%a} {moment.day} {moment:%b %Y}, {hour}:{moment.minute:02d} {ampm}"


def join_names(names):
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def is_number_or_blank(value):
    """A price is a number, or null while it is still pending."""
    if value is None:
        return True
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def main():
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    now = dt.datetime.now(ZoneInfo(data["timezone"]))

    services = data["services"]
    vehicles = data["vehicle_types"]
    dirts = data["dirt_levels"]

    sizes = [v["id"] for v in vehicles]
    for s in services:
        prices = s.get("prices")
        if prices is not None and not all(
            isinstance(prices.get(size), (int, float)) and prices[size] >= 0 for size in sizes
        ):
            raise SystemExit(f"Build stopped: '{s['name']}' needs a price for every vehicle size, or null.")

    name = esc(data["business_name"])
    owner = esc(data["owner"])
    facebook = esc(data["facebook_url"])
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    hours = data.get("hours", "").strip()
    suburbs = [s.strip() for s in data.get("suburbs", []) if s.strip()]

    currency = data.get("currency", "$")

    def price_label(s):
        prices = s.get("prices")
        if prices is None:
            return "Price on request"
        return f"From {currency}{min(prices.values()):,.0f}"

    def service_row(s):
        return (
            '<li class="menu__item">'
            f'<div class="menu__text"><h4>{esc(s["name"])}</h4>'
            f'<p class="menu__price">{esc(price_label(s))}</p>'
            f'<p>{esc(s["summary"])}</p></div>'
            '<button class="btn btn-line menu__add" type="button" '
            f'data-service="{esc(s["id"])}" data-name="{esc(s["name"])}" aria-pressed="false">'
            "Add to quote</button>"
            "</li>"
        )

    service_rows = "\n      ".join(
        f'<h3 class="menu__group">{esc(g["name"])}</h3>\n      <ul class="menu">\n      '
        + "\n      ".join(service_row(s) for s in services if s.get("group") == g["id"])
        + "\n      </ul>"
        for g in data["service_groups"]
    )
    vehicle_options = "".join(
        f'<option value="{esc(v["id"])}">{esc(v["name"])}</option>' for v in vehicles
    )
    dirt_options = "".join(
        f'<option value="{esc(d["id"])}">{esc(d["name"])}</option>' for d in dirts
    )

    rv = json.loads((ROOT / "reviews.json").read_text(encoding="utf-8"))

    def review_li(r):
        return (
            '<li class="review">'
            '<p class="review__stars" role="img" aria-label="5 out of 5 stars">★★★★★</p>'
            f'<blockquote>{esc(r["text"])}</blockquote>'
            f'<p class="review__name">{esc(r["name"])}</p>'
            "</li>"
        )

    featured = int(rv.get("featured", 6))
    reviews_top = "\n      ".join(review_li(r) for r in rv["items"][:featured])
    reviews_rest = "\n        ".join(review_li(r) for r in rv["items"][featured:])
    reviews_link = ""
    if rv.get("google_url", "").strip():
        reviews_link = (
            f' <a href="{esc(rv["google_url"])}" target="_blank" rel="noopener">Read them on Google</a>.'
        )

    # Every way to reach the owner. Each appears only when its detail is filled in.
    whatsapp = data.get("whatsapp", "").strip()
    messenger = data.get("messenger_url", "").strip()
    instagram = data.get("instagram_url", "").strip()
    tiktok = data.get("tiktok_url", "").strip()
    google = data.get("google_url", "").strip()
    texting = bool(data.get("text_enabled", True))
    sms_body = "Hi " + data["owner"] + ", I'd like a quote for a car detail."

    def ways():
        out = []
        if phone:
            out.append(("Call", esc(phone), tel(phone), False))
            if texting:
                out.append(("Text", esc(phone), "sms:" + tel(phone)[4:] + "?&body=" + quote(sms_body), False))
        if whatsapp:
            out.append(("WhatsApp", esc(whatsapp), "https://wa.me/" + intl_digits(whatsapp) + "?text=" + quote(sms_body), True))
        if email:
            out.append(("Email", esc(email), "mailto:" + esc(email) + "?subject=" + quote("Quote request"), False))
        if messenger:
            out.append(("Messenger", "Message on Facebook", esc(messenger), True))
        out.append(("Facebook", "Detailed By Jarrad", facebook, True))
        if instagram:
            out.append(("Instagram", "Photos of recent work", esc(instagram), True))
        if tiktok:
            out.append(("TikTok", "Videos of recent work", esc(tiktok), True))
        if google:
            out.append(("Google", "Reviews and business listing", esc(google), True))
        return out

    contact_items = "\n        ".join(
        '<li><a class="way" href="' + href + '"'
        + (' target="_blank" rel="noopener"' if external else "")
        + f'><span class="way__label">{label}</span><span class="way__detail">{detail}</span></a></li>'
        for label, detail, href, external in ways()
    )
    foot_ways = "\n      ".join(
        '<li><a href="' + href + '"' + (' target="_blank" rel="noopener"' if external else "") + f'>{label}</a></li>'
        for label, detail, href, external in ways()
    )
    header_call = f'<a class="head-call" href="{tel(phone)}">Call</a>' if phone else ""

    areas = f'<p class="areas">We cover {esc(join_names(suburbs))}.</p>' if suburbs else ""

    if phone:
        sticky_second = f'<a class="btn btn-ghost" href="{tel(phone)}">Call</a>'
    else:
        sticky_second = '<a class="btn btn-ghost" href="#contact">Contact</a>' 
    foot_hours = f'<p class="small">Hours: {esc(hours)}</p>' if hours else ""

    draft_bar = ""
    robots = ""
    if not LIVE:
        draft_bar = (
            f'<div class="draft-bar" role="note">Draft for {owner} to review. '
            "Prices, areas and contact details still need to be confirmed.</div>"
        )
        robots = '<meta name="robots" content="noindex, nofollow">'

    ld = json.loads(read("ld.json"))
    ld["name"] = data["business_name"]
    ld["description"] = data["tagline"]
    ld["sameAs"] = [data["facebook_url"]]
    ld["makesOffer"] = [
        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"]}}
        for s in services
    ]
    same_as = [u for u in (data["facebook_url"], instagram, tiktok, google) if u]
    ld["sameAs"] = same_as
    if phone:
        ld["telephone"] = phone
    if email:
        ld["email"] = email
    if suburbs:
        ld["areaServed"] = suburbs
    ld_tag = (
        '<script type="application/ld+json">'
        + json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/")
        + "</script>"
    )

    values = {
        "{{BUSINESS}}": name,
        "{{OWNER}}": owner,
        "{{TAGLINE}}": esc(data["tagline"]),
        "{{FACEBOOK}}": facebook,
        "{{YEAR}}": str(now.year),
        "{{STAMP}}": f"{stamp(now)} {now.tzname()}",
        "{{STAMP_ISO}}": now.isoformat(timespec="minutes"),
        "{{SERVICES}}": service_rows,
        "{{AREAS}}": areas,
        "{{REVIEWS_TOP}}": reviews_top,
        "{{REVIEWS_REST}}": reviews_rest,
        "{{REVIEWS_LINK}}": reviews_link,
        "{{REVIEW_RATING}}": esc(rv["rating"]),
        "{{REVIEW_COUNT}}": str(int(rv["count"])),
        "{{REVIEW_SHOWN}}": str(len(rv["items"])),
        "{{VEHICLE_OPTIONS}}": vehicle_options,
        "{{DIRT_OPTIONS}}": dirt_options,
        "{{PHOTO_LIMIT}}": str(int(data.get("photo_limit", 6))),
        "{{CONTACT_WAYS}}": contact_items,
        "{{FOOT_WAYS}}": foot_ways,
        "{{HEADER_CALL}}": header_call,
        "{{FOOT_HOURS}}": foot_hours,
        "{{STICKY_SECOND}}": sticky_second,
        "{{DRAFT}}": draft_bar,
        "{{ROBOTS}}": robots,
        "{{LD}}": ld_tag,
        "{{LOGO_LARGE}}": data_uri("img/badge-560.webp", "image/webp"),
        "{{LOGO_SMALL}}": data_uri("img/badge-96.webp", "image/webp"),
        "{{FONT_ARCHIVO}}": data_uri("fonts/archivo-subset.woff2", "font/woff2"),
        "{{FAVICON}}": data_uri("img/favicon-64.png", "image/png"),
        "{{APPLE_ICON}}": data_uri("img/apple-touch-180.png", "image/png"),
    }

    def fill(text):
        for key, value in values.items():
            text = text.replace(key, value)
        if "{{" in text:
            raise SystemExit("Build stopped: a placeholder was left unfilled.")
        return text

    config = {
        "owner": data["owner"],
        "formEndpoint": data.get("form_endpoint", "").strip(),
        "email": email,
        "currency": data.get("currency", "$"),
        "photoLimit": int(data.get("photo_limit", 6)),
        "services": {s["id"]: s.get("prices") for s in services},
        "dirts": [{"id": d["id"], "quote": bool(d.get("quote_only"))} for d in dirts],
    }
    config_json = json.dumps(config, ensure_ascii=False).replace("</", "<\\/")

    page = "\n".join([
        "<!doctype html>",
        '<html lang="en-AU">',
        "<head>",
        fill(read("head.html")),
        f"<style>\n{fill(read('style.css'))}\n</style>",
        "</head>",
        "<body>",
        fill(read("body.html")),
        f"<script>window.SITE_CONFIG = {config_json};</script>",
        f"<script>\n{read('app.js')}\n</script>",
        "</body>",
        "</html>",
        "",
    ])

    out = ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    mode = "live" if LIVE else "draft"
    size_kb = len(page.encode("utf-8")) / 1024
    print(f"Built index.html ({mode}), stamped {stamp(now)} {now.tzname()}, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
