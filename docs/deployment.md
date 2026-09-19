# Public demo deployment

The public demo is hosted at [datarichinsightpoor.github.io/free-dose-check](https://datarichinsightpoor.github.io/free-dose-check/). It follows the GitHub Pages project-URL convention used by the Data-Rich, Insight-Poor modeling portfolio.

## Build and publishing path

Repository Pages settings use GitHub Actions as the build source. `.github/workflows/pages.yml` runs on pushes to `main` and can also be run manually from Actions.

The build installs the scientific-test dependencies, runs the Python test suite, and executes `python tools/build_web.py`. That step builds `web/free_dose_check.zip`, synthetic examples, scientific-documentation downloads, and a complete downloadable source snapshot. Only the resulting `web/` directory is uploaded as the Pages artifact.

The deployment job requires the successful build job and uses the `github-pages` environment with `pages: write` and `id-token: write` permissions. Other workflow steps have read-only repository-content permission. Deployments are serialized so concurrent pushes do not interrupt a publication already in progress.

The separate `scientific-contract` workflow checks Python 3.10, 3.12, and 3.13. The Pages build itself gates deployment on the Python 3.12 scientific contract.

## Static hosting and privacy

The Pages site is a static application. The browser downloads Pyodide 0.27.7 and executes the original Python calculation package locally in a worker; no calculation service, database, login, experimental-data endpoint, or secret is needed.

Hosting and runtime/font providers receive asset requests, not submitted assay inputs. JSON/CSV exports are generated on the user's device.

All application assets use relative paths so the project works under the `/free-dose-check/` URL prefix. The browser worker receives an absolute runtime-package URL derived from the page location rather than assuming hosting at the domain root.

## Verify a deployment

After the `public-demo` workflow succeeds, open the public URL in a clean browser session. Check that the runtime becomes ready, the synthetic constrained case returns the reference values, unsupported assumptions suppress recommendations, and JSON/CSV/source downloads work.

For repeatable browser verification:

```sh
npm ci
npx playwright install chromium
node tools/browser_qa.mjs https://datarichinsightpoor.github.io/free-dose-check/ /tmp/free-dose-pages-qa
python tools/check_browser_parity.py /tmp/free-dose-pages-qa
```

The script exercises the public site, saves browser reports and screenshots, and covers 375/390-pixel mobile layouts. The parity checker compares those reports against the locally checked-out Python core; check out the deployed commit before asserting parity.

## Updating or recovering

Commit changes to `main`; tests and a fresh static build run automatically. If tests or the build fail, investigate that workflow rather than manually copying a partial site. A previously successful deployment remains separate from a failed new build.

To republish a previous scientific version, revert the relevant source changes on `main` and let the same workflow verify and deploy the reverted source. Never repair the browser calculation separately from the Python package.
