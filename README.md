# Wise Telecom Nodes Documentation

The public documentation of the Wise Telecom Nodes vaults and their referral commission system.

## Open the Guide

The guide is a website in one file, `index.html` at the root of this repository. Download the repository (the Code button, then Download ZIP) or clone it, and open `index.html` in a browser; no server and no build step are needed, and the page works offline (the fonts it names are fetched from the web when a connection exists and fall back to system fonts otherwise). The sidebar lists the chapters and their sections, the pager at the bottom of each chapter leads to the next one, and every link between chapters stays inside the page.

## The Referral Protocol Guide

`referral-protocol-guide/` holds the guide as Markdown in the GitBook layout: one file per chapter, `README.md` as the overview and `SUMMARY.md` as the table of contents. The guide explains the referral system as it is built, for depositors, referrers, integrators, front end developers, protocol developers and reviewers, and it is the public record of every accepted review finding with its reason. It follows the code: when the referral facets, the registry or the hub change, the chapter that describes the moved behaviour changes with them.

| Chapter | File |
|---|---|
| Referral Protocol Guide (overview) | `referral-protocol-guide/README.md` |
| For Depositors | `referral-protocol-guide/for-depositors.md` |
| For Referrers | `referral-protocol-guide/for-referrers.md` |
| For Integrators and Partners | `referral-protocol-guide/for-integrators.md` |
| UI Integration | `referral-protocol-guide/ui-integration.md` |
| Architecture for Developers | `referral-protocol-guide/architecture.md` |
| Safety and Known Findings | `referral-protocol-guide/safety-and-known-findings.md` |
| Addresses | `referral-protocol-guide/addresses.md` |
| Frequently Asked Questions | `referral-protocol-guide/faq.md` |

The page `index.html` is built from these chapters and is refreshed after every edit, so the two never drift apart. The Markdown is the source; the page is what a reader opens.

The contracts the guide describes live in the vault repository, [wise-telecom-nodes-v2](https://github.com/wise-foundation/wise-telecom-nodes-v2); its configuration records (`config/vault.<product>.<network>.json`) are the source of truth for every address in the Addresses chapter.

## The UI Integration Gists

`ui-integration-gists/` holds the source copies of the referral UI integration guides that are published as gists and linked from the UI Integration chapter, one file per topic. A gist and its copy here are kept identical. The flushing guide is an unpublished draft.

## Rebuilding the HTML

The build needs Python 3 with the `markdown` package. From the repository root:

```
python3 -I tools/build_guide.py
```

The script reads the chapters from `referral-protocol-guide/`, injects them into `tools/guide_template.html` and writes `index.html` at the repository root. Three optional arguments override the source folder, the output file and the template, in that order. The chapter files are listed in the script (`PAGES` and `LINK_MAP`); a new chapter needs an entry in both, a line in `SUMMARY.md` and a bullet in the overview.

## Writing Rules

* Plain English. "You" is the reader and "we" is the protocol operator. Every number is read from the code, and every function name is written as the code declares it.
* No en or em dashes and no double dash asides. A comma, a colon or a new sentence does the job.
* No bare URLs. Every link is a Markdown link.
* No trace of the drafting process: no internal ticket, review or decision numbers in the text, and no attribution trailers or generator lines in commit messages, templates or pull request text. The maintainers are the only authors named anywhere.
* The guide is the record of accepted findings. A newly accepted finding gets its entry in Safety and Known Findings, a fixed one loses it.
* Addresses are copied from a configuration record or a broadcast receipt, never typed.
* Sweep before every publish, from the guide folder:

```
grep -rnP "\xe2\x80\x94|\xe2\x80\x93| -- | - " --include=*.md . | grep -vP "^[^:]*:[0-9]+:#"
grep -rnE "https?://[^ )]+" --include=*.md . | grep -v "](http"
```

The first command lists dashes used as punctuation (a hit inside a code span, such as a subtraction, is fine), the second lists bare URLs.
