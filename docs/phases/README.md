# Research Phases Documentation

| Field | Value |
| :--- | :--- |
| **Document Type** | Documentation Subsystem Index |
| **Status** | Active Index |
| **Owner** | Research Lead / AI Agent |
| **Scope** | Research Phases |
| **Created** | 2026-09-06T21:05:00+07:00 |
| **Last Updated** | 2026-09-06T21:05:00+07:00 |
| **Reference** | [docs/README.md](../README.md), [agents/templates/PHASE_DOC_TEMPLATE.md](../../agents/templates/PHASE_DOC_TEMPLATE.md) |

---

## Purpose & Conventions

This directory houses phase specification documents that define the goals, architectural decisions, and acceptance criteria for each major milestone of the project.

### Creating a New Phase Document

1. Copy [agents/templates/PHASE_DOC_TEMPLATE.md](../../agents/templates/PHASE_DOC_TEMPLATE.md) into this directory.
2. Name the file with a zero-padded prefix and descriptive snake/kebab case:
   - `01_DATA_PREP.md`
   - `02_MODEL_BASELINE.md`
   - `03_TRAINING_PIPELINE.md`
   - `04_EXPERIMENTS_ANALYSIS.md`
3. Fill out the 7-field header with accurate ISO 8601 timestamps.
4. Link the phase in [docs/OVERVIEW.md](../OVERVIEW.md).
