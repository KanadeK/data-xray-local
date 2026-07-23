## What changed

Explain the user-visible and domain changes.

## Why

Describe the privacy review problem and the chosen boundary.

## Privacy impact

- What source data is read?
- What new data can be persisted?
- How are complete matches kept out of reports?
- Does `--no-network` still fail closed?

## Verification

List the exact commands and results. The minimum complete gate is:

```bash
python scripts/verify.py
python scripts/demo.py
python scripts/package_release.py
```

## Checklist

- [ ] Fixtures are deterministic and synthetic.
- [ ] Success, boundary, error, and privacy-leak tests were added or updated.
- [ ] Both READMEs and relevant security/architecture docs are accurate.
- [ ] No real personal data, token, cookie, private asset, or `Co-authored-by` trailer is included.

