# Contributing

Thanks for taking the time to improve KnightWarden Core.

## Before You Open a Pull Request

- Keep changes downstream-agnostic. This repository should not depend on management systems, customer-specific configuration, or downstream extension packages.
- Do not include secrets, credentials, customer data, private evidence, raw prompts, transcripts, mailbox contents, or machine-local paths.
- Keep fixtures fictional and clearly example-shaped.
- Prefer small pull requests with a focused explanation of the behavior or contract being changed.

## Local Checks

Run the same checks as CI before opening a pull request:

```text
python3 -m compileall -q src scripts tests
python3 scripts/check_core_boundary.py
python3 scripts/check_external_workflow_reference_model.py
python3 scripts/check_normalized_external_approval_vocabulary.py
python3 -m unittest discover -s tests
```

## Reporting Security Issues

Please do not open a public issue with exploit details, credentials, private data, or sensitive reproduction material. Follow `SECURITY.md` instead.
