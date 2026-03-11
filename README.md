
# Fix MathJax in Cloze

An Anki add-on that fixes cloze conflicts where `}}` inside MathJax (or other cloze text) is interpreted as the end of a cloze deletion.

## Cloze Conflict Background

Cloze deletions are terminated with `}}`. If `}}` appears inside cloze content, Anki may close the cloze too early.

- Problematic:

```text
{{c1::[$]\frac{foo}{\frac{bar}{baz}}[/$] blah blah blah.}}
```

- Works (space workaround):

```text
{{c1::[$]\frac{foo}{\frac{bar}{baz} }[/$] blah blah blah.}}
```

LaTeX math mode ignores extra spaces, so rendering remains the same.

Alternative workaround (for cases where visible spaces matter):

```text
{{c1::[$]\frac{foo}{\frac{bar}{baz}<!-- -->}[/$] blah blah blah.}}
```

The same idea also helps when `::` needs to appear in cloze-deleted text, e.g.:

```text
{{c1::std:<!-- -->:variant::~type~}} in C++ is a {{c2::type-safe union}}
```

## What this add-on does

This add-on applies the **space workaround by default**:

- Replaces internal `}}` inside cloze content (answer and hint) with `} }`
- Also handles trailing `}}}` patterns by rewriting to `} }}` style output
- Preserves nested cloze terminators like `{{{c1::c}}}` and rewrites the
  adjacent outer brace boundary instead
- Supports cloze hints like `{{c1::answer::hint}}`

## Features

- Bulk fix from **Card Browser** on selected notes
- Single-note fix from **Review screen** context menu
- Safe cloze parsing with nesting awareness
- Custom add-on config dialog with a **Settings** tab and **Support** tab
- Scrollable support page with large QR codes for UPI, BTC, and ETH
- Copy buttons for UPI ID and wallet addresses
- Configurable replacement token via `config.json`

## Usage

### 1. Bulk fix from Browser

1. Open **Browse**.
2. Select one or more notes.
3. Click **Notes -> Fix MathJax in Cloze (selected notes)**.
4. A tooltip shows how many notes/replacements were updated.

### 2. Fix current review note

1. While reviewing a card, right-click.
2. Click **Fix MathJax in This Note**.
3. The current note is updated immediately.

<img width="2083" height="1188" alt="Screenshot_20260307_232051" src="https://github.com/user-attachments/assets/5852640e-4bcf-4dab-ad47-58b95345969e" />
<img width="2083" height="1188" alt="Screenshot_20260307_232059" src="https://github.com/user-attachments/assets/7f0d622d-c714-4c73-888a-c8a875b9b21a" />


## Configuration

Open **Tools -> Add-ons -> Fix MathJax in Cloze -> Config**.

- `Settings` tab: update the replacement token used for internal `}}`
  rewrites.
- `Support` tab: view large QR codes for UPI, BTC, and ETH in a scrollable
  list, with copy buttons for each payment ID/address.

`config.json`:

```json
{
  "replacement": "} }"
}
```

- `replacement`: string used to replace internal `}}` inside cloze content.
- Default is `} }` (space workaround).
- If `replacement` is invalid (empty, non-string, or contains `}}`), the add-on
  falls back to `} }` for safety.

## Files

- `__init__.py` - Add-on logic, parser, and UI hooks
- `manifest.json` - Add-on metadata
- `config.json` - User-configurable replacement token
- `Support/` - QR codes used in the support tab

## Notes

- The add-on rewrites `}}` found inside cloze content and at the immediate
  boundary before cloze termination (to avoid accidental early closure).
- Malformed cloze starts are left unchanged, and parsing continues so later
  valid clozes in the same field can still be fixed.

## Changelog

### 2026-02-25

- Added handling for trailing `}}}` cloze-boundary conflicts (for example,
  `{{c1::\\mathbf{0}}}` -> `{{c1::\\mathbf{0} }}`).
- Confirmed behavior applies to cloze content inside and outside MathJax.
- Added internal `}}` replacement in cloze hints (not just cloze answers).
- Added safety fallback for invalid custom `replacement` values.
- Changed malformed-cloze handling to continue scanning later clozes.
- Updated documentation to describe boundary rewrite behavior.

### 2026-03-11

- Refactored cloze parsing into reusable helpers for clearer nested-cloze
  handling.
- Fixed nested cloze cases like
  `{{c3::\\(\\sin i_{{{c1::c}}} = ...\\)}}` so the add-on preserves
  `{{c1::c}}` and rewrites the outer brace boundary instead.
- Added a regression test for the nested-cloze brace case.