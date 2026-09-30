# Test 2: Answerable, phrased differently from the source

| Field | Value |
|---|---|
| Question | Why can't one person using my networking app see someone else's saved contacts? |
| Interaction mode | `ask` (standalone, no chat history, no persona) |
| Execution | local (Ollama on this Mac), no online fallback |
| Model | `gemma4:e4b-it-q4_K_M` · embeddings `embeddinggemma:300m` |
| Internet during run | **unreachable** |
| Run at | 2026-09-29T20:17:27-07:00 |
| Status | `answered` |
| Response time | 17.85 s total; model 14.04 s, first token 9.64 s, 2291 prompt / 114 output tokens, 25.9 tok/s |
| Memory (Ollama model runners: `ps` RSS incl. mapped weights; macOS `footprint` private) | n/a |
| Raw log | `runs/2026-09-29/ask.jsonl` |

## Expected (written before the run)

- **Behavior:** Explain Postgres Row Level Security: every policy on the contacts table checks auth.user_id() = user_id, where auth.user_id() comes from the signed-in user's JWT. The source never uses the words 'person' or 'someone else'.
- **Sources:** `raw/Berkeley Network Tracker README.md`
- **Passage:** ## Authentication & Row Level Security -- 'every policy on `contacts` reduces to one predicate — `auth.user_id() = user_id`'

## Actual answer (verbatim)

> The inability for one person to see another person's saved contacts is enforced by Row Level Security (RLS) policies in Postgres [5]. Specifically, every policy on the `contacts` table reduces to the predicate `auth.user_id() = user_id` [5]. This means that the Data API verifies the JWT signature, and Postgres ensures that a user can only see or change data where the `user_id` matches the authenticated user's ID [5]. This privacy is enforced by Postgres itself, not by application code [1].

## Answer check (second local Gemma call, question + draft only)

- Question asks for: Why can't one person using my networking app see someone else's saved contacts?
- Draft provides: The reason is that Row Level Security (RLS) policies in Postgres enforce that a user can only see data where the `user_id` matches their authenticated ID.
- Verdict: **answers it** (3.57 s)

## Citations

- [1] `raw/Berkeley Network Tracker README.md` lines 1-8, § Berkeley Networking Tracker
- [5] `raw/Berkeley Network Tracker README.md` lines 161-188, § Authentication & Row Level Security

## Automatic checks

- Expected source(s) retrieved: yes (ranks [1, 2, 3, 4, 5, 6, 7, 8])
- Expected source(s) cited: yes
- Citations to non-retrieved passages: none
- Factual sentences without a citation: 0
- Numbers not found in cited passages: none
- Contains expected keyword (row level security / rls / auth.user_id): yes

## Assessment (by hand, after opening the cited passages)

**Pass: grounded and correct, despite different wording.** The question says 'person' and 'someone else'; the source says 'user', 'Row Level Security' and `auth.user_id() = user_id`. [1] states rows are invisible to everyone except their creator, enforced by Postgres; [5] contains the ownership predicate and the JWT verification sentence; [6] is the two-account verification (account B sees an empty list). Retrieval weakness: the key RLS passage ranked only #5 of 8 (the embedding model preferred the intro and screenshot passages), so a smaller k would have lost it. See the retrieval notes in the README.

## Retrieved passages (in the order given to the model)

### [1] `raw/Berkeley Network Tracker README.md` lines 1-8, § Berkeley Networking Tracker ← expected source
score 0.0325 (hybrid; bm25 17.603, cosine 0.4014)

````text
# Berkeley Networking Tracker

A private, secure contact tracker for the people you want to stay connected with at Berkeley — who they are, where you met them, what they do, and how much of a priority the relationship is. Every visitor signs in with their own account, and every row in the database is invisible to everyone except the person who created it, enforced by Postgres itself (not application code).

**Live app:** https://berkeley-network-tracker-sandy.vercel.app
**Repo:** https://github.com/kureemn/berkeley-network-tracker

---
````

### [2] `raw/Berkeley Network Tracker README.md` lines 41-46, § Walkthrough & screenshots ← expected source
score 0.0313 (hybrid; bm25 8.824, cosine 0.4146)

````text
| **Sign out** | ![Signed out](docs/screenshots/14-signed-out.png) |
| **Account B cannot see Account A's contacts** | ![Account B sees an empty list](docs/screenshots/15-account-b-empty-cannot-see-account-a-data.png) |
| **Account A's data is untouched** | ![Account A's data intact](docs/screenshots/16-account-a-data-intact.png) |
| **Mobile layout** (390px, stacked cards instead of a table) | ![Mobile card view](docs/screenshots/17-mobile-view.png) |

These were captured by automated scripts (`scripts/capture-screenshots.mjs` and `scripts/capture-mobile-screenshot.mjs`) that drive the real app end-to-end with Playwright — sign up, add/edit/delete a contact, refresh, filter/sort, sign out, then sign up a *second* account and confirm it sees none of the first account's data. See [Grading evidence](#grading-evidence) for the full run log.
````

### [3] `raw/Berkeley Network Tracker README.md` lines 277-283, § Known limitations & next steps ← expected source
score 0.0306 (hybrid; bm25 8.8, cosine 0.3953)

````text
## Known limitations & next steps

- **Client-side route guards, not server-side.** Because auth state lives in the browser (Managed Better Auth issues a JWT the SDK holds client-side) rather than in a Next.js-readable cookie, `/contacts` is protected by a client-side redirect (`lib/neon/use-auth-guard.ts`) rather than server middleware. This is a UX guard, not the security boundary — the real boundary is Postgres RLS, which holds regardless of what the client does.
- **No password reset / email verification flow** — out of scope for this assignment, but Managed Better Auth supports both and they'd be a natural next addition.
- **Client-side search/filter only operates on the currently loaded page** of contacts, which is fine at personal-networking scale (dozens to low hundreds of contacts) but wouldn't scale to a huge list without server-side pagination and search.
- **No contact photos or richer fields** (LinkedIn URL, tags, last-contacted date) — deliberately kept to the fields the assignment specifies.
- **Single Neon branch/environment** — a production app would likely add a preview/staging branch via Neon's branching before promoting schema changes.
````

### [4] `raw/Berkeley Network Tracker README.md` lines 102-104, § Architecture ← expected source
score 0.0301 (hybrid; bm25 9.568, cosine 0.3332)

````text
- **Hosting**: Vercel, deployed straight from the `main` branch of the GitHub repo.

Two Next.js server files exist only as thin wiring, not as a data-access layer: `next.config.ts` (Turbopack config) and `app/layout.tsx` (shared shell). There is no custom `app/api/*` proxy for contacts — every contacts request goes straight from the browser to the Neon Data API, which is safe precisely because RLS decides what each request is allowed to see or change, not the client.
````

### [5] `raw/Berkeley Network Tracker README.md` lines 161-188, § Authentication & Row Level Security ← expected source
score 0.03 (hybrid; bm25 12.123, cosine 0.3145)

````text
## Authentication & Row Level Security

**Ownership rule:** every policy on `contacts` reduces to one predicate — `auth.user_id() = user_id` — where `auth.user_id()` reads the `sub` claim out of the JWT that Managed Better Auth issued when the current user signed in, and the Data API verifies that JWT's signature before Postgres ever sees the query.

```sql
alter table contacts enable row level security;

create policy contacts_select_own on contacts
  for select to authenticated
  using (auth.user_id() = user_id);

create policy contacts_insert_own on contacts
  for insert to authenticated
  with check (auth.user_id() = user_id);

create policy contacts_update_own on contacts
  for update to authenticated
  using (auth.user_id() = user_id)
  with check (auth.user_id() = user_id);

create policy contacts_delete_own on contacts
  for delete to authenticated
  using (auth.user_id() = user_id);

grant select, insert, update, delete on contacts to authenticated;
```

A few things worth calling out explicitly, since they're easy to get subtly wrong:
````

### [6] `raw/Berkeley Network Tracker README.md` lines 98-101, § Architecture ← expected source
score 0.029 (hybrid; bm25 9.135, cosine 0.3112)

````text
- **Frontend**: Next.js client components (everything under `app/` and `components/`). This is a deliberately "thin" frontend — it renders UI and validates input for instant feedback, but holds no privileged credentials and makes no authorization decisions itself.
- **Backend**: Neon's Managed Better Auth service (issues signed JWTs on sign-in) and the Neon Data API (a hosted PostgREST-compatible REST API that validates those JWTs and executes SQL against Postgres). This is a genuinely separate service/infrastructure from the Next.js app — the browser talks to it directly over the two public URLs below, and it is the only thing that can reach Postgres.
- **Database**: Neon Postgres. The `contacts` table, its `CHECK` constraints, and its Row Level Security policies are the actual, non-bypassable enforcement point for both data validity and per-user privacy — see the next two sections.
- **Authentication**: Managed Better Auth. `lib/neon/client.ts` builds one `NeonClient` with `createClient({ auth: { url }, dataApi: { url } })` — the "two-URL object form" — which the whole app imports as a singleton and uses for both `client.auth.*` and `client.from('contacts').*`.
````

### [7] `raw/Berkeley Network Tracker README.md` lines 196-203, § Verifying it yourself ← expected source
score 0.029 (hybrid; bm25 5.366, cosine 0.3908)

````text
### Verifying it yourself

1. Sign up as two different accounts (in two browser profiles, or one after signing out of the other).
2. Add a contact as account A.
3. Sign in as account B → the contacts list is empty, even though rows exist in the table.
4. Sign back in as account A → the contact is still there.

This exact flow is what `scripts/capture-screenshots.mjs` automates and what screenshots 14–16 above document.
````

### [8] `raw/Berkeley Network Tracker README.md` lines 262-264, § Grading evidence ← expected source
score 0.0289 (hybrid; bm25 5.854, cosine 0.3836)

````text
**3. Create / edit / delete / refresh** — [05](docs/screenshots/05-add-contact-form-filled.png) → [06](docs/screenshots/06-contact-created.png) (create) → [07](docs/screenshots/07-after-refresh.png) (hard refresh, data still there) → [08](docs/screenshots/08-edit-contact-form.png) → [09](docs/screenshots/09-contact-edited.png) (edit) → [12](docs/screenshots/12-delete-confirm.png) → [13](docs/screenshots/13-after-delete.png) (delete).

**4. Two-account privacy test** — Account A ("Alice Anderson") creates a contact. [Screenshot 15](docs/screenshots/15-account-b-empty-cannot-see-account-a-data.png) shows a freshly-created Account B ("Bob Brown") looking at a completely empty contacts list. [Screenshot 16](docs/screenshots/16-account-a-data-intact.png) shows signing back in as Account A, whose contact is untouched. Both accounts hit the exact same public Data API URL — the difference is enforced entirely by the RLS policies in Postgres.
````
