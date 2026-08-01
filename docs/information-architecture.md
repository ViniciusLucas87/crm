# Pacific North Systems Sales OS — Information Architecture

**Version:** 1.0 | **Date:** 2026-07-19 | **Blueprint for Sprint 2+**

---

## Module Hierarchy

```
Sales OS
├── Command Center (Dashboard)
│   ├── Morning Briefing
│   ├── Key Metrics (KPIs)
│   ├── Today's Priorities
│   ├── Recent Activity
│   ├── AI Insights
│   └── Upcoming Meetings
│
├── Sales
│   ├── Companies          ← Sprint 1 ✅
│   │   └── Company Detail ← Sprint 2+
│   ├── Contacts           ← Sprint 2
│   ├── Opportunities      ← Sprint 2
│   │   └── Pipeline View
│   ├── Activities         ← Sprint 2
│   │   ├── Calls
│   │   ├── Emails
│   │   └── Meetings
│   └── Tasks              ← Sprint 2
│
├── Delivery
│   ├── Projects           ← Sprint 4
│   └── Documents          ← Sprint 4
│
├── AI
│   ├── Research           ← Sprint 3
│   │   ├── Company Intel
│   │   └── Website Analysis
│   ├── Proposals          ← Sprint 3
│   │   └── AI Drafts
│   └── Automations        ← Sprint 3+
│
└── Insights
    ├── Reports            ← Sprint 5
    └── Settings
```

---

## Core Entities

| Entity | Sprint | Relationships |
|--------|--------|---------------|
| **Organization** | 1 | has many Users, Companies |
| **User** | 1 | belongs to Organization |
| **Company** | 1 | has many Contacts, Opportunities, Activities, Tasks |
| **Contact** | 2 | belongs to Company |
| **Opportunity** | 2 | belongs to Company, has Pipeline Stage |
| **Activity** | 2 | belongs to Company/Contact (call, email, meeting) |
| **Task** | 2 | belongs to Company/Contact, has assignee |
| **Project** | 4 | belongs to Company |
| **Document** | 4 | belongs to Company/Project |
| **Proposal** | 3 | belongs to Company, AI-generated |

---

## Future AI Integration Points

| Module | AI Capability | Sprint |
|--------|--------------|--------|
| Companies | AI company summary + website analysis | 3 |
| Companies | Pain-point detection + tech stack inference | 3 |
| Proposals | AI draft generation + pricing suggestions | 3 |
| Activities | Meeting notes + action item extraction | 3 |
| Dashboard | AI-generated daily briefing | 5 |
| Reports | Win/loss analysis + lead source analytics | 5 |

---

## Future MCP Integration Points

The `apps/api/app/ai/` module is structured for MCP:

| Submodule | MCP Role |
|-----------|----------|
| `ai/tools/` | Tool definitions exposed to AI agents |
| `ai/prompts/` | Prompt templates for each AI capability |
| `ai/providers/` | LLM provider adapters (OpenAI, Anthropic) |
| `ai/workflows/` | Multi-step AI workflow compositions |
| `ai/services/` | AI use-case orchestration |

---

## Navigation Principles

- **Command Center** — Always first. The morning briefing.
- **Sales** — Core CRM workflows (Companies → Contacts → Pipeline).
- **Delivery** — Post-sale project delivery.
- **AI** — Intelligence and automation, not a replacement.
- **Insights** — Reports and configuration.

Future modules (grayed out in nav) are visible but disabled — communicating the roadmap without broken links.
