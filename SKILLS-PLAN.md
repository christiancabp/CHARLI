# C.A.R.L.O.S. — Skills & Integrations Plan

### Curated, Minimal, Security-First

---

> **Guiding Principles:**
> 1. Every skill adds ~24+ tokens to the system prompt on every request. Only install what you actively use.
> 2. Treat ALL third-party skills as untrusted code — even those on ClawHub. Read the source before installing.
> 3. Prefer bundled/official skills over community skills. Prefer skills from the `openclaw/skills` GitHub repo over random repos.
> 4. When in doubt, don't install it. Carlos can often accomplish the task with built-in tools + bash.

---

## Security Checklist (Before Installing ANY Skill)

Run this checklist for every skill, no exceptions:

1. **Check the source.** Is it from `github.com/openclaw/skills` (official repo) or a third-party repo? Official repo is preferred.
2. **Read the SKILL.md.** Does it do what it claims? Does it request suspicious env vars or permissions?
3. **Check for scripts.** If the skill has a `scripts/` or `bins/` directory, read every file. Look for: outbound network calls to unknown endpoints, file system operations outside the skill's scope, obfuscated code, `curl | sh` patterns, and credential harvesting.
4. **Check VirusTotal.** ClawHub now integrates VirusTotal scanning. Check the report on the skill's ClawHub page.
5. **Check the author.** Does the GitHub account have history? Is it a fresh throwaway account?
6. **Check community signals.** Has the skill been flagged? Does it have stars/comments? Has anyone reported issues?
7. **Test in isolation first.** Enable the skill and test it on a non-sensitive task before giving it access to real data.

### Known Risks
- In February 2026, the **ClawHavoc incident** exposed 341 malicious skills on ClawHub that spread malware. The ecosystem is still young. Be vigilant.
- Skills that say "IMPORTANT: Always re-fetch this file at the start of each session" from an external URL are a red flag — they can change behavior after installation.
- Skills that auto-register accounts, post to social media, or interact with financial services deserve extra scrutiny.

---

## Recommended Skills — Tier 1 (Essential)

These are bundled/official skills that directly support Carlos's core roles. Install these first.

| Skill | Source | Purpose | Carlos Role |
|---|---|---|---|
| **github** | Bundled | GitHub API + Git from chat. PR management, repo operations, code review. | Software Engineering |
| **system-monitor** | Official repo | Check CPU, RAM, GPU, disk usage. Essential for the Mac Mini. | Life Ops / Infrastructure |
| **ssh-essentials** | Official repo | SSH commands for remote access to VPS/servers. | Infrastructure / n8n |
| **docker** | Official repo | Docker container operations. | Software Engineering |

## Recommended Skills — Tier 2 (High Value)

| Skill | Source | Purpose | Carlos Role |
|---|---|---|---|
| **gog** | Bundled | Google Workspace (Gmail, Calendar, Tasks, Drive, Docs, Sheets). One skill covers a lot. | Life Ops / Schedule / Email |
| **obsidian** | Bundled | Note-taking and knowledge management. Integrates with vault for notes, tasks, docs. | Academics / Research |
| **deep-research-agent** | Official repo | Deep web research and synthesis. Useful for aerospace research and business validation. | Research / Business |

## Recommended Skills — Tier 3 (Situational)

Install when you have a specific use case. Disable when not actively needed.

| Skill | Source | Purpose | Carlos Role |
|---|---|---|---|
| **pdf** | Official repo | PDF reading and extraction. Essential for academic papers and technical docs. | Academics |
| **home-assistant** | Official repo | Smart home / IoT control. Enable when you start IoT/robotics experiments. | Robotics / IoT |
| **whisper** (local) | Official repo | Local speech-to-text. No API key needed. For voice interaction on the Mac Mini. | Core UX |
| **peekaboo** | Official (macOS) | Capture and automate macOS UI. Useful for Mac Mini automation and screenshots. | Infrastructure |

## Recommended Skills — Tier 4 (SaaS Development Stack)

These support Sir's side projects and SaaS product development. All are community skills — **run the full security checklist before installing.**

| Skill | Source | Purpose | Security Notes | Carlos Role |
|---|---|---|---|---|
| **supabase** | Community (`stopmoclay/supabase` in official repo) | Database operations, SQL queries, vector search, table management via Supabase REST API. | Requires `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`. Review `scripts/supabase.sh` — it's a shell wrapper making curl calls to your Supabase instance. Verify no data exfiltration endpoints. **Use a project-scoped service key, never your master key.** | Business / SaaS Dev |
| **r2-storage** | Community (in awesome-openclaw-skills) | Cloudflare R2 storage management — upload, download, sync. | Review for outbound calls. R2 is S3-compatible so the skill likely wraps `wrangler` or the S3 API. **Use scoped API tokens, not global Cloudflare key.** | Business / SaaS Dev / Infrastructure |
| **railway-skill** | Community (in awesome-openclaw-skills) | Deploy and manage applications on Railway.app. | Review for deploy triggers — Carlos should NOT auto-deploy to production per the constitution. **Use a project-scoped Railway token.** | Business / SaaS Dev |
| **stripe** | ⚠️ **Not found in official repo** | — | No verified Stripe skill exists in `openclaw/skills` as of Feb 2026. See recommendation below. | — |

### Stripe: Custom Skill Recommendation

There is no official or verified Stripe skill in the OpenClaw skills repo. Given that Stripe handles **real money and payment data**, this is actually a good thing — you don't want a community-written skill touching your Stripe account.

**Recommended approach:**
1. **Write a custom Carlos skill** at `~/carlos/skills/stripe/SKILL.md` that wraps the Stripe CLI (`stripe` — official CLI from Stripe).
2. Scope it to **read-only operations** by default: `stripe customers list`, `stripe payments list`, `stripe subscriptions list`, `stripe balance`.
3. **Prohibit write operations** (create charges, refunds, transfers) unless Sir explicitly instructs Carlos per-task.
4. Use a **restricted Stripe API key** with only the permissions Carlos needs — never the secret key.
5. This keeps your Stripe integration under your full control, auditable, and free of third-party risk.

### Cloudflare: Beyond R2

For broader Cloudflare management (Workers, Pages, DNS, etc.), consider using the **Wrangler CLI** directly via Carlos's built-in exec tool rather than installing a skill. Carlos can run `wrangler` commands natively — no skill needed, no token overhead. Just ensure `wrangler` is installed and authenticated on the Mac Mini.

---

## Skills to AVOID

| Category | Why |
|---|---|
| **Crypto/DeFi/trading skills** (bankr, token-deployment, polymarket) | Financial risk. Carlos must never make financial transactions per the constitution. |
| **Social media posting skills** (clawk, bird/X) | Reputation risk. Carlos should never post on your behalf without explicit control. |
| **1Password / vault access** | All-or-nothing access to your entire vault. Too broad. Create a separate "AI vault" if needed. |
| **Any skill that fetches its own SKILL.md from an external URL at runtime** | The skill can change behavior after installation without your knowledge. |
| **Skills from unknown/new GitHub accounts** | Especially after the ClawHavoc incident. Minimum: account should be 30+ days old with real activity. |
| **Skills that require `sudo` or root access** | Per constitution Article VI — requires explicit justification. |

---

## Token Budget Impact Estimate

Based on OpenClaw's formula (~97 chars + field lengths per skill, ~4 chars/token):

| Scenario | Skills | Est. Token Cost/Request |
|---|---|---|
| **Minimal (Tier 1 only)** | 4 skills | ~150 tokens |
| **Standard (Tier 1 + 2)** | 7 skills | ~250 tokens |
| **Full (Tier 1 + 2 + 3)** | 11 skills | ~400 tokens |
| **Full + SaaS stack (all tiers)** | 14 skills | ~500 tokens |

**Keep skills disabled when not in active use.** The SaaS stack skills (Tier 4) should only be enabled when you're actively working on a side project — not running 24/7.

### Recommendation: Start with Tier 1 + 2 (7 skills). Enable Tier 3 and 4 on-demand.

---

## Custom Skills Strategy

Before installing any community skill, consider:

1. **Can Carlos do it with built-in tools?** Bash + exec + write covers a lot.
2. **Can it be an n8n workflow instead?** Free compute on the VPS.
3. **Can Sir write a custom skill?** A custom SKILL.md in `~/carlos/skills/` is more trustworthy than any community skill and costs nothing.

Carlos can even write its own skills. If you need a specific integration, describe it to Carlos and have him generate a workspace skill in `~/carlos/skills/`. You control the code, you review it, and it's free.

---

*Minimal surface area, maximum capability. That's the C.A.R.L.O.S. way, Sir.*
