# Specialist Agent Map

This engine uses a small role router rather than pretending every upstream agent is already running. Each task is assigned a role prompt, the CEO creates a plan, and QA independently reviews the output.

The upstream [Agency Agents](https://github.com/msitarzewski/agency-agents) repository provides specialist instruction files. This project currently links to relevant upstream directories/files; it does not claim to load all 230+ agents at runtime.

| Runtime role | Responsibility | Upstream reference |
|---|---|---|
| CEO / Orchestrator | Plan tasks and acceptance checks | [Multi-agent systems](https://github.com/msitarzewski/agency-agents/tree/main/engineering) |
| Researcher | Market/customer evidence, assumptions | [Marketing agents](https://github.com/msitarzewski/agency-agents/tree/main/marketing) |
| Sales strategist | Lead qualification and outreach drafts | [Sales agents](https://github.com/msitarzewski/agency-agents/tree/main/sales) |
| Product manager | Scope and acceptance criteria | [Product manager](https://github.com/msitarzewski/agency-agents/blob/main/product/product-manager.md) |
| Builder | Generate code/artifact files | [Engineering agents](https://github.com/msitarzewski/agency-agents/tree/main/engineering) |
| Delivery specialist | Reports, proposals and other deliverables | [Project management](https://github.com/msitarzewski/agency-agents/tree/main/project-management) |
| QA reviewer | Independent review and defect detection | [Code reviewer](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-code-reviewer.md) |

## Important implementation detail

The runtime role router chooses one specialist based on the task title and description. It does not yet delegate to multiple parallel agents or dynamically import upstream prompt files. That is a future milestone, not a completed capability.

Upstream content is MIT-licensed. If files are copied into this repository later, retain the upstream copyright and permission notice as required by the license.
