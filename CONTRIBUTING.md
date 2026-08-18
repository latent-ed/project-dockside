# How we work

## Branches

`main` is protected. No direct commits, no force pushes.

    feature/<initials>-<short-description>
    fix/<initials>-<short-description>

For example: `feature/dr-silver-pivot`

## Pull requests

Every change reaches `main` through a pull request, approved by the instructor.

- Your teammates cannot unblock a merge, but review each other's work anyway —
  it is assessed, and it catches things before the instructor sees them
- Keep PRs small and single-purpose. A 400-line PR gets rubber-stamped,
  and a rubber-stamped PR is not a review
- Resolve all conversations before merging
- Delete your branch after merge

## Reviewing

Reviewing is not a formality. Read it properly and ask a question if
something is unclear. Your review comments are assessed.

## Secrets

Never commit `.env`. If you add a variable, add it to `.env.example` in the
same PR with an empty value.

If you push a credential by accident, tell the instructor immediately.
Rotating a key takes minutes. Finding it later in the history does not.
