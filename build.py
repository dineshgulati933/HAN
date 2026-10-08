"""
Build the website: content/*.yml + templates/ + static/  ->  _site/

    python build.py            build once (this is what GitHub Actions runs)
    python build.py --serve    build, preview at http://localhost:8000, rebuild on save
"""
import argparse
import datetime as dt
import functools
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

try:
    from PIL import Image
except ImportError:  # previews are optional; the site still builds without Pillow
    Image = None

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "_site"
CACHE = ROOT / ".cache" / "img"

TALK_TYPES = {
    "oral": "Oral",
    "poster": "Poster",
    "invited": "Invited talk",
    "seminar": "Seminar",
    "workshop": "Workshop",
    "panel": "Panel",
}
PUB_STATUSES = {"published", "accepted", "in review", "in prep", "preprint"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Old addresses that should keep working (QR codes, bookmarks, links in emails).
REDIRECTS = {
    "conf": "/presentations",
    "python_projects": "/software",
    "iot_projects": "/software",
    "gis_projects": "/software",
    "apps": "/software",
}


class ContentError(Exception):
    pass


# --------------------------------------------------------------------------- text helpers

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def _link(match):
    label, url = match.group(1), match.group(2).replace('"', "&quot;")
    external = url.startswith("http")
    attrs = ' target="_blank" rel="noopener"' if external else ""
    return f'<a href="{url}"{attrs}>{label}</a>'


def inline_md(text):
    """**bold**, *italic*, `code`, [label](url) — everything else is HTML-escaped."""
    if text is None:
        return Markup("")
    s = html.escape(str(text).strip(), quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, s)
    return Markup(s)


def block_md(text):
    """Paragraphs, ## / ### headings and - bullet lists, with inline_md inside."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln.strip() for ln in block.strip().splitlines()]
        if lines[0].startswith("### "):
            out.append(f"<h3>{inline_md(lines[0][4:])}</h3>")
        elif lines[0].startswith("## "):
            out.append(f"<h2>{inline_md(lines[0][3:])}</h2>")
        elif all(ln.startswith("- ") for ln in lines):
            items = "".join(f"<li>{inline_md(ln[2:])}</li>" for ln in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{inline_md(' '.join(lines))}</p>")
    return Markup("\n".join(out))


def day_label(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def range_label(start, end):
    if end == start:
        return day_label(start)
    if (start.year, start.month) == (end.year, end.month):
        return f"{MONTHS[start.month - 1]} {start.day}–{end.day}, {start.year}"
    if start.year == end.year:
        return f"{MONTHS[start.month - 1]} {start.day} – {MONTHS[end.month - 1]} {end.day}, {start.year}"
    return f"{day_label(start)} – {day_label(end)}"


def fuzzy_date(value, where):
    """Accept 2026, '2026-03' or 2026-03-03. Returns (sortable date, display label)."""
    if isinstance(value, dt.date):
        return value, day_label(value)
    text = str(value).strip()
    if re.fullmatch(r"\d{4}", text):
        return dt.date(int(text), 1, 1), text
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", text)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return dt.date(y, mo, 1), f"{MONTHS[mo - 1]} {y}"
    raise ContentError(f"{where}: date '{value}' should look like 2026, 2026-03 or 2026-03-03")


def require(entry, keys, where):
    missing = [k for k in keys if not entry.get(k)]
    if missing:
        raise ContentError(f"{where}: missing {', '.join(missing)}")


def full_date(value, where):
    if not isinstance(value, dt.date):
        raise ContentError(f"{where}: date '{value}' should be a full date like 2026-03-03")
    return value


def static_file(path, where):
    if not (STATIC / path).is_file():
        raise ContentError(f"{where}: file static/{path} not found")
    return path


def normalize_links(links, where):
    for link in links or []:
        require(link, ["label", "url"], where + " -> links")
    return links or []


# --------------------------------------------------------------------------- content loading

def load_yaml(name):
    path = CONTENT / name
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    except yaml.YAMLError as exc:
        raise ContentError(f"{name} is not valid YAML:\n{exc}") from exc


def load_presentations(site):
    events, seen_slugs, self_names = [], {}, {"self", site["name"].lower()}
    for i, ev in enumerate(load_yaml("presentations.yml")):
        where = f"presentations.yml, meeting #{i + 1} ({ev.get('short') or ev.get('name', '?')})"
        require(ev, ["name", "date", "location", "talks"], where)
        ev["start"] = full_date(ev["date"], where)
        ev["end"] = full_date(ev.get("end") or ev["start"], where)
        ev["when"] = range_label(ev["start"], ev["end"])
        ev["label"] = ev.get("short") or ev["name"]
        base = slugify(ev["label"])
        ev["id"] = ev.get("id") or (base if base.endswith(str(ev["start"].year)) else f"{base}-{ev['start'].year}")

        for j, talk in enumerate(ev["talks"]):
            twhere = f"{where}, talk #{j + 1}"
            require(talk, ["title", "type"], twhere)
            talk["type"] = str(talk["type"]).strip().lower()
            if talk["type"] not in TALK_TYPES:
                raise ContentError(f"{twhere}: type '{talk['type']}' must be one of {', '.join(TALK_TYPES)}")
            talk["type_label"] = TALK_TYPES[talk["type"]]
            talk["date"] = full_date(talk.get("date") or ev["start"], twhere)
            talk["event"] = ev
            presenter = str(talk.get("presenter") or "self")
            talk["coauthor_presented"] = presenter.lower() not in self_names
            talk["presenter"] = presenter if talk["coauthor_presented"] else None
            talk["links"] = normalize_links(talk.get("links"), twhere)

            if talk.get("poster"):
                static_file(talk["poster"], twhere)
                if talk.get("poster_preview"):
                    static_file(talk["poster_preview"], twhere)
            if talk.get("slides") and not str(talk["slides"]).startswith("http"):
                static_file(talk["slides"], twhere)
                talk["slides"] = "/static/" + talk["slides"]

            if talk.get("poster") or talk.get("slug"):
                slug = str(talk.get("slug") or f"{ev['id']}-{slugify(talk['title'])[:40]}".strip("-"))
                if slug in seen_slugs:
                    raise ContentError(f"{twhere}: slug '{slug}' is already used by {seen_slugs[slug]}")
                seen_slugs[slug] = twhere
                talk["slug"], talk["page_url"] = slug, f"/conf/{slug}"
            else:
                talk["page_url"] = None
        ev["talks"].sort(key=lambda t: t["date"])
        events.append(ev)

    events.sort(key=lambda e: e["start"], reverse=True)
    return events


def load_publications(site):
    pubs = []
    for i, pub in enumerate(load_yaml("publications.yml")):
        where = f"publications.yml, entry #{i + 1}"
        require(pub, ["authors", "year", "title", "venue"], where)
        pub["status"] = str(pub.get("status") or "published").lower()
        if pub["status"] not in PUB_STATUSES:
            raise ContentError(f"{where}: status '{pub['status']}' must be one of {', '.join(sorted(PUB_STATUSES))}")
        pub["type"] = pub.get("type") or "journal"
        pub["link"] = f"https://doi.org/{pub['doi']}" if pub.get("doi") else pub.get("url")
        pub["badges"] = pub.get("badges") or []
        pub["links"] = normalize_links(pub.get("links"), where)
        pub["_order"] = i
        pubs.append(pub)
    pubs.sort(key=lambda p: (-int(p["year"]), p["_order"]))
    return pubs


def load_news():
    items = []
    for i, item in enumerate(load_yaml("news.yml")):
        where = f"news.yml, item #{i + 1}"
        require(item, ["date", "text"], where)
        item["sort"], item["label"] = fuzzy_date(item["date"], where)
        items.append(item)
    items.sort(key=lambda n: n["sort"], reverse=True)
    return items


def load_software():
    tools = load_yaml("software.yml")
    for i, tool in enumerate(tools):
        where = f"software.yml, entry #{i + 1}"
        require(tool, ["name", "description"], where)
        tool["tags"] = tool.get("tags") or []
        tool["links"] = normalize_links(tool.get("links"), where)
    return tools


def check_crop(site, key):
    crop = site.get(key)
    if crop is None:
        return
    ok = (isinstance(crop, list) and len(crop) == 4 and all(isinstance(v, (int, float)) for v in crop)
          and 0 <= crop[0] < crop[2] <= 1 and 0 <= crop[1] < crop[3] <= 1)
    if not ok:
        raise ContentError(f"site.yml -> {key}: expected [left, top, right, bottom] fractions between 0 and 1, got {crop}")


def load_content():
    site = load_yaml("site.yml")
    require(site, ["name", "url", "nav"], "site.yml")
    refresh_cv_pdf(site)
    if site.get("photo"):
        static_file(site["photo"], "site.yml -> photo")
        check_crop(site, "photo_crop")
        check_crop(site, "avatar_crop")
    if site.get("cv_pdf"):
        static_file(site["cv_pdf"], "site.yml -> cv_pdf")
    for link in site.get("links") or []:
        require(link, ["label", "url"], "site.yml -> links")

    events = load_presentations(site)
    talks = [t for ev in events for t in ev["talks"]]
    years = {}
    for ev in events:
        years.setdefault(ev["start"].year, []).append(ev)

    about_path = CONTENT / "about.md"
    return {
        "site": site,
        "events": events,
        "talks": talks,
        "talk_years": sorted(years.items(), reverse=True),
        "poster_talks": [t for t in talks if t["page_url"]],
        "talk_stats": {
            "total": len(talks),
            "meetings": len(events),
            "by_type": {k: sum(t["type"] == k for t in talks) for k in TALK_TYPES},
            "coauthor": sum(t["coauthor_presented"] for t in talks),
            "with_poster": sum(bool(t.get("poster")) for t in talks),
        },
        "pubs": load_publications(site),
        "news": load_news(),
        "software": load_software(),
        "cv": load_yaml("cv.yml") or {},
        "about": block_md(about_path.read_text(encoding="utf-8")) if about_path.exists() else "",
    }


# --------------------------------------------------------------------------- CV PDF

# Opens a *copy* of the .docx invisibly and saves it as PDF. If Word was already
# running with your documents open, it is left running and untouched.
WORD_EXPORT_PS = r"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$wasInUse = $word.Documents.Count -gt 0
$alerts = $word.DisplayAlerts
try {
    $word.DisplayAlerts = 0
    $m = [Type]::Missing
    $doc = $word.Documents.Open($env:CV_IN, $false, $true, $false, $m, $m, $m, $m, $m, $m, $m, $false)
    $doc.ExportAsFixedFormat($env:CV_OUT, 17)
    $doc.Close($false)
} finally {
    $word.DisplayAlerts = $alerts
    if (-not $wasInUse) { $word.Quit() }
}
"""

WATCH_EXTRA = []  # files outside the repo that should also trigger a rebuild (the .docx CV)


def refresh_cv_pdf(site):
    """Re-export static/<cv_pdf> from the Word CV (site.yml -> cv_source) when the .docx is newer."""
    if not site.get("cv_source") or not site.get("cv_pdf"):
        return
    src, pdf = Path(site["cv_source"]).expanduser(), STATIC / site["cv_pdf"]
    if not src.is_file():
        print(f"CV: {src} isn't on this computer; using the committed static/{site['cv_pdf']}")
        return
    if src not in WATCH_EXTRA:
        WATCH_EXTRA.append(src)
    if pdf.exists() and pdf.stat().st_mtime >= src.stat().st_mtime:
        return
    if sys.platform != "win32":
        print(f"CV: {src.name} changed, but PDF export needs Microsoft Word on Windows; PDF not updated")
        return

    print(f"CV: exporting {src.name} -> static/{site['cv_pdf']} with Word ...")
    with tempfile.TemporaryDirectory() as tmp:
        copy, out = Path(tmp) / f"cv-copy{src.suffix}", Path(tmp) / "cv.pdf"
        shutil.copyfile(src, copy)
        env = {**os.environ, "CV_IN": str(copy), "CV_OUT": str(out)}
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", WORD_EXPORT_PS],
                                    env=env, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            print("CV: Word didn't finish within 3 minutes; PDF not updated")
            return
        if result.returncode != 0 or not out.is_file():
            detail = (result.stderr or result.stdout).strip().splitlines()
            print(f"CV: export failed, keeping the old PDF ({detail[0] if detail else 'no details'})")
            return
        pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, pdf)
    print(f"CV: updated static/{site['cv_pdf']}; commit it so the live site gets it too")


# --------------------------------------------------------------------------- images

def resized(src_rel, width, fmt="webp", quality=82, crop=None, tag=""):
    """Return the /static URL of a resized (optionally cropped) copy of static/<src_rel>.

    crop is [left, top, right, bottom] as fractions of the image size. Results are
    cached in .cache/ so unchanged images aren't re-processed on every build.
    """
    src = STATIC / src_rel
    if Image is None or src.suffix.lower() not in IMAGE_EXTS:
        return "/static/" + src_rel
    stamp = f"{src.stat().st_mtime_ns}-{src.stat().st_size}-{crop}"
    name = f"{slugify(Path(src_rel).with_suffix(''))}{tag}-{width}.{fmt}"
    cached = CACHE / name
    stamp_file = cached.with_suffix(cached.suffix + ".stamp")
    if not (cached.exists() and stamp_file.exists() and stamp_file.read_text() == stamp):
        CACHE.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGB")
            if crop:
                left, top, right, bottom = crop
                im = im.crop((round(left * im.width), round(top * im.height),
                              round(right * im.width), round(bottom * im.height)))
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            im.save(cached, "JPEG" if fmt == "jpg" else "WEBP", quality=quality)
        stamp_file.write_text(stamp)
    dest = OUT / "static" / "generated" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cached, dest)
    return f"/static/generated/{name}"


def attach_images(data):
    site = data["site"]
    if site.get("photo"):
        site["photo_url"] = resized(site["photo"], 640, crop=site.get("photo_crop"), tag="-tall")
        site["avatar_url"] = (resized(site["photo"], 240, crop=site["avatar_crop"], tag="-avatar")
                              if site.get("avatar_crop") else site["photo_url"])
        site["og_image"] = resized(site["photo"], 1200, fmt="jpg")
    for talk in data["poster_talks"]:
        if not talk.get("poster"):
            continue
        poster = talk["poster"]
        talk["poster_full"] = "/static/" + poster
        talk["poster_is_pdf"] = poster.lower().endswith(".pdf")
        preview_src = talk.get("poster_preview") or (None if talk["poster_is_pdf"] else poster)
        if preview_src:
            talk["poster_thumb"] = resized(preview_src, 480)
            talk["poster_large"] = resized(preview_src, 2000, quality=85)
            talk["poster_og"] = resized(preview_src, 1200, fmt="jpg")  # link previews (LinkedIn etc.)


# --------------------------------------------------------------------------- rendering

def highlight_authors(authors, names):
    s = str(inline_md(authors))
    for name in names:
        esc = html.escape(name, quote=False)
        s = s.replace(esc, f'<strong class="me">{esc}</strong>')
    return Markup(s)


def make_env(data):
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["md"] = inline_md
    env.filters["authors"] = lambda a: highlight_authors(a, data["site"].get("highlight_author", []))
    env.filters["day"] = day_label
    env.filters["month"] = lambda d: MONTHS[d.month - 1]
    env.filters["is_external"] = lambda url: str(url).startswith("http")
    env.filters["stop"] = lambda s: "" if str(s).rstrip().endswith((".", "?", "!")) else "."  # avoid "U.S.." / "?."
    today = dt.date.today()
    env.globals.update(data, today=today, build_id=dt.datetime.now().strftime("%Y%m%d%H%M%S"),
                       updated=day_label(today), year=today.year)
    return env


def write(rel_path, text):
    dest = OUT / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def render(env, template, rel_path, url, **ctx):
    write(rel_path, env.get_template(template).render(page_url=url, **ctx))


def person_jsonld(site):
    same_as = [l["url"] for l in site.get("links") or [] if str(l["url"]).startswith("http")]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site["name"],
        "jobTitle": site.get("position"),
        "affiliation": {"@type": "CollegeOrUniversity", "name": site.get("affiliation")},
        "email": site.get("email"),
        "url": site["url"],
        "sameAs": same_as,
    })


def build():
    started = time.time()
    data = load_content()  # validate everything before touching _site/

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(exist_ok=True)
    shutil.copytree(STATIC, OUT / "static", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("README.md", "CNAME", ".DS_Store", "Thumbs.db"))
    attach_images(data)

    env = make_env(data)
    pages = [
        ("index.html", "index.html", "/"),
        ("publications.html", "publications.html", "/publications"),
        ("presentations.html", "presentations.html", "/presentations"),
        ("software.html", "software.html", "/software"),
        ("cv.html", "cv.html", "/cv"),
        ("about.html", "about.html", "/about"),
    ]
    for template, out, url in pages:
        render(env, template, out, url, jsonld=person_jsonld(data["site"]) if url == "/" else None)
    for talk in data["poster_talks"]:
        render(env, "poster.html", f"conf/{talk['slug']}.html", talk["page_url"], talk=talk)
    for old, new in REDIRECTS.items():
        render(env, "redirect.html", f"{old}.html", f"/{old}", target=new)
    render(env, "404.html", "404.html", "/404")

    site = data["site"]
    urls = [u for _, _, u in pages] + [t["page_url"] for t in data["poster_talks"]]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{site['url'].rstrip('/')}{u}</loc></url>\n" for u in urls)
          + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site['url'].rstrip('/')}/sitemap.xml\n")
    write(".nojekyll", "")
    if site.get("domain"):
        write("CNAME", site["domain"] + "\n")

    print(f"Built {len(urls)} pages, {len(data['talks'])} presentations, {len(data['pubs'])} publications "
          f"-> {OUT.relative_to(ROOT)}/ in {time.time() - started:.1f}s")


# --------------------------------------------------------------------------- local preview

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """Serves /cv from cv.html, like GitHub Pages does."""

    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        target = OUT / path.lstrip("/")
        as_html = OUT / (path.strip("/") + ".html")
        if path != "/" and not target.is_file() and as_html.is_file():
            self.path = "/" + path.strip("/") + ".html"  # /conf -> conf.html even though conf/ exists
        elif not target.exists():
            self.path = "/404.html"
        return super().send_head()

    def log_message(self, *args):
        pass


def snapshot():
    files = [p for d in (CONTENT, TEMPLATES, STATIC) for p in d.rglob("*") if p.is_file()]
    files += [p for p in WATCH_EXTRA if p.is_file()]
    return {p: p.stat().st_mtime_ns for p in files}


def watch():
    seen = snapshot()
    while True:
        time.sleep(1)
        now = snapshot()
        if now != seen:
            seen = now
            try:
                build()
            except ContentError as exc:
                print(f"\n  CONTENT ERROR: {exc}\n")
            except Exception as exc:  # keep the preview alive while editing templates
                print(f"\n  BUILD ERROR: {type(exc).__name__}: {exc}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true", help="preview locally and rebuild on changes")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        build()
    except ContentError as exc:
        print(f"\nCONTENT ERROR: {exc}\n")
        sys.exit(1)

    if args.serve:
        threading.Thread(target=watch, daemon=True).start()
        handler = functools.partial(PreviewHandler, directory=str(OUT))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"Previewing at http://localhost:{args.port}  (edits rebuild automatically, Ctrl+C to stop)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
