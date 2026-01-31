---
name: commit-staged-with-message
description: Generate commit message for staged changes, pause for approval, then commit. Stage files first with `git add`, then run this skill.
model: haiku
argument-hint: (no arguments needed)
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

# Commit staged with Generated Message

## Git Context

- Staged files: !`git diff --staged --name-only`
- Diff stats: !`git diff --staged --stat`
- Recent style: !`git log --oneline -5`

## Step 1: Analyze Staged Changes

Review the pre-loaded context above. Use additional tools as needed:

- `git diff --staged` - Review detailed staged changes

## Step 2: Generate Commit Message

Use the Read tool to check `.gitmessage` for commit message format and syntax.

## Step 3: Pause for Approval

**Please review the commit message.**

- **Approve**: "yes", "y", "commit", "go ahead"
- **Edit**: Provide your preferred message
- **Cancel**: "no", "cancel", "stop"

## Step 4: Commit

Once approved:

- `git commit -m "[message]"` - Commit staged changes with approved message
- `git status` - Verify success
