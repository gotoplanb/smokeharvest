# httpbin.org Form Submission - Critical Path

This example tests the HTML form at httpbin.org/forms/post, which simulates a pizza order form.

## Why This Example?

- **No authentication required** — Anyone can run this immediately
- **Stable endpoints** — httpbin.org is designed for testing and rarely changes
- **Simple but complete** — Demonstrates navigation, form filling, submission, and verification
- **No rate limiting** — You can run this repeatedly without issues

## The Flow

1. Navigate to https://httpbin.org/forms/post
2. Fill out the pizza order form:
   - Customer name: "Test Customer"
   - Phone: "555-1234"
   - Email: "test@example.com"
   - Size: Medium
   - Toppings: Bacon, Cheese
   - Delivery time: 12:00
   - Comments: "Ring doorbell twice"
3. Submit the form
4. Verify the response page shows all the submitted data

## Expected Behavior

After submission, httpbin returns a page showing the form data as JSON. The test verifies that our submitted values appear in the response.

## Running This Example

```bash
# From the smokeharvest repo root, with Claude Code + Playwright MCP configured:

# First run - generate baseline tests
claude "Read templates/prompts/initial-crawl.md and run it against examples/httpbin/"

# The generated tests will appear in examples/httpbin/baseline/

# Subsequent runs - diff against baseline
claude "Read templates/prompts/diff-and-report.md and run it against examples/httpbin/"
```

## What Gets Generated

See `baseline/test_form_submission.py` for the generated pytest-playwright test code.
