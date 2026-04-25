---
title: Contributing
description: Fork, branch, pull request, documentation-sync, and submodule submission
  rules for contributors.
---

## Core Rules

- fork first, then develop in your own repository
- use Pull Requests by default
- one branch should focus on one task
- one PR should solve one clear problem

## First Collaboration Cycle

Each new contributor should complete at least one full cycle:

```text
fork -> clone -> branch -> commit -> push -> Pull Request -> review -> merge
```

Before that cycle is complete, direct write access to the main repository should not be assumed.

## Branch Naming

Suggested names:

- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`

Do not work directly on `master`.

## Commit Message Style

Recommended prefixes:

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `chore:`

Examples:

```text
docs: update developer onboarding guide
fix: unify point lio published frame ids
```

## Pull Request Expectations

A good PR description should state:

1. what changed
2. why it changed
3. how it was verified
4. whether topics, TF, parameters, launch files, or docs were affected

## Documentation Sync

Docs usually need updating when you:

- add or remove a module
- change launch commands
- move parameter files
- rename topics, TF frames, or frame IDs
- change submodule URLs or repository structure

## Submodule Workflow

If you modify a submodule:

1. fork the submodule repository
2. make and submit the submodule PR first
3. once that change is stable, update the submodule pointer in the main repository
4. then submit the main-repo PR

Avoid pointing the main repository at a submodule commit that exists only in a personal fork unless the team explicitly agreed on it.

## Pre-Merge Checklist

- only task-related files are included
- no generated files from `build/`, `install/`, or `log/` are included
- no unrelated submodule pointer changed accidentally
- the work is on your own branch
- required documentation updates are included

## Related Pages

- [Development Notes](development.md)
- [Quick Start](../home/quick_start.md)
- [Updates & Migration](migration_notes.md)
