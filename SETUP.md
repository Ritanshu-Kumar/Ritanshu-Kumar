# Setup

1. Delete the old contents of the `Ritanshu-Kumar` profile repository.
2. Copy this folder into that repository.
3. Create a personal access token so the workflow can read your contribution
   data (the default `GITHUB_TOKEN` GitHub Actions provides does **not**
   have permission to read `contributionsCollection`):
   - Go to **Settings → Developer settings → Personal access tokens →
     Tokens (classic)**.
   - Generate a new classic token with the `read:user` scope (this is what
     GitHub's GraphQL contribution-calendar query requires).
   - Copy the generated token.
4. In the profile repo, go to **Settings → Secrets and variables → Actions**
   and add a new repository secret named `STATS_TOKEN` with that token as
   the value.
5. Commit and push.
6. Run **Actions → Refresh profile graphics → Run workflow** once. This
   generates real values for `assets/stats.svg` and `assets/year.svg`,
   replacing the "Run the profile workflow to generate live data"
   placeholders.
7. The scheduled workflow (daily, 03:00 UTC) refreshes the analytics
   automatically after that. You can also re-run it manually any time from
   the Actions tab.

## Regenerating the portrait

This doesn't need the workflow — run it locally whenever you update the
source photo, then commit the resulting SVG:

```bash
pip install pillow
python scripts/generate_portrait.py     # rebuilds assets/portrait.svg
                                         # from assets/portrait-source.jpg
```

## Editing the tech stack

The tech stack row is just static [shields.io](https://shields.io) badges
in `README.md` — no script or asset file to regenerate. To add, remove, or
recolor an entry, edit the corresponding `<img>` line directly. Each badge
follows this pattern:

```
https://img.shields.io/badge/{Label}-15121f?style=for-the-badge&logo={simple-icons-slug}&logoColor={brand-hex}
```

Look up a tool's slug and brand color at https://simpleicons.org.

No project cards or project list are included.
