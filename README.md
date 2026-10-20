# ROOTWISE

**Strong roots. Better software.**

ROOTWISE is a local-first Python command-line tool for repository inspection, readiness assessment, and digital preservation.

It helps developers understand what their software repositories contain, identify missing foundations, review evidence, preserve project files, and prepare for publication with better information.

ROOTWISE supports human judgment. It does not make release decisions, claim certainty it cannot justify, or silently take control of a developer's work.

**ROOTWISE://LOCAL**

*Repository care · Digital preservation · Developer control*

---

## Why ROOTWISE Exists

Software projects grow through experiments, decisions, documentation, and accumulated work. Before sharing or publishing a project, developers need a clearer understanding of what is present, what is missing, and what deserves attention.

ROOTWISE provides practical tools for inspecting repository foundations, evaluating known conditions, observing local Git changes, creating and verifying preservation snapshots, and preparing reviewable project handoffs.

Its approach is deliberate:

- Preserve intent and context where possible.
- Prefer evidence over assumptions.
- Make limitations visible.
- Protect existing files from unintended overwrites.
- Keep network access under operator control.
- Leave project changes and release decisions to the developer.

## Core Principles

- **Readiness before release:** Identify gaps before publication or deployment.
- **Evidence before assumptions:** Ground findings in the checks actually performed.
- **Honest uncertainty:** Distinguish observed conditions from unknowns and unperformed checks.
- **Preservation with care:** Avoid executing inspected project code during repository inspection.
- **Developer ownership:** Support decisions without taking authority away from the operator.
- **Local-first operation:** Keep work local unless an explicitly requested operation requires otherwise.
- **Safe file handling:** Apply safeguards to preservation operations and existing destinations.
- **Independent development:** Welcome contributions, forks, and projects built from ROOTWISE.

## Features

### Repository inspection

Inspect repository foundations and report findings supported by the checks performed.

### Health reports

Review repository conditions, evidence, recommendations, and limitations. Health reports provide useful information, not a guarantee of security, correctness, or release readiness.

### Snapshots and preservation

Create project snapshots, verify archives against manifests, and restore preserved files subject to safety checks.

Snapshots supplement an independent backup strategy. They do not replace one.

### Git observation

Observe local Git state and potential publication or synchronization risks without silently staging, committing, pushing, or publishing changes.

### Repository cloning

Clone a Git repository into a new destination. Remote cloning is subject to the configured network mode.

### Project trees

Browse project structure with configurable depth and optional inclusion of normally excluded entries. Tree browsing does not execute project code.

### Project handoffs

Prepare local Markdown handoffs containing task context, a bounded project tree, the README when available, and explicitly selected project files.

Handoffs are not transmitted automatically. Review the generated output before sharing it.

### CYBERGARDEN interface

CYBERGARDEN provides ROOTWISE's guided terminal experience and neon cyberpunk botanical identity.

ROOTWISE's core operations remain usable independently of a separate CYBERGARDEN installation.

---

## Requirements

- Python 3.10 or newer.
- Git for Git-based observation and repository cloning.
- A supported Python packaging environment for installation.

ROOTWISE has no third-party runtime dependencies. Its build configuration uses setuptools. Installing the package may require access to package repositories if the necessary build tools are not already available.

## Installation

### 1. Clone the repository

Replace `OWNER` with the GitHub account or organization hosting ROOTWISE.

```bash
git clone https://github.com/OWNER/ROOTWISE.git
cd ROOTWISE
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 3. Install ROOTWISE

```bash
python -m pip install .
```

### 4. Verify the installation

```bash
rootwise --help
```

For an editable development installation, use:

```bash
python -m pip install -e .
```

If you prefer to run the CLI directly from the source tree without installing the package, use:

```bash
python -m rootwise.cli --help
```

## Quick Start

Run ROOTWISE from the repository you want to inspect.

```bash
rootwise inspect .
rootwise health .
rootwise tree .
rootwise observe .
rootwise
```

The final command opens the interactive menu when no subcommand is provided.

Start with inspection and health reporting before deciding what preservation or workspace operations are appropriate for your project.

---

## Command Reference

ROOTWISE provides the following commands.

### `rootwise inspect`

Inspect repository foundations.

```bash
rootwise inspect
rootwise inspect /path/to/project
```

If no path is supplied, the current directory is used.

### `rootwise health`

Generate a repository health report.

```bash
rootwise health
rootwise health /path/to/project
```

The report describes the conditions ROOTWISE checks. It does not run your project's test suite or independently approve publication.

### `rootwise snapshot`

Create a preservation snapshot.

```bash
rootwise snapshot .
rootwise snapshot /path/to/project --output /path/to/snapshots
```

The output directory is optional. Consult the command's help for the exact artifact paths and output behavior.

### `rootwise verify`

Verify a snapshot archive against its manifest.

```bash
rootwise verify /path/to/archive.tar.gz /path/to/manifest.json
```

Use the actual archive and manifest paths produced by your snapshot operation.

### `rootwise restore`

Restore a snapshot into a destination.

```bash
rootwise restore /path/to/archive.tar.gz /path/to/manifest.json /path/to/destination
```

ROOTWISE applies restoration safety checks and requests confirmation before restoring by default. The `--yes` option skips the interactive confirmation.

Use `--yes` only when you understand the destination and the consequences of restoring into it.

### `rootwise observe`

Observe local Git state and potential publication or synchronization risks.

```bash
rootwise observe
rootwise observe /path/to/project
```

Observation does not itself synchronize or publish repository changes.

### `rootwise clone`

Clone a repository into a new destination.

```bash
rootwise clone REPOSITORY DESTINATION
```

For example, use a repository URL and a destination path appropriate to your environment.

Remote cloning is blocked when ROOTWISE is configured for offline operation. Local repository cloning remains available where supported.

### `rootwise tree`

Display a project tree.

```bash
rootwise tree .
rootwise tree . --max-depth 2
rootwise tree . --all
rootwise tree . --all --max-depth 3
```

Options:

- `--max-depth MAX_DEPTH`: Limit the displayed tree depth. The minimum depth is 1.
- `--all`: Include entries normally excluded from the default view.

Tree browsing does not execute project code.

### `rootwise handoff`

Prepare a local Markdown handoff for a specific task.

```bash
rootwise handoff . --task "Review publication readiness"
```

Select specific files when they are relevant:

```bash
rootwise handoff . \
  --task "Review publication readiness" \
  --file README.md \
  --file pyproject.toml
```

Additional options:

- `--output OUTPUT`: Write the handoff to a specified output file.
- `--max-tree-depth MAX_TREE_DEPTH`: Set the maximum project tree depth; the default is 3.
- `--file SELECTED_FILES`: Include an explicitly selected file. This option can be repeated.

The task description is required. By default, the generated Markdown is written to standard output. An explicitly specified output file must not already exist.

Handoffs are generated locally and are not transmitted automatically. File filters and safety checks reduce risk but cannot guarantee that every secret or sensitive detail will be excluded. Review the complete handoff before sharing it.

### `rootwise settings`

Manage local color and network preferences.

```bash
rootwise settings
rootwise settings --color off
rootwise settings --color on
rootwise settings --network offline
rootwise settings --network online
```

Options:

- `--color {on,off}`: Enable or disable ROOTWISE's configured color preference.
- `--network {offline,online}`: Set the network mode.

Offline mode is the default. Changing network mode does not initiate a network connection. Online mode permits explicitly invoked network operations; it does not authorize background activity.

Color output may also be affected by terminal capabilities and environment settings such as `NO_COLOR` and `TERM=dumb`.

### `rootwise menu`

Open the interactive menu.

```bash
rootwise menu
```

Running `rootwise` without a subcommand opens the menu as well.

The menu provides access to:

1. Repository inspection
2. Snapshot creation
3. Snapshot verification
4. Snapshot restoration
5. Git observation
6. Health reporting
7. Operator reference
8. Repository cloning
9. Project tree browsing
10. Project handoffs
11. Operator settings

Choose `q` to exit.

For the authoritative arguments and options of any command, run:

```bash
rootwise COMMAND --help
```

Replace `COMMAND` with the relevant subcommand.

---

## Network, Privacy, and Safety

ROOTWISE is designed for local-first operation and operator-directed workflows.

### Network controls

- Offline mode is the default.
- Remote cloning is blocked in offline mode.
- Local operations remain available where supported.
- Changing network mode does not establish a connection.
- ROOTWISE does not silently publish or synchronize changes.

### File preservation

- Snapshot verification checks an archive against its manifest.
- Restoration applies safety checks and requires confirmation by default.
- Existing destinations receive protective handling where specified by the relevant operation.
- Snapshots are not a substitute for independently maintained backups.

### Inspection boundaries

ROOTWISE reports what its checks support. It does not automatically prove that a repository is secure, that dependencies are trustworthy, or that software is ready for production.

### Handoff boundaries

Handoffs are local artifacts intended for review. Inspect them for credentials, personal information, proprietary material, and other content that should not be shared.

### Operator responsibility

Review findings, verify important assumptions, run the project's own tests, and assess security and release requirements independently. ROOTWISE is an aid to responsible development, not a replacement for it.

---

## Development and Testing

Clone the repository and enter its directory. Create and activate a virtual environment, then install the project in editable mode as described above.

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Compile the application and tests:

```bash
python -m compileall -q rootwise tests
```

These commands check Python compilation and execute the repository's unit tests. They do not, by themselves, establish security or release readiness.

When contributing, include relevant tests and documentation updates for behavioral changes.

## Authorship and Attribution

ROOTWISE was originally created by **Vera Lynn DeGraw (`VeraLynnDegraw`)**.

The original project history and applicable copyright notices should remain identifiable as ROOTWISE evolves.

Contributions, forks, and derivative projects are welcome. Developers may identify their own projects and claim authorship of their original contributions without claiming authorship of work they did not create.

When redistributing ROOTWISE or covered portions of it, retain the applicable original copyright notice and MIT License terms. Contributors and downstream maintainers are encouraged to document meaningful modifications and recognize the people responsible for them.

The MIT License does not require downstream projects to use ROOTWISE's name, imply endorsement, or adopt the original project's identity. This project encourages transparent attribution while respecting the freedom the license grants.

### Forks, Upstream Synchronization, and Independent Projects

Developers are welcome to fork ROOTWISE, synchronize their forks with the original repository, and build independent projects from their own branches.

A fork owner may identify themselves as the maintainer or creator of their own project and document their original contributions. This should not imply that they created the original ROOTWISE project or work authored by other contributors.

For GitHub-based development:

- **`origin`** should point to your own fork or repository.
- **`upstream`** may point to the original ROOTWISE repository when you want to track and incorporate its updates.
- Synchronization is a deliberate maintenance action. Review upstream changes and resolve conflicts before integrating them.
- Preserve applicable copyright notices and the MIT License when redistributing covered work.
- Update your own project's README, metadata, and contributor acknowledgments to accurately describe its identity, maintainers, and development history.

Example remote configuration for a fork:

```bash
git remote -v
git remote add upstream https://github.com/ORIGINAL-OWNER/ROOTWISE.git
git fetch upstream
```

Replace `ORIGINAL-OWNER` with the actual GitHub account or organization that hosts the original repository. If `upstream` is already configured, inspect it rather than adding it again.

To review the original project's branches and recent history before synchronizing, use:

```bash
git branch -a
git log --oneline --decorate -10
```

Choose an appropriate integration method for your branch and review the resulting changes before pushing. Synchronization does not transfer authorship, automatically resolve licensing questions, or guarantee compatibility.

ROOTWISE welcomes independent evolution. Preserve the project's provenance while allowing each fork to establish its own identity.

**Preserve the origin. Respect the contributions. Leave room for others to grow.**

## License

ROOTWISE is released under the MIT License. See [`LICENSE`](LICENSE) for the complete license text and applicable copyright notice.

---

**ROOTWISE**

*Strong roots. Better software.*
