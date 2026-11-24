# Detailed By Jarrad: website

Edit `data.json`, then build:

    python3 build.py          # draft preview: banner and noindex (default)
    python3 build.py --live   # live site, once the owner has approved it

The built `index.html` is one self-contained file. The font, the logo and all CSS and JavaScript are inside it, so the page makes no requests of its own after it loads.

## What to fill in (data.json)

- `phone`, `email`, `hours`, `suburbs`: contact details and service areas. Blank values are hidden on the site.
- `services[].price`: the base price in dollars for each service, for a standard car. `null` means pending.
- `vehicle_types[].multiplier`: the price factor for each vehicle size, for example `1.0` for a small car and `1.2` for an SUV. `null` means pending.
- `dirt_levels[].extra`: the percentage added for each dirt level, for example `0`, `15` and `30`. `null` means pending.
- `form_endpoint`: the address that receives quote requests and photos. Blank means requests are copied to the clipboard instead.
- `photo_limit`: the most photos a customer can add (6 by default).

## How the estimate works

Estimate = sum of the chosen services' prices, × vehicle multiplier, × (1 + dirt extra ÷ 100). It updates as the customer chooses. Until every number it needs is set, it shows "To be confirmed". The estimate is always marked as an estimate, and the owner confirms the final price after reviewing the photos.

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
