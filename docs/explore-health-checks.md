# Explore Health Checks (Recipe Add-on)

Don't blindly trust the explore path. Just because Claude + Playwright MCP can navigate through your app doesn't mean the app is working correctly. A successful crawl through a broken app produces a broken baseline.

## Why

The default SmokeHarvest flow treats the explore path as the source of truth: whatever the live app does becomes the new baseline. This is dangerous. If the app is returning errors, showing empty states, or silently failing—and you generate tests from that behavior—you've just codified bugs as expected behavior.

Health checks run **during** the explore phase. After every interaction (click, submit, navigate), verify that the app responded correctly before moving on.

## Hard Failures

These should **halt the explore and flag immediately**. Do not generate a baseline from a broken app.

### HTTP Errors (4xx/5xx)

After every action that triggers a network request, check for error responses. The Playwright MCP exposes console messages and network activity—use them.

```yaml
# In your critical path config, you can note expected status codes
health_checks:
  fail_on_http_errors: true
  # Some apps return 404 for valid states (e.g., "no results found")
  # List known acceptable error codes per step if needed
  allowed_errors:
    - step: search_empty
      status: [404]
```

**What to look for:**
- `POST` to an API returning `500` after a form submit
- `GET` returning `403` after login (auth didn't stick)
- Any `5xx` is almost always a bug

**What to report:**
```
🛑 HARD FAILURE at step "submit_order"
   POST /api/orders returned 500 Internal Server Error
   Explore halted. Do not generate baseline from this run.
   Action: Investigate the server error before re-running.
```

### JavaScript Errors in Console

Unhandled exceptions, failed fetches, framework error boundaries firing. These show up in the browser console output that Playwright MCP returns after every action.

**What to look for:**
- `Uncaught TypeError`, `Uncaught ReferenceError`
- `Unhandled Promise Rejection`
- Framework-specific: `React error boundary`, Alpine.js `x-` attribute errors
- `Failed to fetch` (network errors from client-side code)

**What to report:**
```
🛑 HARD FAILURE at step "load_dashboard"
   Console error: Uncaught TypeError: Cannot read properties of undefined (reading 'map')
   This suggests a data loading failure, not a UI change.
   Action: Check the application logs and API responses.
```

### Error Elements in the DOM

After every action, check the DOM for error indicators. Many apps show error messages via specific elements, CSS classes, or ARIA roles.

**Common patterns to check:**
- Elements with `role="alert"`
- Elements matching `.error`, `.alert-danger`, `.toast-error`
- Text containing "error", "failed", "something went wrong"
- HTTP error pages (title containing "500", "404", "Not Found")

```yaml
health_checks:
  error_selectors:
    - "[role='alert']"
    - ".error-message"
    - ".toast-error"
    - "[data-testid='error-banner']"
  # Some apps always show an empty alert container—ignore those
  ignore_if_empty: true
```

### Unexpected Navigation

If you click "Submit" and end up on a 404 page, a generic error page, or get bounced back to login—that's not a "new screen to document," it's a failure.

**What to look for:**
- URL contains `/error`, `/404`, `/500`
- Page title contains "Error", "Not Found", "Something went wrong"
- Redirected to login page when session should be authenticated
- URL didn't change at all after a navigation action

## Soft Signals

These should be **flagged in the report for review** but don't necessarily halt the explore.

### Empty Content Where Data Is Expected

A page loads but the main content area is blank. Could be a loading race condition, a failed API call that was swallowed, or a permissions issue.

**What to look for:**
- Main content container exists but has no children
- A list or table that should have rows is empty
- Loading spinner that never resolves (set a reasonable timeout)

**What to report:**
```
⚠️ SOFT SIGNAL at step "view_dashboard"
   Main content area appears empty (0 items in [data-testid="flight-list"])
   This could be a data loading issue or a legitimate empty state.
   Action: Verify the test account has expected data.
```

### Buttons That Stay Disabled

If an action should enable a button but it remains disabled after a reasonable wait, something may be wrong. However, this is sometimes intentional—like a Terms of Service "Accept" button that requires scrolling first.

**What to report:**
```
⚠️ SOFT SIGNAL at step "accept_terms"
   Button [data-testid="accept-btn"] is disabled after action.
   This may require a prerequisite action (e.g., scrolling).
   Action: Check if there's an interaction requirement the explore missed.
```

### Repeated Screens

If you perform an action and the page doesn't change—same heading, same URL, same content—the action may have failed silently.

**What to look for:**
- H1 text is the same before and after an action
- URL unchanged after a navigation/submit action
- No new elements appeared

### Network Requests That Hang

A page loads but a key request never completes. The spinner stays, the data never appears.

**What to look for:**
- Requests pending for longer than a configurable timeout (default: 10s)
- `AbortError` or timeout errors in console

## Retry Logic

Not every failure is real. Transient server errors, network hiccups, and race conditions happen. Before flagging a hard failure:

1. **Retry the action once** after a short pause (2-3 seconds)
2. If the retry succeeds, log it as a **flaky signal** but continue
3. If the retry fails, **halt and flag**

```
⚠️ FLAKY SIGNAL at step "save_flight"
   POST /api/flights returned 500 on first attempt.
   Retry succeeded after 3s pause.
   Action: Investigate intermittent server errors. This may indicate
   a real issue even though the retry passed.
```

## Implementation in the Explore Phase

When Claude + Playwright MCP is executing the explore crawl, it should follow this pattern after every interaction:

1. **Perform the action** (click, fill, submit, navigate)
2. **Wait for network idle** or a known element to appear
3. **Check console** for new JavaScript errors
4. **Check network** for failed HTTP requests
5. **Check DOM** for error indicator elements
6. **Verify transition** — did the page actually change as expected?
7. **If hard failure:** halt, capture screenshot, report error, do not generate baseline
8. **If soft signal:** log it, capture screenshot, continue but include in report

## Impact on the Diff Report

When health checks detect issues, the diff report verdict changes:

| Explore Result | Script Result | Verdict |
|---------------|--------------|---------|
| Clean explore | Scripts pass | ✅ All clear |
| Clean explore | Scripts fail | 🔄 Scripts need update |
| Explore has errors | Scripts fail | 🐛 App may be broken |
| Explore has errors | Scripts pass | ❓ Investigate (app degraded but old paths still work?) |

The key insight: **if the explore path encounters errors, the scripts failing is not a "scripts need update" situation—it's an "app is broken" situation.** Don't generate a new baseline from a broken explore.

## Example: The Terms of Service Scenario

Here's a real example of why this matters. Consider an app with a login flow:

**Before:** Login → OTP → Game
**After:** Login → OTP → Terms of Service → Game

Without health checks, the explore sees the new TOS screen and treats it as the new reality. The diff report says "scripts need update." That's correct in this case—TOS is an intentional addition.

But what if instead of TOS, the app showed an error page after OTP? Without health checks, the explore would still say "scripts need update" and you'd be updating your tests to expect an error page. With health checks:

- The explore detects `role="alert"` or error text on the page
- It flags a hard failure: "App returned an error after OTP verification"
- The report says "App may be broken" instead of "Scripts need update"
- No new baseline is generated from the broken state

The human still makes the final call, but the signal is dramatically better.

## Notes

- Health check selectors are app-specific. Add your app's error patterns to the config.
- Be careful with "error" text matching—some apps legitimately display the word "error" in non-error contexts (e.g., "0 errors found").
- Console warnings (as opposed to errors) are usually noise. Only flag `console.error` level messages.
- If your app uses a client-side error tracking service (Sentry, Bugsnag), those integrations often swallow errors before they hit the console. Check network requests to error tracking endpoints as an additional signal.
