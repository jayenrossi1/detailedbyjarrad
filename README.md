# Detailed By Jarrad: website

Edit `data.json`, then build:

    python3 build.py          # draft preview: banner and noindex (default)
    python3 build.py --live   # live site, once the owner has approved it

The built `index.html` is one self-contained file. The font, the logo and all CSS and JavaScript are inside it, so the page makes no requests of its own after it loads.

## What to fill in (data.json)

- `phone`, `email`, `hours`, `suburbs`: contact details and service areas. Blank values are hidden on the site.
- `services[].prices`: the price for each vehicle size (`small`, `medium`, `large`). `null` shows "Price on request".
- `services[].group`: which menu group the service sits in (`service_groups`).
- `dirt_levels[].quote_only`: when `true`, choosing that level shows "Quoted from your photos" in place of a price.
- `form_endpoint`: the address that receives quote requests and photos. Blank means requests are copied to the clipboard instead.
- `photo_limit`: the most photos a customer can add (6 by default).
- `reviews.json`: the Google reviews, rating and link.

## How the estimate works

Estimate = the chosen services' prices for the selected vehicle size, added together. It shows "To be confirmed" if any chosen service has no price yet, and "Quoted from your photos" for heavy jobs. The owner confirms the final price.

## Merch store (merch.json)

The Merch section and its header link appear only when `products` has at least one item. Each product:

    {
      "name": "Logo Tee",
      "price": 35,
      "description": "Heavyweight cotton, regular fit.",
      "sizes": ["S", "M", "L", "XL"],
      "colours": ["Black"],
      "image": "img/merch/logo-tee.webp",
      "checkout_url": "",
      "sold_out": false
    }

- `image`: a square photo in `img/merch/`, about 600 px wide.
- `checkout_url`: the payment provider's checkout link. With it, the button reads "Buy now". Without it, the button reads "Order by text" and opens a message to the owner.
- `sold_out`: `true` replaces the button with "Sold out".
- `postage_note` (top level): one line shown under the products, such as postage price and timing.

## Photos

Customers can drop photos into the photo box or choose them from their phone. Photos are resized on the device to 1600 px on the longest side, so uploads stay small. Photos are only sent when `form_endpoint` points to a service that accepts file uploads. Until then, the page tells the customer to attach them in a Facebook message.

## Files

- `index.html`: the built site. Publish this one file.
- `data.json`: everything the owner may change.
- `_src/`: page parts (head, body, CSS, JavaScript, JSON-LD). Edit these, then rebuild.
- `build.py`: assembles `index.html`, inlines the assets and stamps the "Site updated" time in Brisbane time.
- `fonts/`: Archivo, subset to Latin and self-hosted (SIL Open Font License, see `fonts/OFL-Archivo.txt`).
- `img/`: the logo as WebP at two sizes.

## Still to do

- Choose a form service that accepts photos, and set `form_endpoint`.
- Add Jarrad's pricing, vehicle multipliers and dirt levels to `data.json`.
- Add phone, email, hours and service areas.
- Set up hosting and the custom domain, then build with `--live`.
