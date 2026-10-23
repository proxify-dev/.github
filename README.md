# proxify-dev/.github

The public org page at [github.com/proxify-dev](https://github.com/proxify-dev): `profile/README.md`
and the images it shows. The members-only page lives in `proxify-dev/.github-private`.

Every image is drawn from live sources, so nothing here is edited by hand when a repo ships:

| Image | Script | Reads |
|---|---|---|
| `banner-{light,dark}.gif` | `scripts/banner_gif.py` | agentic-kit README: the summary under the tagline, and the "You ask Claude" table (one scene per row) |
| `kit-strip-{light,dark}.svg` | `scripts/org_public.py` | agentic-kit topics |
| `playbook-banner-{light,dark}.png` | `scripts/banner_site.py` | agentic.proxify.io: page title, subtitle, a screenshot |
| `playbook-strip-{light,dark}.svg` | `scripts/org_public.py` | agentic-playbook README: the `###` sections under `## Documentation` |

`.github/workflows/refresh-profile.yml` reruns them daily (the site screenshot on Mondays only)
and commits what changed.

## Run locally

```sh
uv run --with pillow python3 scripts/banner_gif.py
python3 scripts/org_public.py
uv run --with pillow python3 scripts/banner_site.py   # needs Google Chrome; set $CHROME if not on PATH
```

## Failure alerts

Set the repo secret `SLACK_WEBHOOK_URL` to post failed runs to Slack. Without it a failed run
is only visible in the Actions tab.

Fonts in `scripts/fonts/` are Inter and JetBrains Mono, both under the SIL Open Font License.
