# Project Instructions for Claude Code

## Installed Plugins & Tools

### everything-claude-code Plugin
**Status:** ✅ Fully Installed (Full Profile)
**Source:** https://github.com/affaan-m/everything-claude-code
**Install Date:** 2026-04-21

**Installation Details:**
- Rules installed: `~/.claude/rules/` (all languages + common)
- Agents installed: `~/.claude/agents/` (48 specialized agents)
- Skills available: 183+ skills
- Profile: `full` (includes all modules)

**Key Modules Installed:**
- Core: rules-core, agents-core, commands-core, hooks-runtime
- Languages: Python, TypeScript, Go, Rust, Swift, Java, Kotlin, C++, C#, Dart, PHP, Perl
- Frameworks: FastAPI, Django, Laravel, Spring Boot, NestJS, Next.js
- Workflows: quality, security, testing, deployment
- Domains: database, orchestration, supply-chain, document-processing
- APIs: research-apis, social-distribution, media-generation

**Usage:**
```bash
# Use namespaced form for plugin-installed skills
/everything-claude-code:plan "Add user authentication"
/everything-claude-code:code-review
/everything-claude-code:python-review
/everything-claude-code:tdd

# List all available skills
/plugin list everything-claude-code@everything-claude-code
```

**Available Specialized Agents:**
- `architect` - Software architecture and system design
- `code-reviewer` - Expert code review
- `python-review` - Python-specific code review
- `build-error-resolver` - Build and compilation error fixing
- `database-reviewer` - Database query optimization and schema design
- `security-reviewer` - Security audit and vulnerability detection
- `docs-lookup` - Documentation retrieval via Context7
- `e2e-runner` - End-to-end testing with Playwright
- And 40+ more specialized agents...

### gstack
**Location:** `~/.claude/skills/gstack`
**Source:** https://github.com/garrytan/gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Available gstack skills:
- `/office-hours` - YC Office Hours mode for startup guidance
- `/plan-ceo-review` - CEO/founder-mode plan review
- `/plan-eng-review` - Engineering manager-mode plan review
- `/plan-design-review` - Designer's eye plan review
- `/design-consultation` - Design consultation and research
- `/design-shotgun` - Generate multiple AI design variants
- `/design-html` - Generate production-quality HTML/CSS
- `/review` - Pre-landing PR review
- `/ship` - Ship workflow with tests and version bump
- `/land-and-deploy` - Land and deploy workflow
- `/canary` - Post-deploy canary monitoring
- `/benchmark` - Performance regression detection
- `/browse` - Fast headless browser for QA testing
- `/connect-chrome` - Launch GStack Browser
- `/qa` - Systematically QA test and fix bugs
- `/qa-only` - Report-only QA testing
- `/design-review` - Designer's eye QA
- `/setup-browser-cookies` - Import cookies from Chromium
- `/setup-deploy` - Configure deployment settings
- `/retro` - Weekly engineering retrospective
- `/investigate` - Systematic debugging with root cause investigation
- `/document-release` - Post-ship documentation update
- `/codex` - OpenAI Codex CLI wrapper
- `/cso` - Chief Security Officer mode security audit
- `/autoplan` - Auto-review pipeline
- `/plan-devex-review` - Developer experience plan review
- `/devex-review` - Live developer experience audit
- `/careful` - Safety guardrails for destructive commands
- `/freeze` - Restrict file edits to specific directory
- `/guard` - Full safety mode
- `/unfreeze` - Clear freeze boundary
- `/gstack-upgrade` - Upgrade gstack to latest version
- `/learn` - Manage project learnings

### Get Shit Done (GSD)
**Location:** `~/.claude/skills/get-shit-done`
**Source:** https://github.com/gsd-build/get-shit-done

A lightweight meta-prompting, context engineering, and spec-driven development system. Solves context rot and quality degradation.

Key features:
- Spec-driven development with quality gates
- Schema drift detection
- Security enforcement with threat models
- Scope reduction detection
- Spiking & sketching workflows
- Agent size-budget enforcement

### Awesome Claude Skills (Composio)
**Location:** `~/.claude/skills/awesome-claude-skills`
**Source:** https://github.com/ComposioHQ/awesome-claude-skills

Curated collection of practical Claude Skills for productivity. Includes skills for:
- Document Processing
- Development & Code Tools
- Data & Analysis
- Business & Marketing
- Communication & Writing
- Creative & Media
- Productivity & Organization
- Collaboration & Project Management
- Security & Systems
- App Automation (500+ apps via Composio)

### Antigravity Awesome Skills
**Location:** `~/.claude/skills/antigravity-awesome-skills`
**Source:** https://github.com/sickn33/antigravity-awesome-skills

Massive library of 1,431+ agentic skills for Claude Code and other AI coding assistants. Includes:
- Installable skill library with bundles and workflows
- Skills across development, testing, security, infrastructure, product, and marketing
- Role-based bundles for faster onboarding
- Workflow-driven execution for planning, coding, debugging, testing

### NotebookLM MCP CLI
**Location:** `~/.claude/skills/notebooklm-mcp-cli`
**Source:** https://github.com/jacob-bd/notebooklm-mcp-cli

Programmatic access to Google NotebookLM via CLI and MCP server.

CLI commands available via `nlm`:
- `nlm notebook list/create` - Manage notebooks
- `nlm source add` - Add sources (URL, text, Drive, files)
- `nlm notebook query` - Query notebooks
- `nlm studio create` - Create audio/video content
- `nlm slides revise` - Revise slide decks
- `nlm download` - Download artifacts
- `nlm research start` - Web/Drive research
- `nlm share` - Share notebooks
- `nlm batch` - Batch operations
- `nlm pipeline` - Multi-step workflows
- `nlm setup add` - Configure AI tools integration

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health
