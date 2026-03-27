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

This add-on applies the space workaround by default:

- Replaces internal `}}` inside cloze content and hints with `} }`
- Handles trailing `}}}` boundary conflicts by rewriting them to safe output
- Preserves nested cloze terminators like `{{{c1::c}}}`
- Adds quick actions in the Browser and reviewer context menu
- Includes a Settings tab and a Support tab with QR codes, copy buttons, and a Ko-fi widget

## Usage

### 1. Bulk fix from Browser

1. Open Browse.
2. Select one or more notes.
3. Click Notes -> Fix MathJax in Cloze (selected notes).
4. A tooltip shows how many notes and replacements were updated.

### 2. Fix current review note

1. While reviewing a card, right-click.
2. Click Fix MathJax in This Note.
3. The current note is updated immediately.

<img width="2083" height="1188" alt="Screenshot_20260307_232051" src="https://github.com/user-attachments/assets/5852640e-4bcf-4dab-ad47-58b95345969e" />
<img width="2083" height="1188" alt="Screenshot_20260307_232059" src="https://github.com/user-attachments/assets/7f0d622d-c714-4c73-888a-c8a875b9b21a" />

## Configuration

Open Tools -> Add-ons -> Fix MathJax in Cloze -> Config.

- Settings tab: update the replacement token used for unsafe internal `}}`
- Support tab: use the embedded Ko-fi button, QR codes, or copy buttons

`config.json`:

```json
{
  "replacement": "} }"
}
```

- `replacement`: string used to replace internal `}}` inside cloze content
- Default: `} }`
- If invalid (empty, non-string, or contains `}}`), the add-on falls back to `} }`

## Notes

- The add-on rewrites `}}` found inside cloze content and at the immediate boundary before cloze termination.
- Malformed cloze starts are left unchanged, and parsing continues so later valid clozes in the same field can still be fixed.
- Development, packaging, and versioning notes live in `DEVELOPMENT.md`.

## Support

If this add-on helps, you can support it from the in-app Support tab or here:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D01W6NQT)
