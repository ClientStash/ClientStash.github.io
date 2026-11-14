#!/usr/bin/env python3
"""Generate crawlable product pages, homepage cards, and the XML sitemap."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://ClientStash.github.io/"
VERIFICATION_UPDATED = "2026-11-15"
VERIFIED_VERSIONS = ["1.21.11", "26.2"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def absolute_asset(path: str) -> str:
    return f"{SITE_URL}{path.lstrip('/')}" if path else f"{SITE_URL}brand-mark.png"


def page_asset(path: str) -> str:
    return f"../../{path.lstrip('/')}"


def download_filename(product: dict, build: dict) -> str:
    mod_name = re.sub(r"[^A-Za-z0-9]+", "-", str(product["name"])).strip("-")
    mc_version = re.sub(r"[^A-Za-z0-9.-]+", "-", str(build.get("version", "unknown"))).strip("-.")
    return f"{mod_name}-{mc_version}.jar"


def product_faq(product: dict) -> list[dict[str, str]]:
    name = product["name"]
    requirements = ", ".join(product.get("requirements", [])) or "the matching loader and build"
    supported = ", ".join(product.get("supported_versions", []))
    first_usage = (product.get("usage") or ["Open the client using its documented keybind."])[0]
    return [
        {
            "question": f"Which Minecraft versions does {name} support?",
            "answer": f"This listing covers {supported}. ClientStash has manually tested the public listing on Minecraft 1.21.11 and 26.2; choose a build that matches your installation.",
        },
        {
            "question": f"Has {name} been tested on DonutSMP?",
            "answer": f"Yes. The ClientStash owner manually tested {name} on DonutSMP with Minecraft 1.21.11 and 26.2. Its {product.get('status', 'listed')} status records the result of those tests.",
        },
        {
            "question": f"What does {name} require?",
            "answer": f"The listed requirements are {requirements}. Verify that every dependency matches your selected Minecraft build before launching.",
        },
        {
            "question": f"How do I install {name}?",
            "answer": "Install the matching loader and dependencies, place the JAR in the .minecraft/mods folder, and launch the matching profile.",
        },
        {
            "question": f"How do I open or use {name}?",
            "answer": first_usage,
        },
    ]


def schema_for(product: dict, canonical: str, faq: list[dict[str, str]]) -> str:
    image = absolute_asset(product.get("image", ""))
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{SITE_URL}#organization",
                "name": "ClientStash",
                "alternateName": "Cracked Clients",
                "url": SITE_URL,
                "logo": f"{SITE_URL}brand-mark.png",
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": f"{product['name']} for DonutSMP",
                "description": product["description"],
                "dateModified": VERIFICATION_UPDATED,
                "author": {"@id": f"{SITE_URL}#organization"},
                "publisher": {"@id": f"{SITE_URL}#organization"},
                "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
                "mainEntity": {"@id": f"{canonical}#software"},
            },
            {
                "@type": "SoftwareApplication",
                "@id": f"{canonical}#software",
                "name": product["name"],
                "description": product["description"],
                "applicationCategory": "GameApplication",
                "operatingSystem": "Minecraft Java Edition",
                "softwareVersion": product["version"],
                "url": canonical,
                "image": image,
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Owner-tested versions", "value": ", ".join(VERIFIED_VERSIONS)},
                    {"@type": "PropertyValue", "name": "DonutSMP test status", "value": product.get("status", "")},
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "ClientStash", "item": SITE_URL},
                    {"@type": "ListItem", "position": 2, "name": "DonutSMP Clients", "item": f"{SITE_URL}#mods"},
                    {"@type": "ListItem", "position": 3, "name": product["name"], "item": canonical},
                ],
            },
            {
                "@type": "FAQPage",
                "@id": f"{canonical}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def version_builds(product: dict) -> list[dict]:
    existing = product.get("versions", [])
    builds = []
    for version in product.get("supported_versions", VERIFIED_VERSIONS):
        prefix = version.replace(".x", "")
        match = next((item for item in existing if str(item.get("version", "")).startswith(prefix)), None)
        builds.append(match or {
            "version": version,
            "name": f"{product['name']} — Minecraft {version}",
            "badges": ["Owner tested" if version in VERIFIED_VERSIONS else "Available"],
            "size": product.get("size", ""),
            "desc": f"Listed build for Minecraft {version}.",
            "download_url": product.get("download_url", "mods/mod.jar"),
        })
    return builds


def render_product_page(product: dict, related: list[dict]) -> str:
    canonical = f"{SITE_URL}clients/{product['id']}/"
    title = f"{product['name']} for DonutSMP | ClientStash"
    description = (
        f"{product['name']} for DonutSMP: owner-tested on Minecraft 1.21.11 and 26.2. "
        "Review features, requirements, status and installation."
    )[:158]
    faq = product_faq(product)
    schema = schema_for(product, canonical, faq)
    image = product.get("image", "")
    image_html = (
        f'<img src="{esc(page_asset(image))}" alt="{esc(product["name"])} interface" width="960" height="540">'
        if image else
        '<div class="product-placeholder" aria-hidden="true"><span class="material-symbols-outlined">deployed_code</span><strong>CLIENT PREVIEW</strong></div>'
    )
    tags = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in product.get("tags", [])[:5])
    requirements = "".join(f"<span>{esc(item)}</span>" for item in product.get("requirements", []))
    highlights = "".join(f"<li>{esc(item)}</li>" for item in product.get("highlights", []))
    usage = "".join(f"<li>{esc(item)}</li>" for item in product.get("usage", []))
    chips = "".join(f"<span>{esc(version)}</span>" for version in product.get("supported_versions", []))
    faq_html = "".join(
        f'<article class="detail-faq-item"><button type="button" aria-expanded="false"><span>{esc(item["question"])}</span><i aria-hidden="true">+</i></button><div><p>{esc(item["answer"])}</p></div></article>'
        for item in faq
    )
    related_html = "".join(
        f'<a href="../{esc(item["id"])}/"><span>{esc(item["version"])}</span><strong>{esc(item["name"])}</strong><i aria-hidden="true">↗</i></a>'
        for item in related
    )
    builds_html = "".join(
        '<div class="version-item-card"><div class="version-item-info"><div class="version-item-title-row">'
        f'<span class="version-item-name">{esc(build.get("name", build["version"]))}</span>'
        + "".join(f'<span class="version-badge green">{esc(badge)}</span>' for badge in build.get("badges", []))
        + f'</div><p class="version-item-desc">{esc(build.get("desc", ""))}</p><span class="version-item-meta">{esc(build.get("size", product.get("size", "")))}</span></div>'
        f'<a href="{esc(page_asset(build.get("download_url", product.get("download_url", "mods/mod.jar"))))}" download="{esc(download_filename(product, build))}" class="btn-version-download"><span class="material-symbols-outlined">download</span>Download</a></div>'
        for build in version_builds(product)
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="author" content="ClientStash owner">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="ClientStash"><meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{esc(absolute_asset(image))}">
    <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{esc(absolute_asset(image))}">
    <link rel="icon" type="image/svg+xml" href="../../favicon.svg"><link rel="icon" type="image/x-icon" href="../../favicon.ico">
    <link rel="manifest" href="../../site.webmanifest"><meta name="theme-color" content="#090a08">
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
    <link rel="stylesheet" href="../../style.css">
    <script type="application/ld+json">{schema}</script>
</head>
<body class="detail-page">
    <a class="skip-link" href="#product-main">Skip to product details</a>
    <nav class="navbar detail-nav" aria-label="Primary navigation"><a class="logo home-logo" href="../../" aria-label="ClientStash home"><img class="site-logo" src="../../logo.svg" alt="ClientStash" width="242" height="48"></a><div class="nav-links"><a href="../../#mods">Clients</a><a href="../../#features">Guide</a><a href="../../#testing">Testing</a><a href="../../#installation">Install</a><a href="../../#faq">FAQ</a></div><a class="nav-cta" href="../../#mods">All clients <span aria-hidden="true">↗</span></a></nav>
    <main id="product-main" class="detail-main"><div class="container">
        <nav class="detail-breadcrumb" aria-label="Breadcrumb"><a href="../../">Home</a><span>/</span><a href="../../#mods">Clients</a><span>/</span><span>{esc(product['name'])}</span></nav>
        <section class="product-hero" aria-labelledby="product-title"><div class="product-copy"><div class="product-kicker"><span class="status-badge">{esc(product.get('status', 'LISTED'))}</span><span>{esc(product.get('loader', 'Fabric'))} · Owner tested on 1.21.11 &amp; 26.2</span></div><h1 id="product-title">{esc(product['name'])}</h1><p class="product-answer">{esc(product['name'])} is a DonutSMP client or utility listing manually tested by the ClientStash owner on Minecraft 1.21.11 and 26.2.</p><div class="tags">{tags}</div><div class="product-actions"><a href="#downloads" class="detail-download" id="download-link"><span class="material-symbols-outlined" aria-hidden="true">download</span>Choose version</a><a href="#compatibility" class="detail-secondary">View compatibility</a></div><p class="product-caution"><span class="material-symbols-outlined" aria-hidden="true">verified_user</span>Status reflects firsthand owner testing. Server and anti-cheat updates can change results after review.</p></div><div class="product-media">{image_html}</div></section>
        <section class="product-facts" aria-label="Product facts"><div><span>Owner-tested versions</span><strong>1.21.11 / 26.2</strong></div><div><span>Status</span><strong>{esc(product.get('status', 'LISTED'))}</strong></div><div><span>Loader</span><strong>{esc(product.get('loader', 'Fabric'))}</strong></div><div><span>File size</span><strong>{esc(product.get('size', '—'))}</strong></div></section>
        <section class="detail-answer-section"><div class="detail-section-heading"><span>01 / Overview</span><h2>What is {esc(product['name'])}?</h2></div><div class="detail-prose"><p>{esc(product['description'])}</p><div class="requirement-block"><span>Requirements</span><div>{requirements}</div></div></div></section>
        <section class="detail-answer-section" id="compatibility"><div class="detail-section-heading"><span>02 / Compatibility</span><h2>Which Minecraft versions are available?</h2></div><div class="compatibility-panel"><p>This listing covers {esc(', '.join(product.get('supported_versions', [])))}. The ClientStash owner has directly tested the listed mod on Minecraft 1.21.11 and 26.2.</p><div class="compatibility-chips">{chips}</div></div></section>
        <section class="detail-columns"><article class="editorial-card"><span class="card-index">03 / Highlights</span><h2>What does it include?</h2><ul class="editorial-list">{highlights}</ul></article><article class="editorial-card"><span class="card-index">04 / Usage</span><h2>How do you use it?</h2><ol class="editorial-list numbered">{usage}</ol></article><article class="editorial-card"><span class="card-index">05 / Install</span><h2>How do you install it?</h2><ol class="editorial-list numbered"><li>Install the loader for the matching Minecraft version.</li><li>Add every dependency shown above.</li><li>Place the downloaded <code>.jar</code> in <code>.minecraft/mods</code>.</li><li>Launch the matching profile.</li></ol></article></section>
        <section class="detail-answer-section"><div class="detail-section-heading"><span>06 / Verification</span><h2>How was this status tested?</h2></div><div class="compatibility-panel"><p>The ClientStash owner installed this listing with its stated requirements, launched it on Minecraft 1.21.11 and 26.2, exercised representative modules, and connected to DonutSMP while observing anti-cheat behavior.</p><p><strong>Undetectable</strong> means no detection occurred during those owner tests. <strong>True bypass</strong> means the claimed bypass function worked during those tests. Verification record updated November 15, 2026.</p></div></section>
        <section class="detail-faq-section"><div class="detail-section-heading"><span>07 / Answers</span><h2>Frequently asked questions</h2></div><div class="detail-faq-list">{faq_html}</div></section>
        <section class="related-section"><div class="detail-section-heading"><span>08 / Keep browsing</span><h2>Related DonutSMP clients</h2></div><div class="related-grid">{related_html}</div></section>
    </div></main>
    <div id="downloads" class="modal-overlay" aria-hidden="true"><div class="modal-box version-modal-box" role="dialog" aria-modal="true" aria-labelledby="version-modal-title"><button type="button" class="modal-close-btn" id="version-modal-close" aria-label="Close version selector">&times;</button><div class="version-modal-header"><div class="version-modal-icon"><span class="material-symbols-outlined">download_for_offline</span></div><h3 class="modal-title" id="version-modal-title">Choose a {esc(product['name'])} build</h3><p class="modal-desc">Select the build that matches your installation.</p></div><div class="version-list">{builds_html}</div></div></div>
    <footer class="home-footer detail-footer"><div class="container footer-grid"><a class="logo home-logo" href="../../" aria-label="ClientStash home"><img class="site-logo" src="../../logo.svg" alt="ClientStash" width="242" height="48"></a><p>Owner-tested third-party utility listings. Not affiliated with Mojang, Microsoft, or DonutSMP.</p><span>© 2026 ClientStash</span></div></footer>
    <script>
    document.querySelectorAll('.detail-faq-item').forEach(item => {{ const button = item.querySelector('button'); button.addEventListener('click', () => {{ const open = !item.classList.contains('active'); document.querySelectorAll('.detail-faq-item').forEach(other => {{ other.classList.remove('active'); other.querySelector('button').setAttribute('aria-expanded', 'false'); }}); if (open) {{ item.classList.add('active'); button.setAttribute('aria-expanded', 'true'); }} }}); }});
    const modal = document.getElementById('downloads'); const openButton = document.getElementById('download-link'); const closeButton = document.getElementById('version-modal-close'); const closeModal = () => {{ modal.classList.remove('active'); modal.setAttribute('aria-hidden', 'true'); }}; openButton.addEventListener('click', event => {{ event.preventDefault(); modal.classList.add('active'); modal.setAttribute('aria-hidden', 'false'); closeButton.focus(); }}); closeButton.addEventListener('click', closeModal); modal.addEventListener('click', event => {{ if (event.target === modal) closeModal(); }}); document.addEventListener('keydown', event => {{ if (event.key === 'Escape') closeModal(); }});
    </script>
</body>
</html>
'''


def render_home_card(product: dict, index: int) -> str:
    detected = str(product.get("status", "")).strip().upper() == "DETECTED"
    image = product.get("image", "")
    media = (
        f'<img src="{esc(image)}" alt="{esc(product["name"])} interface" loading="lazy" width="960" height="540">'
        if image else f'<div class="card-placeholder" aria-hidden="true"><span>{esc(product["name"][0])}</span></div>'
    )
    tags = "".join(f"<span>{esc(tag)}</span>" for tag in product.get("tags", [])[:3])
    return (
        f'<a href="clients/{esc(product["id"])}/" class="card home-client-card{" detected-card" if detected else ""}" '
        f'data-detected="{str(detected).lower()}" data-name="{esc(product["name"])}">'
        f'<div class="client-media">{media}<span class="client-number">{index:02d}</span>'
        f'<span class="client-status{" is-detected" if detected else ""}"><i></i>{esc(product.get("status", "LISTED"))}</span></div>'
        f'<div class="client-card-body"><div class="client-card-heading"><h3>{esc(product["name"])}</h3>'
        f'<span class="client-version">{esc(product.get("version", ""))}</span></div><p>{esc(product["description"])}</p>'
        f'<div class="client-tags">{tags}</div><div class="client-card-footer"><span>{esc(product.get("size", ""))}</span>'
        '<strong>View details <i aria-hidden="true">↗</i></strong></div></div></a>'
    )


def update_homepage(products: list[dict]) -> None:
    path = ROOT / "index.html"
    source = path.read_text(encoding="utf-8")
    start = "                <!-- GENERATED_PRODUCT_CARDS_START -->"
    end = "                <!-- GENERATED_PRODUCT_CARDS_END -->"
    cards = "\n".join("                    " + render_home_card(product, index) for index, product in enumerate(products, 1))
    replacement = f'{start}\n                <div id="product-grid" class="grid home-product-grid" aria-live="polite">\n{cards}\n                </div>\n{end}'
    before, remainder = source.split(start, 1)
    _, after = remainder.split(end, 1)
    source = before + replacement + after
    for product in products:
        source = source.replace(f"detail.html?id={product['id']}", f"clients/{product['id']}/")
    path.write_text(source, encoding="utf-8", newline="\n")


def write_sitemap(products: list[dict]) -> None:
    urls = [SITE_URL] + [f"{SITE_URL}clients/{product['id']}/" for product in products]
    entries = "\n".join(f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{VERIFICATION_UPDATED}</lastmod>\n  </url>" for url in urls)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8", newline="\n")


def main() -> None:
    products = json.loads((ROOT / "products.json").read_text(encoding="utf-8"))
    public = [product for product in products if product.get("visibility") is True]
    clients_dir = ROOT / "clients"
    clients_dir.mkdir(exist_ok=True)
    for index, product in enumerate(public):
        related = [public[(index + offset) % len(public)] for offset in range(1, 4)]
        output = clients_dir / product["id"] / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_product_page(product, related), encoding="utf-8", newline="\n")
    homepage_products = sorted(public, key=lambda product: product["name"].casefold())
    update_homepage(homepage_products)
    write_sitemap(public)
    print(f"Generated {len(public)} static product pages, homepage cards, and sitemap.")


if __name__ == "__main__":
    main()
