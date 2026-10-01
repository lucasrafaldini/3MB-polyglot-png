# Contributing to 3MB-polyglot-png

Thanks for your interest in contributing! 🎉 This project welcomes issues and
pull requests of all sizes, and it participates in
[Hacktoberfest](https://hacktoberfest.com/).

## Ways to contribute

- 🐛 **Report bugs** — open an issue with clear reproduction steps.
- 💡 **Suggest features** — open a feature-request issue.
- 📝 **Improve docs** — typos, clarifications, examples, tutorials.
- 🧪 **Add tests** — edge cases are always appreciated.
- 🔧 **Fix issues** — browse the
  [issue tracker](https://github.com/lucasrafaldini/3MB-polyglot-png/issues),
  especially items labelled `good first issue` and `hacktoberfest`.

## Development setup

```bash
git clone https://github.com/lucasrafaldini/3MB-polyglot-png.git
cd 3MB-polyglot-png
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a pull request

1. **Create a branch** off `main` (e.g. `fix/zip-offsets`).
2. **Write or update tests** for your change.
3. **Run the checks locally** and make sure they pass:
   ```bash
   pytest
   ruff check .
   ```
4. **Keep commits focused** and write clear commit messages.
5. **Describe your change** in the PR, linking any related issue
   (e.g. `Closes #12`).

## Pull request guidelines

- One logical change per PR keeps reviews fast.
- Follow the existing code style; `ruff` enforces most of it.
- Add docstrings for new public functions.
- Be patient and kind in review discussions — see our
  [Code of Conduct](CODE_OF_CONDUCT.md).

## Hacktoberfest notes

- Quality over quantity: spammy or automated PRs will be marked `invalid`
  or `spam` and will not count.
- Meaningful contributions will be merged or labelled `hacktoberfest-accepted`.
- If you're new, comment on an issue to let us know you're working on it so we
  can avoid duplicate effort.

Happy hacking! 🚀
