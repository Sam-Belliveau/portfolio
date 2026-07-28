# samb.nyc

Personal research website, in the style of a classic academic homepage.

## Updating the site

All content lives in [`src/content.jsx`](src/content.jsx) — profile, news,
publications, projects, experience, education, and honors are plain data
exported from that one file. Edit it and push to `main`; GitHub Actions
builds and deploys to GitHub Pages automatically.

[`src/App.jsx`](src/App.jsx) renders that content and
[`src/index.css`](src/index.css) styles it. Neither needs to change for
routine updates.

Figure thumbnails live in `src/assets/figures/`, exported from the original
project repositories. The résumé link points at the latest release of
[Sam-Belliveau/resume](https://github.com/Sam-Belliveau/resume), which is
also vendored as a submodule at `src/assets/resume_repo` and serves as the
source of truth for the site's facts.

## Development

```sh
npm install
npm run dev      # local preview
npm run lint
npm run build
```
