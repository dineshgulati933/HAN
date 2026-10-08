# Posters

Drop new poster files here (PNG, JPG, or PDF), then point to them from
`content/presentations.yml`:

```yaml
poster: posters/asabe26_dairy_footprint.png
slug: asabe26-dairy        # -> hydroagrinexus.com/conf/asabe26-dairy
```

- Name files `<meeting><yy>_<topic>.png`, lowercase, no spaces.
- Export at full resolution; the build makes small web previews automatically.
- For a PDF poster, also add `poster_preview: posters/<name>.png` (a screenshot)
  so it gets a thumbnail.
