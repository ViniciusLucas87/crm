# Deployment Snapshot — Pre-Cutover
# Timestamp: 2026-08-01 10:45 PT
# Purpose: Record current state before any deployment changes

## Git Status
- **Repository**: NOT INITIALIZED
- **No commits, no branches, no remotes**

## Monorepo Structure
```
CRM System/
├── apps/
│   ├── api/          # FastAPI backend (Python 3.12, Docker)
│   ├── marketing/     # Next.js 15 public website (NO Dockerfile)
│   ├── web/           # Next.js CRM frontend (Docker, npm)
│   └── worker/        # Celery worker (Python 3.12, Docker)
├── packages/
│   └── contracts/     # Shared TypeScript contracts (@pns/contracts)
├── docker-compose.yml # Local dev: postgres, redis, api, worker, worker-beat
└── pnpm-workspace.yaml
```

## Existing Dockerfiles
| App | Dockerfile | Build tool | Start command |
|---|---|---|---|
| api | apps/api/Dockerfile | pip install | uvicorn (in Dockerfile) |
| web | apps/web/Dockerfile | npm build | next start |
| worker | apps/worker/Dockerfile | pip install | celery worker |
| **marketing** | **NONE** | **N/A** | **N/A** |

## Package Manager
- **Root**: pnpm 9.12.2 (workspace)
- **web (CRM)**: npm (separate package-lock.json)
- **marketing**: pnpm 9.12.2
- **api/worker**: pip (Python 3.12)

## Current Production DNS (CanSpace — from earlier audit)
### pacificnorthsystems.com
| Host | Type | Value | TTL | Purpose | Change? |
|---|---|---|---|---|---|
| @ | A | 31.43.161.6 | 14400 | Web hosting (old) | YES → Railway |
| @ | A | 31.43.160.6 | 14400 | Web hosting (old) | YES → Railway |
| www | CNAME | sites.framer.app. | 14400 | Framer website | YES → Railway |
| @ | MX 10 | mx.zohocloud.ca. | 14400 | Zoho email | NO |
| @ | MX 20 | mx2.zohocloud.ca. | 14400 | Zoho email | NO |
| @ | MX 50 | mx3.zohocloud.ca. | 14400 | Zoho email | NO |
| @ | NS | dns1.canspace.ca. | 86400 | Nameserver | NO |
| @ | NS | dns2.canspace.ca. | 86400 | Nameserver | NO |
| @ | TXT | zoho-verification=... | 14400 | Zoho verification | NO |
| @ | TXT | v=spf1 include:zohocloud.ca ~all | 14400 | SPF | NO |
| @ | TXT | google-site-verification=... | 14400 | Google Search Console | NO |
| ftp | CNAME | pacificnorthsystems.com. | 14400 | FTP alias | YES → remove or Railway |
| mail | CNAME | pacificnorthsystems.com. | 14400 | Mail alias | NO |
| zmail._domainkey | TXT | v=DKIM1; k=rsa; p=... | 14400 | DKIM | NO |

### pacificnorthsystems.ca
(Similar structure, domain-only registration)

## Railway Status
- **No Railway project found**
- **No railway.json or nixpacks.toml**
- **No existing Railway services**
- **Must create from scratch**

## Framer Status
- **www CNAME → sites.framer.app** (ACTIVE)
- **Framer project exists and is the current live site**
- **Must NOT delete or cancel**
