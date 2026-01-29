# SmokeHarvest: Self-Heal Prompt

Use this prompt with Claude Code + Playwright MCP to fix failing Playwright tests by exploring the live app, comparing what the app actually does to what the tests expect, and updating the tests to match reality.

---

## Prompt

```
I have Playwright tests that are failing against a live application. I need you to explore
the app using the Playwright MCP, compare what you find to the existing test scripts, and
fix the tests to match the current app behavior.

Read the SmokeHarvest docs at [PROJECT]/smokeharvest/docs/ for guidance—especially
explore-health-checks.md for detecting real failures vs. intentional changes.

**Step 1: Create a timestamped run folder**

Create a folder for this run:

    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    mkdir -p screenshots/$TIMESTAMP/explore screenshots/$TIMESTAMP/script

All screenshots for this run go in this one folder.

**Step 2: Explore the live app**

Use the Playwright MCP (browser tools) to manually walk through the application's
critical path. At each step:

1. Take a screenshot named `NN-description.png` (e.g., `01-login.png`, `03-after-otp.png`)
   These will be saved by the MCP and later copied into `screenshots/$TIMESTAMP/explore/`
2. Use a fixed viewport of 1024x768
3. Perform health checks after every action:
   - Check console for JavaScript errors
   - Check for error elements in the DOM (role="alert", .error, etc.)
   - Check network for failed HTTP requests
   - Verify the page actually transitioned (heading changed, new content appeared)
4. If the app requires credentials, read them from the project's .env file
5. If the app requires an OTP or interactive step, pause and ask the user

If you encounter a hard failure (HTTP errors, JS exceptions, error elements), STOP
and report the failure. Do not proceed to fix tests against a broken app.

After exploring, copy explore screenshots from Docker:

    docker cp <container>:/tmp/playwright-output/. screenshots/$TIMESTAMP/explore/

**Step 3: Run the existing Playwright test scripts**

Run the existing test suite with the SHOT_RUN environment variable set so script
screenshots land in the right place:

    SHOT_RUN=screenshots/$TIMESTAMP pytest tests/test_visual_script.py -v

Script screenshots go into `screenshots/$TIMESTAMP/script/` with the same
`NN-description.png` naming to pair with explore screenshots.

If tests fail (expected), capture what the test actually sees at the failure point.

**Step 4: Visual diff**

If a diff script exists at smokeharvest/scripts/diff_screenshots.py, run it:

    python3 smokeharvest/scripts/diff_screenshots.py screenshots/$TIMESTAMP

This generates `screenshots/$TIMESTAMP/diff/` images and `screenshots/$TIMESTAMP/report.md`.

The report classifies each step as MATCH (RMS < 22), REVIEW (22-30), or DIFFERS (≥ 30)
and gives a verdict: ALL CLEAR, REVIEW NEEDED, or SCRIPTS NEED UPDATE.

Otherwise, compare the explore vs script screenshots manually and produce a markdown
report identifying which steps match and which diverge.

**Step 5: Assess and recommend**

Based on the explore health checks and the visual diff:

- If explore was clean and scripts fail: **update the scripts** to match the new flow
- If explore had errors and scripts fail: **report the app is broken**, do not update scripts
- If explore had soft signals: **flag for human review** before updating scripts

**Step 6: Fix the tests (if explore was clean)**

Update the failing Playwright test files to account for the changes discovered
during exploration. Common fixes include:

- Adding new steps for screens that were inserted into the flow
- Updating selectors that changed
- Updating expected text content
- Adding new test cases for new functionality
- Updating helper functions used across tests

After fixing, re-run the tests to confirm they pass, then re-run the full visual
diff to confirm the report shows ALL CLEAR.
```

---

## Usage

```bash
# Point Claude at your project with failing tests
claude "Read smokeharvest/templates/prompts/self-heal.md and execute it. \
  My app is running at http://localhost:5050. \
  The failing tests are in tests/test_login_flow.py."
```

## What Happens

1. Claude creates a timestamped run folder under `screenshots/`
2. Claude explores your live app with Playwright MCP, taking screenshots into `explore/`
3. Claude runs your existing (failing) test scripts, capturing into `script/`
4. Screenshots are diffed — `diff/` images and `report.md` land in the same folder
5. Health checks determine if the app is broken or if the scripts are stale
6. If the app is healthy, Claude updates the test scripts to match current behavior
7. Updated tests are re-run to confirm ALL CLEAR

## Output

Everything for one run in one folder:

```
screenshots/20260129-181436/
├── explore/          <- what the live app looks like
│   ├── 01-login.png
│   ├── 02-otp.png
│   └── ...
├── script/           <- what the test scripts see
│   ├── 01-login.png
│   ├── 02-otp.png
│   └── ...
├── diff/             <- pixel differences
│   ├── 01-login.png
│   └── ...
└── report.md         <- verdict: ALL CLEAR / REVIEW NEEDED / SCRIPTS NEED UPDATE
```

## When to Use This

- After deploying a feature that intentionally changes the UI flow
- When tests start failing and you're not sure if the app is broken or the tests are stale
- As a periodic maintenance step to keep smoke tests aligned with the live app

## When NOT to Use This

- If you know the app is broken — fix the app first
- If the test failures are intermittent/flaky — that's a different problem (see SPEC.md Open Questions)
- If you want to generate tests from scratch — use `initial-crawl.md` instead
