# gopass for Alfred 6

Search, copy, and edit gopass entries with Alfred's native UI.

## Installation

Requires Alfred 6 with Powerpack, Python 3, and an initialized gopass store.
Run `make release` and open the resulting `../gopass.alfredworkflow` in Alfred 6.

## Usage

Type `gp` to browse the store or `gp search terms` to open a filtered list.

| Shortcut | Action |
| --- | --- |
| Enter | Copy the password using gopass's timed clipboard |
| Command + Enter | Open the selected entry's editor |
| Shift + Enter | Copy the username |
| Control + Enter | Open the stored HTTP(S) website |
| Command + K | Open the actions menu |
| Command + F | Focus search |

The window opens with focus on the results. After typing into the search field,
use Down Arrow to return to the results before pressing Shift + Enter. The
actions menu also contains Copy Username.

The edit sheet supports username, website, and a replacement password.
Leave the password blank to retain the current one. Command + S saves, and
Escape cancels. The editor operates on conventional gopass entries with the
password on the first line and `username:` (or `user:` / `login:`) and
`url:` (or `website:`) fields on subsequent lines. Other entry content is
preserved.
