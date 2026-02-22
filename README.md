
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

- Replaces internal `}}` inside cloze answer text with `} }`
- Leaves the actual cloze terminator untouched
- Supports cloze hints like `{{c1::answer::hint}}`

## Features

- Bulk fix from **Card Browser** on selected notes
- Single-note fix from **Review screen** context menu
- Safe cloze parsing with nesting awareness
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

## Configuration

`config.json`:

```json
{
  "replacement": "} }"
}
```

- `replacement`: string used to replace internal `}}` inside cloze answers.
- Default is `} }` (space workaround).

## Files

- `__init__.py` - Add-on logic, parser, and UI hooks
- `manifest.json` - Add-on metadata
- `config.json` - User-configurable replacement token

## Notes

- The add-on rewrites only `}}` found **inside cloze answer text**.
- Malformed cloze text is left unchanged for safety.
