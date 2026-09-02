# Game details (0.18.0)

For a detected game with local ES-DE metadata, Companion displays **Show Game
Details** below the actions/documents. Expand it to read genre, developer,
publisher, player count, release date, rating and description. Missing fields do
not create empty rows, and the whole section is absent if nothing can be shown.
The default collapsed state keeps both compact and full action views short.

Descriptions use pages of up to 400 UTF-16 code units, with controller-friendly
**Previous Page** and **Next Page** buttons. Closing the details resets to page 1;
a new detected game/session also closes the panel. Normal descriptions are shown
in full. Rendering is limited to 12,000 code units for unusually large entries,
with an explicit notice, and individual metadata fields are capped at 160.
Markup is displayed as plain React text, never rendered as HTML.

Release dates are displayed as `YYYY-MM-DD`, without local timezone conversion.
The parser accepts compact ES-DE dates, with or without their time component,
and ISO date-only strings. Invalid calendar/time values are hidden. ES-DE's
default `19700101T000000` is treated as unknown rather than a real release date.
Unknown text values and default/unrated zero ratings are hidden. Valid ratings
above zero and at most one are shown as a percentage labeled **ES-DE rating**;
this is scraped metadata, not an independent Companion review.

The plugin only reads metadata already provided by its local ES-DE gamelist
index. This feature performs no web search, scraping, or configuration writes.
It retains the existing launch-session metadata behavior: after changing or
scraping metadata in ES-DE, use Companion's **Refresh Detection** to recreate
the session and reload it. Merely reopening Game Details does not rescrape.

## Test on Steam Deck

The user reported this feature working on their Steam Deck with version 0.18.0
on 2026-09-02. This is a smoke-test report, not validation of every metadata
format, description length or controller.

Launch a game whose metadata has been scraped in ES-DE. Open **Show Game Details**,
check the populated fields, then page through a long description with the
controller. Verify **Hide Game Details**, and that a different game starts
collapsed at its own first page. Games without metadata should keep their normal
actions without an empty details panel. Compact mode and native RetroArch control
are unchanged.

Automated tests cover field selection, unknown/invalid values, valid/leap dates,
rating bounds, description pagination/limits, surrogate-pair boundaries and
metadata passthrough. Real Decky focus/navigation still needs hardware testing.

References: [ES-DE metadata definitions](https://gitlab.com/es-de/emulationstation-de/-/blob/master/es-app/src/MetaData.cpp)
and [ES-DE metadata documentation](https://gitlab.com/es-de/emulationstation-de/-/blob/master/INSTALL.md).
