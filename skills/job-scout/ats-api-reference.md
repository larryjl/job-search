# ATS API Reference

Reference for the three public, unauthenticated ATS APIs used in the ats-api path. Consulted during step A2 of job-scout.

---

## Endpoints

| ATS | Endpoint | Response root | JD field |
|-----|----------|---------------|----------|
| **Greenhouse** | `GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true` | `jobs[]` | `content` (raw HTML — strip tags) |
| **Lever** | `GET https://api.lever.co/v0/postings/{slug}?mode=json` | top-level `[]` | `descriptionPlain` |
| **Ashby** | `GET https://api.ashbyhq.com/posting-api/job-board/{slug}` | `jobs[]` | `descriptionPlain` |

## Field names by ATS

**Greenhouse:** `jobs[].id`, `jobs[].title`, `jobs[].location.name`, `jobs[].content` (HTML — strip tags before use), `jobs[].absolute_url`

**Lever:** `[].id`, `[].text` (title), `[].categories.location`, `[].descriptionPlain`, `[].hostedUrl`, `[].workplaceType`, `[].country`

**Ashby:** `jobs[].id`, `jobs[].title`, `jobs[].isRemote`, `jobs[].workplaceType`, `jobs[].location`, `jobs[].descriptionPlain`, `jobs[].jobUrl` (not `jobPostingUrl`), `jobs[].descriptionHtml`

## curl | python3 pattern

`web_fetch` cannot handle boards with hundreds of postings. `urllib` is blocked by the sandbox firewall. Always use this pattern:

```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/{slug}" | python3 -c "
import json, sys, re
data = json.loads(sys.stdin.read())
jobs = data.get('jobs', [])          # Ashby + Greenhouse; Lever: top-level array, no wrapper key
keywords = ['data analyst', 'data engineer', 'analytics engineer',
            'analytics manager', 'integration analyst', 'integration engineer']
matches = [j for j in jobs if any(k in j.get('title','').lower() for k in keywords)]
for j in matches:
    print(j.get('title'), '|', j.get('location'), '|', j.get('jobUrl'))
    desc = j.get('descriptionPlain', '')
    if not desc:
        html = j.get('content', '') or ''
        desc = re.sub(r'<[^>]+>', ' ', html)
        desc = re.sub(r'&[a-z#0-9]+;', ' ', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
    print(desc[:2000])
"
```

Parse and filter in the same pipeline call — do not load the full response into the context window.
