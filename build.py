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
        first = vehicles[0]
        return (
            f'<div class="menu__price" data-prices="{esc(json.dumps(prices))}">'
            f'<span class="menu__from">{esc(first.get("short", first["name"]))}</span>'
            f'<span class="menu__figure" data-value="{prices[first["id"]]}">{money_text(prices[first["id"]])}</span></div>'
        )

    def service_row(s):
        includes = "".join(f"<li>{esc(i)}</li>" for i in s.get("includes", []))
        includes_html = f'<ul class="menu__includes">{includes}</ul>' if includes else ""
        return (
            '<li class="menu__item">'
            f'<div class="menu__text"><h4>{esc(s["name"])}</h4>'
            f'<p>{esc(s["summary"])}</p>{includes_html}</div>'
            f"{price_block(s)}"
            '<button class="btn btn-line menu__add" type="button" '
            f'data-service="{esc(s["id"])}" data-name="{esc(s["name"])}" aria-pressed="false">'
            "Add to quote</button>"
            "</li>"
        )

    # One switch reprices the whole menu for the chosen vehicle size.
    size_switch = (
        '<div class="size-switch"><span class="size-switch__label" id="size-switch-label">Show prices for</span>'
        '<div class="seg-group" role="radiogroup" aria-labelledby="size-switch-label">'
        + "".join(
            f'<label class="seg"><input type="radio" name="menu-size" value="{esc(v["id"])}"{" checked" if i == 0 else ""}>'
            f'<span>{esc(v.get("short", v["name"]))}</span></label>'
            for i, v in enumerate(vehicles)
        )
        + "</div></div>"
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
            '<span class="stars" role="img" aria-label="5 out of 5 stars"></span>'
            f'<blockquote>{esc(r["text"])}</blockquote>'
            f'<p class="review__name">{esc(r["name"])}</p>'
            "</li>"
        )

    featured = int(rv.get("featured", 6))
    reviews_top = "\n      ".join(review_li(r) for r in rv["items"][:featured])
    reviews_rest = "\n        ".join(review_li(r) for r in rv["items"][featured:])
    reviews_all = "\n      ".join(review_li(r) for r in rv["items"])
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
            out.append(("Email", esc(email).replace("@", "<wbr>@"), "mailto:" + esc(email) + "?subject=" + quote("Quote request"), False))
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

    # Simple line symbols, drawn with the page's own colours. These are generic
    # symbols, not the companies' logos.
    icon_paths = {
        "Call": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
        "Text": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        "WhatsApp": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>',
        "Messenger": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>',
        "Email": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/>',
        "Facebook": '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>',
        "Instagram": '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
        "TikTok": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
        "YouTube": '<polygon points="6 3 20 12 6 21 6 3"/>',
        "Google": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    }

    def icon(label):
        return (
            '<svg class="way__icon" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icon_paths.get(label, "")}</svg>'
        )

    contact_items = "\n        ".join(
        '<li><a class="way" href="' + href + '"'
        + (' target="_blank" rel="noopener"' if external else "")
        + f'><span class="way__badge">{icon(label)}</span>'
        + f'<span class="way__words"><span class="way__label">{label}</span><span class="way__detail">{detail}</span></span></a></li>'
        for label, detail, href, external in ways()
    )
    foot_ways = "\n      ".join(
        '<li><a href="' + href + '"' + (' target="_blank" rel="noopener"' if external else "") + f'>{icon(label)}{label}</a></li>'
        for label, detail, href, external in ways()
    )
    header_call = f'<a class="head-call" href="{tel(phone)}">Call</a>' if phone else ""

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
            if image else ""
        )
        price = f'{currency}{item["price"]:,.0f}' if float(item["price"]).is_integer() else f'{currency}{item["price"]:,.2f}'
        colours = f'<p class="product__fact">Colours: {esc(", ".join(item["colours"]))}</p>' if item.get("colours") else ""
        desc = f'<p>{esc(item["description"])}</p>' if item.get("description") else ""
        if item.get("sold_out"):
            action = '<div class="product__row"><span class="btn btn-line product__add is-off">Sold out</span></div>'
        else:
            sizes = item.get("sizes") or []
            chips = ""
            if sizes:
                chips = (
                    f'<fieldset class="sizes"><legend>Choose your size</legend><div class="sizes__row">'
                    + "".join(
                        f'<label class="size-chip"><input type="radio" name="size-{pid}" value="{esc(sz)}">'
                        f"<span>{esc(sz)}</span></label>"
                        for sz in sizes
                    )
                    + "</div></fieldset>"
                )
            action = (
                f"{chips}"
                '<button class="btn btn-primary product__add" type="button">Add to cart</button>'
                '<p class="product__msg" role="status" aria-live="polite"></p>'
            )
        return (
            f'<li class="product" data-product="{pid}" data-name="{esc(item["name"])}" '
            f'data-price="{round(item["price"] * 100)}">{picture}<div class="product__body"><h3>{esc(item["name"])}</h3>'
            f'<p class="product__price">{price}</p>{desc}{colours}{action}</div></li>'
        )

    if products:
        merch_intro = esc(merch.get("intro") or f"Shirts and hoodies from {data['business_name']}.")
        # Postage rates are stated in the cart only, never under the products.
        post_cfg = merch.get("postage") or {}

        def money(v):
            v = float(v)
            return f"${v:.0f}" if v == int(v) else f"${v:.2f}"

        post_flat = float(post_cfg.get("flat", 0) or 0)
        post_free = float(post_cfg.get("free_over", 0) or 0)
        if post_flat and post_free:
            post_rate = f" ({money(post_flat)}, free on orders of {money(post_free)} or more)"
        elif post_flat:
            post_rate = f" ({money(post_flat)})"
        else:
            post_rate = " (free)"
        merch_section = (
            '<section class="merch" id="merch" aria-labelledby="merch-title"><div class="wrap">'
            f'<h2 id="merch-title">Clothing</h2><p class="intro">{merch_intro}</p>'
            '<ul class="products">' + "".join(product_card(i) for i in products) + "</ul></div></section>"
        )
        nav_merch = '<a href="#merch">Clothing</a>'
        area_name = esc(data.get("area", ""))
        merch_cart = (
            '<button class="cart-fab" id="cart-fab" type="button" aria-haspopup="dialog" hidden>Cart (0)</button>'
            '<dialog class="drawer" id="cart" aria-labelledby="cart-title"><div class="drawer__inner">'
            '<div class="drawer__head"><h2 id="cart-title">Your cart</h2>'
            '<button class="btn btn-ghost btn-sm" type="button" data-close>Close</button></div>'
            '<ul class="cart-items" id="cart-items"></ul>'
            '<p class="note" id="cart-empty">Your cart is empty. Add a tee or hoodie from the Clothing section.</p>'
            '<div id="cart-checkout">'
            '<fieldset class="cart-delivery"><legend>Delivery</legend>'
            f'<label><input type="radio" name="cart-delivery" value="pickup" checked> Pickup or drop-off on the {area_name} (free)</label>'
            f'<label><input type="radio" name="cart-delivery" value="post"> Post, Australia-wide{post_rate}</label></fieldset>'
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
        '<span class="rating__text"><span class="stars rating__stars" aria-hidden="true"></span>'
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

    hero_rating = (
        f'<a class="hero__rating" href="#reviews" aria-label="{rating_label}. Read the reviews">'
        '<span class="stars" aria-hidden="true"></span>'
        f'<span>{esc(rv["rating"])} from {int(rv["count"])} Google reviews</span></a>'
    )

    towns = (
        f'<div class="towns-block"><h3 class="towns-title">Where {owner} works</h3><ul class="towns">'
        + "".join(f"<li>{esc(t)}</li>" for t in suburbs)
        + "</ul></div>"
    ) if suburbs else ""

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
    if data.get("opening_hours"):
        ld["openingHours"] = data["opening_hours"]
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
        "{{HERO_RATING}}": hero_rating,
        "{{TOWNS}}": towns,
        "{{SIZE_SWITCH}}": size_switch,
        "{{REVIEWS_ALL}}": reviews_all,
        "{{MERCH_CART}}": merch_cart,
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
