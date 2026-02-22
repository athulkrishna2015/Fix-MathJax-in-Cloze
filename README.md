# Fix MathJax in Cloze

An Anki add-on that fixes MathJax rendering issues inside cloze deletions by rewriting problematic `}}` sequences inside cloze content.

## What it fixes

Example transformation:

- From:

```text
The general depolarization field is expressed as{{c2::\(\vec{E}_{\text{dep}} = -\frac{N\vec{P}}{\varepsilon_0}\)}},, where the symbol \(N\) represents...
```

- To:

```text
The general depolarization field is expressed as {{c2::\(\vec{E}_{\text{dep}\ } = -\frac{N\vec{P}\ }{\varepsilon_0}\)}}, where the symbol \(N\) represents...
```

This prevents accidental early cloze termination when `}}` appears inside MathJax content.

## Features

- Bulk fix from **Card Browser** on selected notes
- Single-note fix from **Review screen** context menu
- Safe cloze parsing (supports cloze hints like `{{c1::answer::hint}}`)
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
  "replacement": "}\\ }"
}
```

- `replacement`: string used to replace internal `}}` inside cloze answers.
- Default is `}\ ` (as represented in JSON: `"}\\ "`).

## Files

- `__init__.py` - Add-on logic, parser, and UI hooks
- `manifest.json` - Add-on metadata
- `config.json` - User-configurable replacement token

## Notes

- The add-on only rewrites `}}` found **inside cloze answer text**.
- Malformed cloze text is left unchanged for safety.
