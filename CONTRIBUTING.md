# Contributing

## Branch naming

Format: `<type>/<short-kebab-case-description>`

| Prefix      | Use for                                                |
|-------------|---------------------------------------------------------|
| `feature/`  | New functionality                                        |
| `fix/`      | Bug fixes                                                |
| `refactor/` | Restructuring code without changing behavior             |
| `test/`     | Test-only changes                                        |
| `docs/`     | Documentation                                            |
| `chore/`    | Maintenance — env vars, dependency bumps, config, Docker/packaging |
| `ci/`       | Changes to `.github/workflows/`                          |

Keep the branch prefix and commit message type the same (e.g. a `chore/`
branch gets `chore:` commits) — makes `git branch -a` and `git log` tell
the same story.

## CI trigger (`.github/workflows/test.yml`)

```yaml
on:
  push:
```

Runs on every push to every branch.

## Standard workflow

```bash
# 1. Start from a clean, up-to-date main
git checkout main
git pull origin main

# 2. Branch
git checkout -b chore/example-change

# 3. Work, then review before staging
git status
git diff

# 4. Stage and commit
git add <files>
git commit -m "chore: example change"

# 5. Push (first push on a new branch needs -u; after that, plain `git push`)
git push -u origin chore/example-change
```

Then on GitHub: open the PR (base `main`) → wait for the `test` check to
pass → Squash and merge → Delete branch.

Clean up locally. Note: after a squash merge, `git branch -d` will often
fail with "not fully merged" — expected, since squash creates a new commit
SHA that doesn't match anything on your local branch. Since the merge is
already confirmed on GitHub, it's safe to fall back to force delete:

```bash
git checkout main
git pull origin main
git branch -d chore/example-change || git branch -D chore/example-change
```

## Command reference

- `git checkout <branch>` — switch branches (moves HEAD, updates working directory files)
- `git checkout -b <branch>` — create + switch to a new branch in one step
- `git push -u origin <branch>` — push and link local branch to its remote counterpart (only needed once per branch)
- `git branch -d <branch>` — delete a local branch, but only if git can verify it's fully merged (see squash-merge note above)
- `git branch -D <branch>` — force delete regardless of merge status; use only once independently confirmed (e.g. on GitHub) that the branch's work is safely merged
