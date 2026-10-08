# hydroagrinexus.com

Personal academic website of Dinesh Gulati. All content lives in plain-text files in
`content/`; a small Python script turns them into the website, and GitHub Actions
publishes it on every push to `main`.

```
content/            <- the only folder you edit for routine updates
  site.yml          name, bio, photo, links, research interests, menu
  news.yml          short dated updates on the home page
  publications.yml  papers (your name is bolded automatically)
  presentations.yml talks & posters, grouped by meeting, with tags
  software.yml      web apps and packages
  cv.yml            education, experience, grants, awards, skills
  about.md          the About page story
static/
  posters/          new poster files go here
  images/           your photo (crops are set in site.yml)
  assets/           cv_dinesh.pdf (exported from your Word CV by the build)
  css/site.css      colors and fonts are variables at the top
  js/site.js        mobile menu, "Upcoming" badges, presentation filters
templates/          page layouts (Jinja2); _macros.html draws every card
build.py            content + templates -> _site/
```

Everything you add appears in all the right places: a new talk shows up on the
Presentations page, in the CV page, and in the stats. Nothing is typed twice.

## Everyday updates

You can do all of these directly on github.com (open the file, click the pencil,
commit to `main`). The site updates about a minute later; check the **Actions** tab
if it doesn't.

**New talk or poster** — add a block to `content/presentations.yml`:

```yaml
- name: ASABE Annual International Meeting
  short: ASABE AIM 2027
  date: 2027-07-11
  end: 2027-07-14
  location: Omaha, NE
  talks:
    - title: My talk title
      type: oral                      # oral | poster | invited | seminar | workshop | panel
    - title: My poster title
      type: poster
      poster: posters/asabe27_et.png  # upload the file to static/posters/ first
      slug: asabe27                   # page: hydroagrinexus.com/conf/asabe27
    - title: Talk my advisor gave
      type: oral
      presenter: Dr. Meetpal S. Kukal # adds "Presented by …" + "Co-author presented" tag
```

Meetings that haven't ended yet get an **Upcoming** badge automatically, and it
disappears on its own the day after the meeting.

**Printing a QR code for a poster?** Pick the `slug` first, push, check that
`hydroagrinexus.com/conf/<slug>` loads, then make the QR code. Never rename a slug
after printing.

**New paper** — add to `content/publications.yml` (`featured: true` also lists it
on the home page). Add a line to `news.yml` if you want it announced.

**New award, grant, or job** — `content/cv.yml`.

**New CV PDF** — save your Word CV (`cv_source` in `site.yml`) and run
`python build.py` on your computer. If the .docx is newer than the PDF, the build
re-exports `static/assets/cv_dinesh.pdf` with Word (from a copy, so the document you
have open isn't touched). Commit the new PDF so the live site gets it; GitHub can't
see your D: drive, so it uses whatever PDF is committed. While `--serve` is running,
just saving the .docx in Word is enough.

## Previewing locally (optional)

```bash
pip install -r requirements.txt
python build.py --serve
```

Open http://localhost:8000. Pages rebuild whenever you save a file in `content/`,
`templates/`, or `static/` (restart after editing `build.py` itself).

## When something is wrong

The build checks your content before publishing and stops with a plain message,
for example:

```
CONTENT ERROR: presentations.yml, meeting #2 (IWQW 2026), talk #1: type 'Poster' must be one of oral, poster, invited, ...
CONTENT ERROR: presentations.yml, meeting #1 (ASABE AIM 2027), talk #2: file static/posters/asabe27_et.png not found
```

If that happens on GitHub, the old site stays online; open the failed run in the
**Actions** tab, fix the line it names, and commit again. YAML tips: indent with
spaces (never tabs), and put a title in quotes if it contains a colon.

## How it's deployed

`.github/workflows/pages.yml` runs `python build.py` on every push and pull request.
On `main` it publishes `_site/` to the `gh-pages` branch, which GitHub Pages serves.
`_site/` is never committed. Old addresses (`/conf`, `/python_projects`, …) redirect
to their new pages; see `REDIRECTS` in `build.py`.
