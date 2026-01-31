---
name: generating-prd-md-from-userstory-md
description: Transforms UserStory.md into PRD.md by extracting features and converting user stories into functional requirements.
model: haiku
allowed-tools: Read, Write
---

# PRD Generation from User Story

Converts `docs/UserStory.md` into `docs/PRD.md` with structured functional requirements.

## Purpose

Bridges the gap between user-focused stories and implementation-ready requirements by converting narrative descriptions into technical requirements.

## Workflow

1. **Read inputs**
   - Read `ralph/docs/templates/prd.md.template` - follow its structure exactly
   - Read `docs/UserStory.md` - parse all sections: Problem, Users, Value, Stories, Criteria, Constraints

2. **Extract and convert**
   - User stories → Functional requirements (WHAT the system must do)
   - Success criteria + Constraints → Non-functional requirements (HOW it performs)
   - Group by functional area (CLI, API, Storage, etc.)

3. **Generate PRD.md**
   - Follow template structure and PARSER REQUIREMENT comments
   - Project Overview: Combine problem statement + value proposition
   - Functional Requirements: Organized by feature area
   - Non-Functional Requirements: Performance, usability, platform
   - Story Breakdown: Include `(depends: STORY-XXX)` when story B requires story A to complete first
   - Out of Scope: Copy from UserStory.md

4. **Validate against template**
   - Verify output matches `ralph/docs/templates/prd.md.template` structure
   - Check PARSER REQUIREMENT elements are present (headings, checkboxes, story format)

5. **Save**
   - Backup existing PRD.md as `PRD.md.bak` if overwriting
   - Write to `docs/PRD.md`
   - Suggest: `make ralph_prd_json`

## Conversion Examples

**User Story → Functional Requirement**:

- "As a developer, I want to add tasks from CLI" → "CLI command: `task add "description"`"

**Success Criteria → Non-Functional**:

- "Operations in < 5 seconds" → "Performance: All CLI operations complete in < 5 seconds"

**Constraints → Non-Functional**:

- "Must work on Linux, macOS, Windows" → "Platform Support: Cross-platform compatibility"

## Usage

```bash
make ralph_prd_md
```

## Next Steps

```bash
make ralph_prd_json   # Generate prd.json from PRD.md
make ralph_run        # Start Ralph loop
```
