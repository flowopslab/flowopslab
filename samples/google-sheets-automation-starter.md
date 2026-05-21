# Google Sheets Automation Starter

This is a compact checklist FlowOps Lab uses for same-day Google Sheets automation jobs.

## Good Fit

- Pull rows from one sheet into another
- Clean and deduplicate lead/customer records
- Add time-based or on-edit triggers
- Generate daily summary tabs
- Send simple Gmail notifications from a sheet
- Create a clear handoff note so the owner can maintain it

## First-Scope Questions

1. Which spreadsheet is the source of truth?
2. Which tabs need to be read or written?
3. What fields make a row unique?
4. What should happen to invalid or duplicate rows?
5. Should the automation run on edit, hourly, daily, or manually?
6. Who should receive notifications?

## Same-Day Deliverable

For a focused $50 setup, the output is usually:

- One working Apps Script
- Trigger setup instructions
- A before/after test case
- A short README in the spreadsheet or a separate Markdown file
- Notes on limits, failure cases, and how to disable the trigger

## Boundary

Do not send passwords, private keys, payment card data, medical data, or full sensitive customer exports before fit confirmation.
