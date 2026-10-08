# Living research site

The site lives entirely in `explainer/`. Cloudflare publishes only `public/`, so research documents, audio and development files are not uploaded as site assets.

Run `npm ci` and `npm run dev` from this folder. `npm run check` validates data groups, batch arithmetic and the published research state. `npm run deploy` checks and publishes the site.

## Update progress

Edit `public/research.json`: its update date, phase, summary, milestones and decisions. Only mark a task complete when it is complete. These changes are shared after publishing; exploring the site does not alter research progress.

## Add measured results

Keep `results` empty until experiments run. Put public evidence files under `public/results/` and add a result with these fields:

```json
{
  "id": "unique-run-id",
  "condition": "original",
  "budget": 256,
  "sampleSize": 1319,
  "correct": 0,
  "meanTokens": 0,
  "meanSeconds": 0,
  "model": "exact checkpoint and revision",
  "seed": 42,
  "date": "2026-10-09",
  "split": "official-test",
  "notes": "Record prompts, hardware and decoding settings in the evidence file.",
  "source": "/results/unique-run-id.json"
}
```

The values above show the schema, not a real run. Replace every measurement with actual observations. Valid condition IDs are in `RESULT_CONDITIONS` in `public/research-model.js`, including `unchanged` for the additional pretrained reference; budgets are 128, 256 or 512, and splits are `development`, `official-test` or `transfer`. Publish individual runs rather than mixing different seeds, models or splits into one average. Never put credentials, private question sets or student IDs in public evidence files.

## Cloudflare Git connection

Use project name `llm-proj`, production branch `main`, root directory `explainer`, build command `npm run check`, deploy command `npx wrangler deploy`, and the dashboard's default preview command. Cloudflare installs dependencies from the lockfile. The Wrangler configuration declares the public asset directory and the custom domain `llm-proj.cjuy.dev`.

Optional build watch paths can include `explainer/*` to avoid deploying for research-only changes. A local commit does not deploy; a push to the connected production branch does. The initial connection is managed by the user in Cloudflare.

## Design

Mobbin research references informed adjacent explanations and examples: [Turo lesson](https://mobbin.com/screens/c1cc661e-ec5c-4d15-a781-d388cb329940) and [Codecademy learning workspace](https://mobbin.com/screens/d27b1f49-aaa8-465e-aee3-179b0caca154). Their images are not shipped. Atkinson Hyperlegible is self-hosted from Google Fonts with its license in `public/fonts/`.
