# SmokeHarvest

**Generate Playwright tests from live application behavior. Detect changes automatically.**

SmokeHarvest uses Claude Code with the Playwright MCP to crawl your application, generate end-to-end tests reflecting actual behavior, and maintain those tests as a living baseline. On subsequent runs, it diffs new behavior against the baseline and surfaces changes for human review.

## The Idea

Instead of writing tests that assert expected behavior, **harvest tests from observed behavior**.

1. Point SmokeHarvest at your live app
2. It crawls critical paths and generates Playwright tests
3. Those tests become your baseline—documentation of "what the app does right now"
4. After releases, run again and diff against the baseline
5. Changes surface as categorized diffs: 🐛 likely bugs, 🔄 probable UI updates, ❓ needs review

**This is a recipe, not a library.** Copy the templates into your project and adapt them. There's nothing to install or maintain.

## Quick Start

### Try the Example (httpbin.org)

```bash
# Clone this repo
git clone https://github.com/youruser/smokeharvest
cd smokeharvest

# Run the httpbin example with Claude Code + Playwright MCP
claude "Read templates/prompts/initial-crawl.md and execute it against examples/httpbin/"

# Check the generated tests
cat examples/httpbin/baseline/test_form_submission.py
```

### Use It On Your App

1. Copy `templates/smokeharvest.config.yaml` into your project
2. Copy `templates/.env.example` to `.env` and fill in your test credentials
3. Edit the config to define your critical paths
4. Run the initial crawl:
   ```bash
   claude "Read [path]/templates/prompts/initial-crawl.md and execute it against my smokeharvest.config.yaml"
   ```
5. Commit the generated tests as your baseline (but never commit `.env`)
6. After releases, run the diff:
   ```bash
   claude "Read [path]/templates/prompts/diff-and-report.md and execute it against my smokeharvest.config.yaml"
   ```

## What's In This Repo

```
smokeharvest/
├── README.md                      # You're here
├── SPEC.md                        # Full specification and design
├── .gitignore                     # Keeps .env and secrets out of git
├── examples/
│   └── httpbin/                   # Working example against httpbin.org
│       ├── smokeharvest.config.yaml
│       ├── critical-path.md
│       ├── .env.example           # Environment template (no secrets needed for httpbin)
│       └── baseline/
│           └── test_form_submission.py
├── templates/
│   ├── smokeharvest.config.yaml   # Starter config—copy this
│   ├── .env.example               # Environment template—copy to .env
│   └── prompts/
│       ├── initial-crawl.md       # Prompt for first run
│       └── diff-and-report.md     # Prompt for subsequent runs
└── docs/
    └── auth-patterns.md           # Handling login, OTP, OAuth, etc.
```

## Requirements

- [Claude Code](https://claude.ai/code) or Claude with computer use
- [Playwright MCP](https://github.com/anthropics/anthropic-quickstarts/tree/main/mcp-playwright) configured
- A live application to test against

## How It Works

### First Run: Generate Baseline

```
Your App (live) → Claude + Playwright MCP → Generated Tests (baseline)
```

Claude navigates your app, fills forms, clicks buttons, and observes what happens. It generates idiomatic Playwright test code that captures this behavior.

### Subsequent Runs: Diff and Report

```
Your App (live) → Claude + Playwright MCP → Compare to Baseline → Categorized Diff
```

Claude re-runs the critical paths and compares current behavior to the baseline. Differences are categorized:

| Category | Meaning | Example |
|----------|---------|---------|
| 🐛 Likely Bug | Something broke | Element missing, 500 error, assertion fails |
| 🔄 UI Update | Intentional change | New selector, different text, added field |
| ❓ Needs Review | Ambiguous | Timing change, intermittent element |

## Why Not Just Write Tests?

You should write tests. But:

- **Bootstrapping is slow** — SmokeHarvest gets you from zero to baseline in minutes
- **Maintenance is painful** — When selectors change, SmokeHarvest shows you exactly what changed
- **Bugs hide in diffs** — A human reviewing "selector changed" might catch that it shouldn't have

SmokeHarvest doesn't replace your test suite. It's a smoke test that runs after every release and tells you "something changed" so you can investigate.

## Philosophy

This is intentionally **not** a maintained package:

- No versions to keep compatible
- No issues to triage
- The value is in the idea and the prompts, not code that needs updates

If the Playwright MCP changes, update your prompts. If your app changes, update your config. You own it.

## Multi-Environment Setup

Track changes as they propagate through your deployment pipeline by running SmokeHarvest against each environment.

### Option 1: Separate Config Files

```
your-project/
├── smokeharvest.dev.yaml
├── smokeharvest.qa.yaml
├── smokeharvest.staging.yaml
├── smokeharvest.prod.yaml
└── tests/e2e/
    ├── baseline-dev/
    ├── baseline-qa/
    ├── baseline-staging/
    └── baseline-prod/
```

Each config points to a different `base_url` and output directory:

```yaml
# smokeharvest.dev.yaml
app:
  name: myapp-dev
  base_url: https://dev.myapp.com

output:
  test_directory: ./tests/e2e/baseline-dev
```

### Option 2: Environment Variable Override

Use a single config with the base URL from an environment variable:

```yaml
# smokeharvest.config.yaml
app:
  name: myapp
  base_url_env: SMOKEHARVEST_BASE_URL  # reads from environment

output:
  test_directory_env: SMOKEHARVEST_OUTPUT_DIR
```

Then run with:
```bash
SMOKEHARVEST_BASE_URL=https://dev.myapp.com SMOKEHARVEST_OUTPUT_DIR=./tests/e2e/baseline-dev claude "..."
```

### Watching Changes Move Through Environments

The real power is seeing a change propagate:

```
Monday:    Dev baseline shows new selector for checkout button
Tuesday:   QA diff detects the same change (expected ✓)
Wednesday: Staging diff detects it (expected ✓)
Thursday:  Prod diff detects it (expected ✓) — or doesn't (bug! 🐛)
```

If a change appears in prod that you never saw in dev/QA, something went wrong with your pipeline. If a change in dev never makes it to prod, maybe a feature got reverted or stuck.

This turns SmokeHarvest into **deployment pipeline observability**—you're not just testing the app, you're tracking how changes flow through your release process.

## Learn More

- [SPEC.md](./SPEC.md) — Full specification and design rationale
- [docs/auth-patterns.md](./docs/auth-patterns.md) — Handling authentication scenarios
- [examples/httpbin/](./examples/httpbin/) — Working example you can run now

## License

MIT — Do whatever you want with this.
