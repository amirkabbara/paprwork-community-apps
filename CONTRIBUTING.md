# Contributing App Bundles

Thank you for contributing to the Paprwork community! This guide explains how to submit your own app bundles.

---

## Prerequisites

- [Paprwork](https://github.com/Papr-ai/paprwork) installed and running
- Git and a GitHub account

---

## Step 1: Create Your App Bundle

The easiest way to create a bundle is inside Paprwork:

1. Build your mini-app in Paprwork
2. Ask the AI agent: *"Export this app as a bundle"*
3. The agent uses `export_app_bundle` to create a bundle at `~/PAPR/bundles/{your-bundle-id}/`

Your bundle will have this structure:

```
your-bundle-id/
├── manifest.json      # Required: bundle metadata
├── README.md          # Recommended: description for users
├── apps/
│   └── your-app-id/
│       ├── index.html # Required: app entry point
│       ├── app.ts     # Your app logic
│       └── style.css  # Your styles
└── jobs/              # Optional: automation jobs
    └── your-job-id/
        ├── job.json
        └── code/
```

---

## Step 2: Prepare Your Submission

### Bundle Checklist

- [ ] `manifest.json` is valid and complete
- [ ] `schemaVersion` is `"1.0.0"`
- [ ] `minPaprworkVersion` is set correctly (use `"2.0.0"` if unsure)
- [ ] `index.html` loads without errors
- [ ] No API keys, secrets, or personal data in any files
- [ ] README.md describes what the app does

### manifest.json Requirements

Your manifest must include at minimum:

```json
{
  "schemaVersion": "1.0.0",
  "bundleId": "your-unique-id",
  "name": "Your App Name",
  "version": "1.0.0",
  "createdAt": "2026-01-01T00:00:00.000Z",
  "minPaprworkVersion": "2.0.0",
  "description": "Brief description of your app",
  "app": {
    "id": "your-app-id",
    "name": "Your App Name",
    "version": "1.0.0",
    "entryFile": "index.html",
    "appPath": "apps/your-app-id"
  },
  "jobs": [],
  "sqlite": [],
  "deploymentProfiles": [],
  "sync": {
    "preferredRoot": "~/PAPR",
    "bundleSubpath": "bundles",
    "cloudReady": true
  }
}
```

---

## Step 3: Submit a Pull Request

1. **Fork** this repository
2. Copy your bundle folder into `bundles/your-bundle-id/`
3. Add an entry to `registry.json`:

```json
{
  "bundleId": "your-bundle-id",
  "name": "Your App Name",
  "description": "Brief description",
  "version": "1.0.0",
  "author": "your-github-username",
  "tags": ["relevant", "tags"],
  "minPaprworkVersion": "2.0.0",
  "path": "bundles/your-bundle-id"
}
```

4. Open a pull request with:
   - A clear title (e.g., "Add: Expense Tracker app bundle")
   - A description of what your app does
   - A screenshot if possible

---

## Guidelines

- **One app per bundle** - keep bundles focused
- **No external dependencies** - apps should work offline
- **No secrets** - never include API keys, tokens, or credentials
- **Keep it small** - avoid large assets (images > 500KB, videos, etc.)
- **Test before submitting** - import your own bundle to verify it works
- **Use descriptive IDs** - `expense-tracker` not `app1`

---

## Review Process

1. A maintainer will review your PR
2. We check: valid manifest, no secrets, app loads correctly
3. If approved, your app appears in Paprwork's Community tab on merge

---

## Questions?

Open an [issue](https://github.com/Papr-ai/paprwork-community-apps/issues) if you need help.
