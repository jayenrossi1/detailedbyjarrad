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

    def money_text(value):
        return f"{currency}{value:,.0f}"

    def price_block(s):
        prices = s.get("prices")
        if prices is None:
            return '<div class="menu__price"><span class="menu__figure menu__figure--ask">Price on request</span></div>'
        return (
            '<div class="menu__price"><span class="menu__from">from</span>'
            f'<span class="menu__figure">{money_text(min(prices.values()))}</span></div>'
        )

    def sizes_line(s):
        prices = s.get("prices")
        if prices is None:
            return ""
        cells = "".join(
            f'<div><dt>{esc(v.get("short", v["name"]))}</dt><dd>{money_text(prices[v["id"]])}</dd></div>'
            for v in vehicles
        )
        return f'<dl class="menu__sizes">{cells}</dl>'

    def service_row(s):
        includes = "".join(f"<li>{esc(i)}</li>" for i in s.get("includes", []))
        includes_html = f'<ul class="menu__includes">{includes}</ul>' if includes else ""
        return (
            '<li class="menu__item">'
            f'<div class="menu__text"><h4>{esc(s["name"])}</h4>'
            f'<p>{esc(s["summary"])}</p>{includes_html}{sizes_line(s)}</div>'
            f"{price_block(s)}"
            '<button class="btn btn-line menu__add" type="button" '
            f'data-service="{esc(s["id"])}" data-name="{esc(s["name"])}" aria-pressed="false">'
            "Add to quote</button>"
            "</li>"
        )

    service_rows = "\n      ".join(
        f'<div class="menu-group{" menu-group--dark" if g.get("dark") else ""}">'
        f'<h3 class="menu__group">{esc(g["name"])}</h3>\n      <ul class="menu">\n      '
        + "\n      ".join(service_row(s) for s in services if s.get("group") == g["id"])
        + "\n      </ul></div>"
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
    youtube = data.get("youtube_url", "").strip()
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
        if youtube:
            out.append(("YouTube", "Videos of recent work", esc(youtube), True))
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

    about = data.get("about") or {}
    if about.get("photos"):
        for ph in about["photos"]:
            if not (ROOT / ph["src"]).is_file():
                raise SystemExit(f"Build stopped: photo not found: {ph['src']}")
        about_section = (
            '<section class="about" id="about" aria-labelledby="about-title"><div class="wrap about__layout">'
            f'<div class="about__text"><h2 id="about-title">{esc(about["heading"])}</h2>'
            + "".join(f"<p>{esc(t)}</p>" for t in about.get("text", []))
            + '<p><a class="btn btn-primary" href="#quote">Get an estimate</a></p></div>'
            + "".join(
                f'<img class="about__photo" src="{esc(ph["src"])}" alt="{esc(ph["alt"])}" '
                'width="720" height="960" loading="lazy" decoding="async">'
                for ph in about["photos"]
            )
            + "</div></section>"
        )
    else:
        about_section = ""

    # Merch store. Hidden until merch.json lists at least one product.
    merch = json.loads((ROOT / "merch.json").read_text(encoding="utf-8"))
    products = merch.get("products", [])

    def product_card(item):
        image = item.get("image", "").strip()
        if image and not (ROOT / image).is_file():
            raise SystemExit(f"Build stopped: merch image not found: {image}")
        if not isinstance(item.get("price"), (int, float)):
            raise SystemExit(f"Build stopped: merch item '{item.get('name')}' needs a price.")
        pid = esc(item["id"])
        picture = (
            f'<img class="product__img" src="{esc(image)}" alt="{esc(item["name"])}" '
            'width="640" height="640" loading="lazy" decoding="async">'
            if image else '<div class="product__img product__img--none" aria-hidden="true"></div>'
        )
        price = f'{currency}{item["price"]:,.0f}' if float(item["price"]).is_integer() else f'{currency}{item["price"]:,.2f}'
        colours = f'<p class="product__fact">Colours: {esc(", ".join(item["colours"]))}</p>' if item.get("colours") else ""
        desc = f'<p>{esc(item["description"])}</p>' if item.get("description") else ""
        if item.get("sold_out"):
            action = '<div class="product__row"><span class="btn btn-line product__add is-off">Sold out</span></div>'
        else:
            sizes = item.get("sizes") or []
            select = ""
            if sizes:
                options = '<option value="">Size</option>' + "".join(f"<option>{esc(sz)}</option>" for sz in sizes)
                select = (
                    f'<label class="visually-hidden" for="size-{pid}">Size for {esc(item["name"])}</label>'
                    f'<select class="product__size" id="size-{pid}">{options}</select>'
                )
            action = (
                f'<div class="product__row">{select}'
                '<button class="btn btn-primary product__add" type="button">Add to cart</button></div>'
                '<p class="product__msg" role="status" aria-live="polite"></p>'
            )
        return (
            f'<li class="product" data-product="{pid}" data-name="{esc(item["name"])}" '
            f'data-price="{round(item["price"] * 100)}">{picture}<div class="product__body"><h3>{esc(item["name"])}</h3>'
            f'<p class="product__price">{price}</p>{desc}{colours}{action}</div></li>'
        )

    if products:
        merch_intro = esc(merch.get("intro") or f"Shirts and hoodies from {data['business_name']}.")
        postage = f'<p class="note">{esc(merch["postage_note"])}</p>' if merch.get("postage_note") else ""
        merch_section = (
            '<section class="merch" id="merch" aria-labelledby="merch-title"><div class="wrap">'
            f'<h2 id="merch-title">Merch</h2><p class="intro">{merch_intro}</p>'
            '<ul class="products">' + "".join(product_card(i) for i in products) + f"</ul>{postage}</div></section>"
        )
        nav_merch = '<a href="#merch">Merch</a>'
        area_name = esc(data.get("area", ""))
        merch_cart = (
            '<button class="cart-fab" id="cart-fab" type="button" aria-haspopup="dialog" hidden>Cart (0)</button>'
            '<dialog class="drawer" id="cart" aria-labelledby="cart-title"><div class="drawer__inner">'
            '<div class="drawer__head"><h2 id="cart-title">Your cart</h2>'
            '<button class="btn btn-ghost btn-sm" type="button" data-close>Close</button></div>'
            '<ul class="cart-items" id="cart-items"></ul>'
            '<p class="note" id="cart-empty">Your cart is empty. Add a tee or hoodie from the Merch section.</p>'
            '<div id="cart-checkout">'
            '<fieldset class="cart-delivery"><legend>Delivery</legend>'
            f'<label><input type="radio" name="cart-delivery" value="pickup" checked> Pickup or drop-off on the {area_name} (free)</label>'
            '<label><input type="radio" name="cart-delivery" value="post"> Post, Australia-wide</label></fieldset>'
            '<dl class="cart-totals"><div><dt>Items</dt><dd id="cart-sub"></dd></div>'
            '<div><dt>Delivery</dt><dd id="cart-post"></dd></div>'
            '<div class="cart-total"><dt>Total</dt><dd id="cart-total"></dd></div></dl>'
            f'<p class="help">Send your order to {owner}. He replies to confirm it and arrange payment.</p>'
            '<div class="cart-actions"><a class="btn btn-primary" id="cart-sms" href="#merch">Order by text</a>'
            '<a class="btn btn-ghost" id="cart-email" href="#merch">Order by email</a></div>'
            "</div></div></dialog>"
        )
    else:
        merch_section = ""
        nav_merch = ""
        merch_cart = ""

    rating_inner = (
        f'<span class="rating__score">{esc(rv["rating"])}</span>'
        '<span class="rating__text"><span class="rating__stars" aria-hidden="true">★★★★★</span>'
        f'<span class="rating__count">{int(rv["count"])} reviews on Google</span></span>'
    )
    rating_label = f'Rated {esc(rv["rating"])} out of 5 from {int(rv["count"])} reviews on Google'
    if rv.get("google_url", "").strip():
        rating_box = (
            f'<a class="rating" href="{esc(rv["google_url"])}" target="_blank" rel="noopener" '
            f'aria-label="{rating_label}. Read them on Google">{rating_inner}</a>'
        )
    else:
        rating_box = f'<div class="rating" role="img" aria-label="{rating_label}">{rating_inner}</div>'

    area_name = data.get("area", "").strip()
    if suburbs and area_name:
        areas = f'<p class="areas">We cover the {esc(area_name)}, including {esc(join_names(suburbs))}.</p>'
    elif suburbs:
        areas = f'<p class="areas">We cover {esc(join_names(suburbs))}.</p>'
    else:
        areas = ""

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
            "Some prices are still to be confirmed.</div>"
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
    same_as = [u for u in (data["facebook_url"], instagram, tiktok, youtube, google) if u]
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
        "{{MERCH}}": merch_section,
        "{{RATING_BOX}}": rating_box,
        "{{MERCH_CART}}": merch_cart,
        "{{ABOUT}}": about_section,
        "{{AREA}}": esc(data.get("area", "")),
        "{{SITE_URL}}": esc(data.get("site_url", "")),
        "{{NAV_MERCH}}": nav_merch,
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
        "formMode": data.get("form_mode", "fetch"),
        "email": email,
        "currency": data.get("currency", "$"),
        "photoLimit": int(data.get("photo_limit", 6)),
        "services": {s["id"]: s.get("prices") for s in services},
        "dirts": [{"id": d["id"], "quote": bool(d.get("quote_only"))} for d in dirts],
        "merch": {
            "postage": round(float((merch.get("postage") or {}).get("flat", 0)) * 100),
            "freeOver": round(float((merch.get("postage") or {}).get("free_over", 0)) * 100),
            "phone": tel(phone)[4:] if phone else "",
            "area": data.get("area", ""),
        },
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

    depth = 0
    for match in __import__("re").finditer(r"<section\b[^>]*>|</section>", page):
        tag = match.group(0)
        if tag.startswith("</"):
            depth -= 1
        else:
            if depth > 0 and 'class="estimate"' not in tag:
                raise SystemExit("Build stopped: a page section is nested inside another section.")
            depth += 1
    if depth != 0:
        raise SystemExit("Build stopped: unbalanced section tags.")

    out = ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    mode = "live" if LIVE else "draft"
    size_kb = len(page.encode("utf-8")) / 1024
    print(f"Built index.html ({mode}), stamped {stamp(now)} {now.tzname()}, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
