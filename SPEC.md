# SmokeHarvest: Automated E2E Test Generation from Live Behavior

## Overview

SmokeHarvest uses Claude Code with the Playwright MCP to crawl a live application, generate Playwright test code reflecting actual behavior, and maintain those tests as a living baseline. On subsequent runs, it diffs new behavior against the baseline and surfaces changes as GitHub PRs for human review.

**This is a starter kit, not a library.** Copy the templates and prompts into your own project and adapt them. There's nothing to install or maintain.

## Problem Statement

End-to-end tests are valuable but tedious to write and maintain. When UI changes, tests break—but it's often unclear whether the breakage represents a bug or an intentional update. Engineers waste time investigating false positives or manually updating selectors.

**SmokeHarvest flips the model:** Instead of writing tests that assert expected behavior, harvest tests from observed behavior. The generated code becomes documentation of "what the app does right now." Changes surface as diffs, categorized for human review.

## Repository Structure

```
smokeharvest/
├── README.md                      # Quick start and concept overview
├── SPEC.md                        # This file - full specification
├── examples/
│   └── httpbin/                   # Working example against httpbin.org
│       ├── smokeharvest.config.yaml
│       ├── critical-path.md
│       └── baseline/
│           └── form-submission.spec.ts
├── templates/
│   ├── smokeharvest.config.yaml   # Starter config to copy into your project
│   └── prompts/
│       ├── initial-crawl.md       # Claude Code prompt for first run
│       └── diff-and-report.md     # Claude Code prompt for subsequent runs
└── docs/
    └── auth-patterns.md           # Handling OTP, OAuth, and other auth flows
```

## Quick Start

1. Copy `templates/smokeharvest.config.yaml` into your project
2. Define your critical paths
3. Run the `initial-crawl.md` prompt with Claude Code + Playwright MCP
4. Commit the generated tests as your baseline
5. After releases, run `diff-and-report.md` to surface changes

## Public Example: httpbin.org

The `examples/httpbin/` directory contains a working example you can run immediately to prove the concept works. httpbin.org is a simple HTTP request/response testing service—no authentication, no bot detection, stable endpoints.

### httpbin Critical Path

1. **Navigate** to httpbin.org/forms/post
2. **Fill the form** — Customer name, pizza size, toppings, delivery instructions
3. **Submit** the form
4. **Verify** the response page displays the submitted data correctly

This example demonstrates the full SmokeHarvest flow without requiring access to any private application.

---

## Real-World Example: Copilot (Flight Planning App)

For a more realistic example, here's how SmokeHarvest would be configured for Copilot, a flight planning application for single-pilot operations. This demonstrates authentication, multi-step workflows, and form interactions.

### Copilot Critical Path

1. **Login** — Username/password authentication
2. **Create flight plan** — New flight with basic details
3. **Add left seat (PIC)** — Assign pilot in command
4. **Add right seat (SIC)** — Assign second pilot (not PIC)
5. **Set departure and arrival** — Airport selection
6. **Edit estimated times** — Modify departure/arrival times
7. **Verify save** — Confirm data persisted correctly

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SmokeHarvest Run                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Claude Code receives trigger (manual or post-release)   │
│                         │                                   │
│                         ▼                                   │
│  2. Load critical path definition from config               │
│                         │                                   │
│                         ▼                                   │
│  3. Playwright MCP crawls live site                         │
│     - Executes each step in critical path                   │
│     - Records selectors, actions, assertions                │
│     - Handles interactive prompts (e.g., OTP)               │
│                         │                                   │
│                         ▼                                   │
│  4. Generate Playwright test code                           │
│     - One test file per critical path                       │
│     - Human-readable, maintainable code                     │
│                         │                                   │
│                         ▼                                   │
│  5. Compare against baseline (if exists)                    │
│     - Diff generated tests vs repo's tests/e2e/             │
│     - Categorize changes                                    │
│                         │                                   │
│                         ▼                                   │
│  6. Output                                                  │
│     - First run: Commit as baseline                         │
│     - Subsequent runs: Create PR with categorized diff      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Critical Path Configuration

A YAML file defining the smoke test scope.

**httpbin example (simple):**

```yaml
# examples/httpbin/smokeharvest.config.yaml
app:
  name: httpbin
  base_url: https://httpbin.org

auth:
  type: none

critical_paths:
  - name: form_submission
    description: Submit the pizza order form and verify response
    steps:
      - action: navigate
        target: /forms/post
        description: Go to the HTML form page

      - action: fill_form
        description: Fill out the pizza order form
        fields:
          - name: custname
            value: "Test Customer"
          - name: custtel
            value: "555-1234"
          - name: custemail
            value: "test@example.com"
          - name: size
            value: "medium"
          - name: topping
            value: ["bacon", "cheese"]
          - name: delivery
            value: "12:00"
          - name: comments
            value: "Ring doorbell twice"

      - action: submit
        description: Submit the form

      - action: verify
        description: Confirm response shows submitted data
        assertions:
          - contains: "Test Customer"
          - contains: "medium"
          - contains: "bacon"
```

**Copilot example (with auth and complex workflow):**

```yaml
# smokeharvest.config.yaml
app:
  name: copilot
  base_url: https://copilot.example.com
  
auth:
  type: username_password
  # Credentials stored in environment variables
  username_env: COPILOT_TEST_USER
  password_env: COPILOT_TEST_PASS

critical_paths:
  - name: flight_plan_creation
    description: Create a complete flight plan with crew assignments
    steps:
      - action: login
        description: Authenticate with username/password
        
      - action: navigate
        target: /flights/new
        description: Go to new flight plan page
        
      - action: fill_form
        description: Create flight plan with basic details
        fields:
          - name: departure_airport
            example: KGNV
          - name: arrival_airport
            example: KJAX
            
      - action: assign_crew
        description: Add PIC and SIC
        roles:
          - position: left_seat
            is_pic: true
          - position: right_seat
            is_pic: false
            
      - action: set_times
        description: Edit estimated departure and arrival times
        
      - action: save_and_verify
        description: Save flight plan and confirm persistence
```

### 2. Test Generation Strategy

Claude + Playwright MCP will:

1. **Execute each step** against the live site
2. **Record interactions** including:
   - Selectors used (preferring data-testid, falling back to stable alternatives)
   - Values entered
   - Assertions that would validate success
3. **Generate idiomatic pytest-playwright code** that another engineer could read and maintain

Example generated output:

```python
# tests/e2e/test_flight_plan_creation.py
# Generated by SmokeHarvest - DO NOT EDIT MANUALLY
# Baseline captured: 2025-01-28T10:30:00Z

import os
import pytest
from playwright.sync_api import Page, expect


class TestFlightPlanCreation:
    """Create a complete flight plan with crew assignments"""

    @pytest.fixture(autouse=True)
    def login(self, page: Page):
        """Authenticate before each test"""
        page.goto("/login")
        page.fill('[data-testid="username"]', os.environ["COPILOT_TEST_USER"])
        page.fill('[data-testid="password"]', os.environ["COPILOT_TEST_PASS"])
        page.click('[data-testid="login-button"]')
        expect(page).to_have_url("/dashboard")

    def test_creates_flight_plan_with_crew_assignments(self, page: Page):
        # Navigate to new flight
        page.click('[data-testid="new-flight-button"]')
        expect(page).to_have_url("/flights/new")

        # Set airports
        page.fill('[data-testid="departure-airport"]', "KGNV")
        page.fill('[data-testid="arrival-airport"]', "KJAX")

        # Assign crew - left seat as PIC
        page.click('[data-testid="add-crew-button"]')
        page.select_option('[data-testid="left-seat-select"]', "pilot-123")
        page.check('[data-testid="left-seat-pic-checkbox"]')

        # Assign crew - right seat (not PIC)
        page.click('[data-testid="add-crew-button"]')
        page.select_option('[data-testid="right-seat-select"]', "pilot-456")
        # Right seat is NOT checked as PIC

        # Set times
        page.fill('[data-testid="departure-time"]', "2024-01-15T09:00")
        page.fill('[data-testid="arrival-time"]', "2024-01-15T10:30")

        # Save
        page.click('[data-testid="save-flight-button"]')

        # Verify persistence
        expect(page.locator('[data-testid="flight-saved-toast"]')).to_be_visible()
        expect(page.locator('[data-testid="departure-airport-display"]')).to_have_text("KGNV")
        expect(page.locator('[data-testid="arrival-airport-display"]')).to_have_text("KJAX")
```

### 3. Diff and Categorization

On subsequent runs, SmokeHarvest compares generated tests against the baseline and categorizes changes:

| Category | Indicators | Example |
|----------|------------|---------|
| 🐛 **Likely Bug** | Element missing, 500 errors, unexpected redirects, assertion failures on core data | `departure-airport-display` no longer exists |
| 🔄 **Probable UI Update** | Selector changed but element still present, text changed, new fields added | `[data-testid="save-button"]` → `[data-testid="save-flight-btn"]` |
| ❓ **Needs Review** | Ambiguous changes, timing differences, intermittent elements | New modal appears sometimes |

#### Screenshot Diffing (Optional but Useful)

If you capture screenshots to compare runs, keep them stable:

- **Fix the viewport** (example: 1024x768) for both exploratory and scripted runs.
- **Prefer viewport-only screenshots** (not full-page) to avoid height drift from dynamic content.
- **Name pairs consistently** (e.g., `explore-01-home.png` and `script-01-home.png`) so automated diffs can match them.

If you are using Playwright MCP inside Docker, screenshots are written in the container (often under `/tmp/playwright-output`). Copy them to your repo with:

```bash
docker cp <container_name>:/tmp/playwright-output/. /path/to/your/repo/screenshots/
```

### 4. Output: GitHub PR

```markdown
## SmokeHarvest Diff Report

**Run:** 2024-01-15 08:30 UTC (post-release)
**Baseline:** commit abc123

### Summary
- 🐛 1 likely bug
- 🔄 2 probable UI updates  
- ❓ 1 needs review

### 🐛 Likely Bugs

#### Missing element: `flight-saved-toast`
The success toast after saving a flight plan is no longer appearing.
- **File:** `tests/e2e/flight-plan-creation.spec.ts:47`
- **Previous:** `await expect(page.locator('[data-testid="flight-saved-toast"]')).toBeVisible();`
- **Current:** Element not found within timeout

### 🔄 Probable UI Updates

#### Selector change: save button
- **Previous:** `[data-testid="save-button"]`
- **Current:** `[data-testid="save-flight-btn"]`
- **Recommendation:** Update baseline if intentional

#### New field: flight notes
A new optional field `flight-notes` was detected on the form.
- **Recommendation:** Add to test coverage

### ❓ Needs Review

#### Timing change: crew assignment
The crew assignment section now requires an additional click to expand.
- **Previous:** Crew fields visible immediately
- **Current:** Requires clicking "Add Crew" to reveal fields
```

## Authentication Handling

### Current: Username/Password

For Copilot's current auth flow, credentials are stored as environment variables and used directly by the generated tests.

### Future: OTP/MFA (Spoken Concept for Demo)

When an application requires one-time passwords:

```
SmokeHarvest: I've reached the login screen and triggered OTP.
              Paste the code when you receive it:
              
Human:        847293

SmokeHarvest: Continuing authentication flow...
```

For fully automated pipelines, this would be wired to an email API (e.g., Resend) to programmatically fetch OTP codes. This is out of scope for the initial demo but worth mentioning as the natural evolution.

## Repo Structure

Tests will live in the Copilot repository:

```
copilot/
├── src/
├── tests/
│   ├── unit/
│   └── e2e/                    # SmokeHarvest managed
│       ├── flight-plan-creation.spec.ts
│       └── ...
├── smokeharvest.config.yaml
└── ...
```

## Integration with QuadPool

SmokeHarvest can be triggered as a QuadPool task:

1. **Trigger:** Post-release webhook or scheduled morning run
2. **Linear ticket:** "Run SmokeHarvest against production"
3. **Claude Code execution:** Uses Playwright MCP to crawl and generate
4. **Output:** PR created, Linear ticket updated with results

## Demo Narrative

For the Fix to Fix recording:

1. **Public example first:** "Here's SmokeHarvest running against httpbin.org—you can try this yourself right now"
2. **Show the flow:** Claude + Playwright MCP fills the form, submits, generates test code
3. **Show generated code:** "This is what the app does right now, captured as executable tests"
4. **Transition to real app:** "Now let me show you what this looks like against a real application..."
5. **Copilot demo:** Run against Copilot, show the more complex critical path with auth
6. **Simulate a change:** Deploy something (or talk through it)
7. **Second run:** Diff surfaces the change
8. **Review PR:** "Is this a bug or intentional? Engineer decides."
9. **Speak to OTP:** "In a real-world scenario with MFA, Claude would pause and prompt for the code"
10. **Call to action:** "Adapt the templates for your own app—the httpbin example shows you how"

## Success Criteria

1. **httpbin example works out of the box:** Someone can clone the repo and run it immediately
2. **Baseline generation works:** First run produces valid, runnable Playwright tests
3. **Diffs are meaningful:** Changes are correctly categorized and surfaced
4. **Code is maintainable:** Generated tests are readable by humans, not just machines
5. **Demo is compelling:** The Fix to Fix episode clearly shows the value proposition
6. **Easy to adapt:** Templates are clear enough that someone can configure for their own app

## Philosophy: Recipe, Not Package

This is intentionally NOT a maintained open source library. It's a recipe—a documented approach with starter files that you copy into your own project and own from there.

**Why:**
- No version compatibility to maintain
- No issues to triage from people using it wrong
- The value is in the *idea* and the *prompts*, not in code that needs to keep working
- Claude + Playwright MCP does the heavy lifting; this just tells it what to do

If the Playwright MCP changes, you update your prompts. If your app changes, you update your config. You own it.

## Learn More

- [docs/auth-patterns.md](./docs/auth-patterns.md) — Handling authentication scenarios
- [docs/visual-diffing.md](./docs/visual-diffing.md) — Optional screenshot diffing recipe
- [examples/httpbin/](./examples/httpbin/) — Working example you can run now

## Open Questions

1. **Test data management:** Should SmokeHarvest create test data (new flights) or use existing data? Creating data is more isolated but adds complexity.

2. **Selector strategy:** Prefer `data-testid` attributes, but what's the fallback hierarchy when they don't exist? (text content → ARIA labels → CSS selectors)

3. **Baseline storage:** Git branch? Tagged commits? Separate baseline file that tracks "last known good"?

4. **Flaky test handling:** How to distinguish genuine bugs from intermittent failures? Multiple runs? Retry logic?

## Non-Goals (For Now)

- Full test suite generation (only critical paths)
- Visual regression testing (only functional assertions)
- Performance testing
- Cross-browser testing (Chromium only for demo)
- Automated OTP handling (spoken concept only)
