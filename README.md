# ROOTWISE

**Strong roots. Better software.**

ROOTWISE helps developers understand the condition of a software repository before sharing, publishing, or preparing it for deployment.

It inspects repository foundations, identifies missing essentials, records evidence, and explains what needs attention and what remains uncertain. Its goal is not to make release decisions for developers, but to help them make those decisions with better information.

**ROOTWISE://LOCAL**

*Repository care · Digital preservation · Developer control*

## Why ROOTWISE Exists

Software projects grow through experiments, decisions, documentation, and accumulated work. Before sharing a project, it helps to understand what is present, what is missing, and what might need care.

ROOTWISE provides a local workspace for repository inspection and preservation. It favors clear evidence over assumptions, cautious operations over destructive shortcuts, and developer choice over automatic decisions.

## Core Principles

- **Readiness before release:** Identify gaps before a project is published or deployed.
- **Evidence before assumptions:** Explain findings and provide reasons for recommendations.
- **Honest uncertainty:** Distinguish performed checks from unknowns and limitations.
- **Preservation by default:** Inspect projects without modifying their contents or executing inspected code.
- **Platform awareness:** Account for different hosting and deployment environments without treating their requirements as interchangeable.
- **Developer ownership:** Recommend improvements while leaving decisions and changes to the developer.
- **Local-first operation:** Keep repository inspection and preservation local unless the developer explicitly chooses otherwise.

## Features

### Repository Inspection

Examine repository structure and essential project files. Identify missing documentation, unexpected file types, empty files, and other findings supported by the checks performed.

### Repository Health Reports

Summarize inspection findings and provide actionable recommendations. Reports distinguish observed conditions from checks that have not been performed.

### Snapshots and Preservation

Create repository snapshots, verify snapshot integrity, and restore preserved files with safeguards against unsafe paths and unintended overwrites.

Snapshots are preservation tools, not substitutes for independent backups or a complete disaster-recovery strategy.

### Git Synchronization Observation

Observe repository status and classify potential synchronization candidates. ROOTWISE reports changes for review rather than silently staging or publishing them.

### Operator Guidance

Use a guided terminal menu to access repository scans, health reports, snapshot operations, synchronization observation, and reference information.

## The ROOTWISE Terminal

ROOTWISE uses a neon cyberpunk botanical presentation style designed to remain readable and practical.

The local terminal interface includes:

- A consistent `ROOTWISE://LOCAL` identity banner.
- Grouped menu options for repository care, preservation, change observation, and guidance.
- Framed menus with aligned borders and bounded long labels.
- Terminal color detection and plain-text fallbacks.
- Clear session-exit messaging that reinforces developer control.

The visual design supports the work rather than hiding it. Findings, limitations, and operator choices remain the focus.

## Architecture

ROOTWISE is a standalone Python command-line application.

Its responsibilities are separated into two broad areas:

- **Core operations:** Repository inspection, health reporting, snapshots, restoration safeguards, and Git synchronization observation.
- **Terminal presentation:** Branding, colors, layout, menu frames, prompts, and display formatting.

The current terminal presentation implementation lives locally in `rootwise/cybergarden.py`. ROOTWISE does not require the separate CYBERGARDEN project to be installed.

The longer-term direction is to develop reusable presentation capabilities and configurable settings without coupling ROOTWISE's core behavior to a particular interface library.

## Publishing Is Not Deployment

ROOTWISE treats source-code publication and production deployment as separate readiness stages.

A project may be ready to publish on GitHub without being ready for production use. Hosting requirements, deployment configuration, operational security, and runtime behavior require appropriate checks for their specific context.

A ROOTWISE report is evidence to support a decision, not a guarantee that a repository is safe, complete, secure, or production-ready.

## Safety and Design Commitments

- Read-only inspection by default.
- No execution of inspected project code as part of repository inspection.
- Evidence-backed findings and clearly stated limitations.
- No fabricated universal readiness score.
- Safeguards around snapshot verification and restoration.
- No silent staging or publishing of Git changes.
- Developer-controlled changes and release decisions.
- Local operation without mandatory runtime dependencies.

## Installation and Usage

ROOTWISE requires Python 3.10 or newer.

From the repository root, you can run the application with:

```bash
python -m rootwise.cli
```

When installed in an environment, the `rootwise` command is available through the project's configured console entry point.

The terminal menu guides you through the available operations. Review findings and recommendations before making changes to your repository.

## Development and Testing

ROOTWISE is under active development. Supported checks and workflows will expand incrementally, with automated tests protecting existing behavior.

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The current tests cover repository inspection, health reports, snapshot creation and verification, restoration safeguards, synchronization observation, and terminal presentation behavior.

## Project Philosophy

**Inspect honestly. Preserve carefully. Grow deliberately.**

ROOTWISE exists to help developers care for the foundations of their projects while keeping ownership, context, and final decisions in human hands.
