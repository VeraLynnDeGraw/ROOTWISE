# ROOTWISE

**Strong roots. Better software.**

ROOTWISE helps developers prepare software projects for publication, collaboration, and deployment by inspecting repository foundations, identifying missing essentials, and reporting evidence-based findings.

It helps developers understand what is ready, what needs attention, and what remains uncertain before sharing a project on GitHub or other hosting platforms.

## Core Principles

- **Readiness before release:** Identify gaps before a project is published or deployed.
- **Evidence before assumptions:** Explain findings and provide reasons for recommendations.
- **Honest uncertainty:** Distinguish verified checks from unknowns and limitations.
- **Preservation by default:** Inspect projects without modifying files or executing inspected code.
- **Platform awareness:** Support different hosting and deployment environments without assuming their requirements are identical.
- **Developer ownership:** Recommend improvements while leaving decisions and changes to the developer.
- **Local-first operation:** Keep inspection local unless the developer explicitly chooses otherwise.

## What ROOTWISE Checks

- Project documentation and repository structure.
- License and essential project files.
- Tests, dependency manifests, and build configuration.
- Git status and publishing preparation.
- Security documentation and potential configuration risks.
- Hosting and deployment prerequisites.

## Publishing Is Not Deployment

ROOTWISE treats source-code publication and production deployment as separate readiness stages. A project may be ready to publish on GitHub without being ready for production use.

## Design Commitments

- Read-only inspection by default.
- No execution of inspected project code.
- Evidence-backed findings and clearly stated limitations.
- No fabricated universal readiness score.
- Developer-controlled changes and release decisions.

## Project Status

ROOTWISE is under development. Its checks and supported platforms will expand incrementally, with automated tests protecting existing behavior.
