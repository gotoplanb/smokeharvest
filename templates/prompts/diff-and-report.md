# SmokeHarvest: Diff and Report Prompt

Use this prompt with Claude Code + Playwright MCP after releases to detect changes.

---

## Prompt

```
I need you to run a smoke test against a live website and compare the results to our baseline tests.

Read the configuration file at [PATH_TO_CONFIG]/smokeharvest.config.yaml

**Step 1: Execute the critical paths**

For each critical path defined in the config:
1. Use the Playwright MCP to execute the same steps as the baseline
2. Record what actually happens:
   - Which selectors still work?
   - Which selectors have changed?
   - Are there new elements that weren't there before?
   - Are there elements missing that were there before?
   - Do all assertions still pass?

**Step 2: Compare against baseline**

Read the existing baseline tests in the output directory.

Compare the current behavior to the baseline and categorize each difference:

🐛 **Likely Bug** - Use this category when:
- An element that was present is now missing entirely
- A page returns an error (500, 404, etc.)
- An assertion that verified core data now fails
- A form submission that worked now fails

🔄 **Probable UI Update** - Use this category when:
- A selector changed but the element is still present and functional
- Text content changed (button labels, headings, etc.)
- New optional fields or elements appeared
- Layout changed but functionality is intact

❓ **Needs Review** - Use this category when:
- The change is ambiguous
- Timing or intermittent behavior differences
- Could be either a bug or intentional change

**Step 3: Generate report**

Create a markdown report with:
1. Summary: counts of each category
2. Details for each difference, including:
   - The file and line number in the baseline
   - What the baseline expected
   - What actually happened
   - Your categorization and reasoning
3. Recommended actions

**Step 4: Generate updated tests**

If there are changes categorized as "Probable UI Update", generate updated test code that reflects the new behavior. Save these as `_new.py` files alongside the baseline (don't overwrite the baseline).

**Step 5: Create PR description**

Generate a GitHub PR description that:
- Summarizes what changed
- Lists each change by category
- Helps a reviewer quickly decide: bug or intentional?
```

---

## Usage

```bash
# After a release, run this to check for changes
claude "Read the prompt at templates/prompts/diff-and-report.md and execute it against examples/httpbin/"
```

## What Happens

1. Claude re-runs the critical paths against the live site
2. Compares current behavior to the baseline tests
3. Categorizes every difference
4. Generates a report you can review
5. Creates updated test files (as `.new.spec.ts`) for probable UI changes
6. Drafts a PR description

## Reviewing the Output

- **🐛 Likely Bugs**: Investigate these immediately - something may be broken
- **🔄 Probable UI Updates**: Review and merge the `_new.py` files if the changes are intentional
- **❓ Needs Review**: Use your judgment - may need manual testing

## Updating the Baseline

If the changes are intentional:
```bash
# Replace baseline with the new tests
mv baseline/test_form_submission_new.py baseline/test_form_submission.py
git add baseline/
git commit -m "Update SmokeHarvest baseline after [release/change]"
```
