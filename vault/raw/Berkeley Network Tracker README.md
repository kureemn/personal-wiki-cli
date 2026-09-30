# Berkeley Networking Tracker

A private, secure contact tracker for the people you want to stay connected with at Berkeley — who they are, where you met them, what they do, and how much of a priority the relationship is. Every visitor signs in with their own account, and every row in the database is invisible to everyone except the person who created it, enforced by Postgres itself (not application code).

**Live app:** https://berkeley-network-tracker-sandy.vercel.app
**Repo:** https://github.com/kureemn/berkeley-network-tracker

---

## Table of contents

- [Walkthrough & screenshots](#walkthrough--screenshots)
- [Features](#features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Local setup](#local-setup)
- [Environment variables](#environment-variables)
- [Database schema](#database-schema)
- [Authentication & Row Level Security](#authentication--row-level-security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Grading evidence](#grading-evidence)
- [Known limitations & next steps](#known-limitations--next-steps)

---

## Walkthrough & screenshots

| | |
|---|---|
| **Landing page** (signed out) | ![Landing page](docs/screenshots/01-landing.png) |
| **Sign up** | ![Sign up form](docs/screenshots/02-sign-up-form.png) |
| **Empty state** (new account, no contacts yet) | ![Empty dashboard](docs/screenshots/03-dashboard-empty.png) |
| **Invalid input rejected with a clear message** | ![Empty name rejected](docs/screenshots/04-invalid-input-empty-name.png) |
| **Adding a contact** | ![Add contact form filled in](docs/screenshots/05-add-contact-form-filled.png) |
| **Contact created** | ![Contact created](docs/screenshots/06-contact-created.png) |
| **Data survives a hard refresh** | ![After refresh](docs/screenshots/07-after-refresh.png) |
| **Editing a contact** | ![Edit contact form](docs/screenshots/08-edit-contact-form.png) |
| **Sort by column, filter by priority** | ![Two contacts, sortable table](docs/screenshots/10-two-contacts-sorted.png) ![Filtered to High priority](docs/screenshots/11-filtered-high-priority.png) |
| **Delete with confirmation** | ![Delete confirmation](docs/screenshots/12-delete-confirm.png) ![After delete](docs/screenshots/13-after-delete.png) |
| **Sign out** | ![Signed out](docs/screenshots/14-signed-out.png) |
| **Account B cannot see Account A's contacts** | ![Account B sees an empty list](docs/screenshots/15-account-b-empty-cannot-see-account-a-data.png) |
| **Account A's data is untouched** | ![Account A's data intact](docs/screenshots/16-account-a-data-intact.png) |
| **Mobile layout** (390px, stacked cards instead of a table) | ![Mobile card view](docs/screenshots/17-mobile-view.png) |

These were captured by automated scripts (`scripts/capture-screenshots.mjs` and `scripts/capture-mobile-screenshot.mjs`) that drive the real app end-to-end with Playwright — sign up, add/edit/delete a contact, refresh, filter/sort, sign out, then sign up a *second* account and confirm it sees none of the first account's data. See [Grading evidence](#grading-evidence) for the full run log.

## Features

- Email/password sign up, sign in, and sign out (Neon Managed Better Auth)
- Add a contact with name, company, role, where you met them, notes, and priority
- Priority is restricted to `high` / `medium` / `low` — enforced in Postgres, not just the UI
- Sortable, filterable contact table (click a column header to sort; filter by priority; free-text search) with a stacked-card layout on mobile
- Edit and delete your own contacts
- Contacts persist in Postgres and survive a browser refresh
- Empty names and invalid priority values are rejected with a clear, inline error message
- Distinct loading, empty, success, and error states throughout
- Fully responsive: usable on a phone as well as a desktop

## Technology stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 16 (App Router, TypeScript, React 19) | File-based routing and a client-heavy App Router app were enough to keep "frontend" and "backend" cleanly separated (see [Architecture](#architecture)) without inventing a second server for a project this size. |
| Styling / components | Tailwind CSS v4 + shadcn/ui (Radix primitives) | A real component system (Dialog, Select, Table, Badge, Toast, …) instead of hand-rolled UI — accessible out of the box and easy to theme, which satisfies the "design or component system" requirement without pulling in a heavier design framework. |
| Database | Neon Postgres | Serverless Postgres with branching, and the only backend the assignment's auth/data stack is built on. |
| Auth | Neon Managed Better Auth | Hosted email/password auth that issues JWTs Postgres can read directly via `auth.user_id()` — no separate auth server to run or secrets to manage beyond a cookie secret we don't even need (see below). |
| Data access | Neon Data API (`@neondatabase/neon-js`) | A PostgREST-style REST API in front of Postgres, callable straight from the browser, with Postgres Row Level Security as the actual security boundary. This is the specific SDK the assignment calls for, used via its "two-URL object form" for both auth and data. |
| Validation | Zod (shared) + Postgres `CHECK` constraints | Two layers: a Zod schema gives instant UI feedback, and the same rules exist as `CHECK` constraints so they hold even if something bypasses the UI entirely (see [Authentication & RLS](#authentication--row-level-security)). |
| Testing | Vitest | Fast, zero-config unit testing for the validation logic. |
| Hosting | Vercel | Zero-config Next.js deployments with first-class GitHub integration. |

## Architecture

```
┌──────────────────────────┐         ┌──────────────────────────────────┐
│   Browser (Next.js app)  │         │             Neon                   │
│                           │         │                                    │
│  React client components │  HTTPS  │  ┌──────────────────────────────┐  │
│  using @neondatabase/     │────────▶│  │  Managed Better Auth          │  │
│  neon-js (two-URL form)   │         │  │  (sign up / in / out, JWTs)   │  │
│                           │         │  └──────────────┬───────────────┘  │
│  - sign up / in / out     │         │                 │ issues JWT       │
│  - contacts table UI      │  HTTPS  │  ┌──────────────▼───────────────┐  │
│  - create/edit/delete     │────────▶│  │  Neon Data API (PostgREST)    │  │
│  - sort / filter          │         │  │  validates JWT, forwards      │  │
└──────────────────────────┘         │  │  auth.user_id() into Postgres │  │
                                       │  └──────────────┬───────────────┘  │
                                       │                 ▼                  │
                                       │  ┌──────────────────────────────┐  │
                                       │  │  Postgres: contacts table     │  │
                                       │  │  + Row Level Security         │  │
                                       │  │  + CHECK constraints          │  │
                                       │  └──────────────────────────────┘  │
                                       └──────────────────────────────────┘
```

- **Frontend**: Next.js client components (everything under `app/` and `components/`). This is a deliberately "thin" frontend — it renders UI and validates input for instant feedback, but holds no privileged credentials and makes no authorization decisions itself.
- **Backend**: Neon's Managed Better Auth service (issues signed JWTs on sign-in) and the Neon Data API (a hosted PostgREST-compatible REST API that validates those JWTs and executes SQL against Postgres). This is a genuinely separate service/infrastructure from the Next.js app — the browser talks to it directly over the two public URLs below, and it is the only thing that can reach Postgres.
- **Database**: Neon Postgres. The `contacts` table, its `CHECK` constraints, and its Row Level Security policies are the actual, non-bypassable enforcement point for both data validity and per-user privacy — see the next two sections.
- **Authentication**: Managed Better Auth. `lib/neon/client.ts` builds one `NeonClient` with `createClient({ auth: { url }, dataApi: { url } })` — the "two-URL object form" — which the whole app imports as a singleton and uses for both `client.auth.*` and `client.from('contacts').*`.
- **Hosting**: Vercel, deployed straight from the `main` branch of the GitHub repo.

Two Next.js server files exist only as thin wiring, not as a data-access layer: `next.config.ts` (Turbopack config) and `app/layout.tsx` (shared shell). There is no custom `app/api/*` proxy for contacts — every contacts request goes straight from the browser to the Neon Data API, which is safe precisely because RLS decides what each request is allowed to see or change, not the client.

## Local setup

Requires Node.js 20.9+ and a Neon account with a project that has the Data API + Managed Better Auth enabled (**Neon Console → your project → Postgres database → Data API → enable, choosing Managed Better Auth**).

```bash
git clone https://github.com/kureemn/berkeley-network-tracker.git
cd berkeley-network-tracker
npm install

cp .env.example .env.local
# Fill in NEXT_PUBLIC_NEON_AUTH_URL, NEXT_PUBLIC_NEON_DATA_API_URL, and
# DATABASE_URL from the Neon Console (Data API page + Connection Details).

npm run db:migrate   # applies db/schema.sql: table, RLS policies, grants
npm run dev           # http://localhost:3000
```

Run the test suite and a production build at any time:

```bash
npm test     # Vitest — validation unit tests
npm run build
```

## Environment variables

See [`.env.example`](.env.example) for the full list with placeholder values. Names only, no real secrets, ever:

| Variable | Exposed to browser? | Used by this app? |
|---|---|---|
| `NEXT_PUBLIC_NEON_AUTH_URL` | Yes | Yes — the Managed Better Auth endpoint the browser talks to directly. |
| `NEXT_PUBLIC_NEON_DATA_API_URL` | Yes | Yes — the Data API (PostgREST) endpoint the browser talks to directly. |
| `DATABASE_URL` | No | Only by `db/migrate.mjs`, run locally/by hand to apply `db/schema.sql`. The deployed app never reads it, and it is not set in Vercel. |
| `NEON_AUTH_BASE_URL` | No | Not used by this implementation (it's the base URL a server-side Better Auth proxy would use). Documented in `.env.example` in case that's added later. |
| `NEON_AUTH_COOKIE_SECRET` | No | Same as above — reserved, not used. |

Because authentication and data access both happen client-side against Neon's own services, the Postgres connection string is never loaded by the running application at all — it only ever touches a local shell (or CI secret) when someone runs the migration script. `.env.local` is git-ignored; only `.env.example` is committed.

## Database schema

Full DDL lives in [`db/schema.sql`](db/schema.sql). The `contacts` table:

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` | Primary key, `default gen_random_uuid()`. |
| `user_id` | `text` | **Not null**, `default auth.user_id()`. Owning user's id, taken from their JWT. |
| `name` | `text` | Not null; `CHECK (length(btrim(name)) > 0)` — no empty/whitespace-only names. |
| `company` | `text` | Optional. |
| `role` | `text` | Optional. |
| `met_at` | `text` | Optional — where you met them. |
| `notes` | `text` | Optional. |
| `priority` | `text` | Not null; `CHECK (priority in ('high','medium','low'))`. |
| `created_at` | `timestamptz` | `default now()`. |
| `updated_at` | `timestamptz` | `default now()`, kept current by an `AFTER UPDATE` trigger. |

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

- **Four separate policies**, one per operation, rather than one blanket policy — each is independently readable and testable, and matches the assignment's requirement of distinct select/insert/update/delete policies.
- **`update` has both `USING` and `WITH CHECK`.** `USING` gates which existing rows you're even allowed to touch; `WITH CHECK` re-evaluates the same predicate against the row *after* the write. Without `WITH CHECK`, a user could `UPDATE ... SET user_id = 'someone-else'` and hand a row off to another account. With it, that write is rejected because the row would no longer satisfy `auth.user_id() = user_id`.
- **RLS is necessary but not sufficient.** Postgres also checks table-level `GRANT`s before it ever consults a policy — RLS policies restrict *which rows*, grants control *whether the role can attempt the operation at all*. Both are required; the last line above grants the `authenticated` role permission on all four operations.
- **The frontend holds no elevated credentials.** `NEXT_PUBLIC_NEON_AUTH_URL` and `NEXT_PUBLIC_NEON_DATA_API_URL` are safe to ship to the browser precisely because every request they make is authenticated as a specific end user and constrained by the policies above — there is no service-role key anywhere in this app.
- **Validation is layered.** The `CHECK` constraints on `name` and `priority` are the actual, unbypassable enforcement — they apply no matter how a row is written. The Zod schema in `lib/validation.ts` mirrors the same rules purely so the UI can show an inline error instantly instead of round-tripping to Postgres first.

### Verifying it yourself

1. Sign up as two different accounts (in two browser profiles, or one after signing out of the other).
2. Add a contact as account A.
3. Sign in as account B → the contacts list is empty, even though rows exist in the table.
4. Sign back in as account A → the contact is still there.

This exact flow is what `scripts/capture-screenshots.mjs` automates and what screenshots 14–16 above document.

## Testing

```bash
npm test
```

runs `vitest run` against `tests/validation.test.ts`, which exercises the same Zod schema (`lib/validation.ts`) that mirrors the database's `CHECK` constraints:

- rejects an empty `name`
- rejects a whitespace-only `name`
- rejects a `priority` outside `high` / `medium` / `low`
- accepts a fully valid payload for each of the three priority values
- confirms `name` is trimmed

Passing output (see [Grading evidence](#grading-evidence) for the full transcript):

```
 Test Files  1 passed (1)
      Tests  7 passed (7)
```

## Deployment

1. Neon: create a project, then **Postgres database → Data API → Enable**, choosing **Managed Better Auth** as the auth provider (or `neonctl data-api create --auth-provider neon_auth`). This provisions the `auth` schema, `auth.user_id()`, and the `authenticated` / `anonymous` Postgres roles.
2. Apply the schema: `npm run db:migrate` (runs `db/schema.sql` against `DATABASE_URL`).
3. Push the repo to GitHub, then import it into Vercel (or `vercel link && vercel deploy --prod`).
4. In Vercel, add `NEXT_PUBLIC_NEON_AUTH_URL` and `NEXT_PUBLIC_NEON_DATA_API_URL` as environment variables (Production, Preview, and Development).
5. Add the deployed Vercel domain to Neon Auth's trusted origins: `neonctl neon-auth domain add https://your-app.vercel.app` (or via the Neon Console).
6. Open the live URL in a private browser window and run through the [verification checklist](#authentication--row-level-security) above.

## Grading evidence

**1. Automated test — passing output**

```
$ npm test

> berkeley-network-tracker@0.1.0 test
> vitest run

 RUN  v4.1.11 /berkeley-network-tracker

 ✓ tests/validation.test.ts (7 tests) 4ms
   ✓ validateContact > rejects an empty name
   ✓ validateContact > rejects a whitespace-only name
   ✓ validateContact > rejects an invalid priority value
   ✓ validateContact > accepts a full valid payload with priority=high
   ✓ validateContact > accepts a full valid payload with priority=medium
   ✓ validateContact > accepts a full valid payload with priority=low
   ✓ validateContact > trims whitespace around the name

 Test Files  1 passed (1)
      Tests  7 passed (7)
```

**2. Sign in / sign out** — [screenshot 02](docs/screenshots/02-sign-up-form.png) (creating an account) → [screenshot 03](docs/screenshots/03-dashboard-empty.png) (signed in) → [screenshot 14](docs/screenshots/14-signed-out.png) (signed out, "Signed out." toast, redirected to the landing page).

**3. Create / edit / delete / refresh** — [05](docs/screenshots/05-add-contact-form-filled.png) → [06](docs/screenshots/06-contact-created.png) (create) → [07](docs/screenshots/07-after-refresh.png) (hard refresh, data still there) → [08](docs/screenshots/08-edit-contact-form.png) → [09](docs/screenshots/09-contact-edited.png) (edit) → [12](docs/screenshots/12-delete-confirm.png) → [13](docs/screenshots/13-after-delete.png) (delete).

**4. Two-account privacy test** — Account A ("Alice Anderson") creates a contact. [Screenshot 15](docs/screenshots/15-account-b-empty-cannot-see-account-a-data.png) shows a freshly-created Account B ("Bob Brown") looking at a completely empty contacts list. [Screenshot 16](docs/screenshots/16-account-a-data-intact.png) shows signing back in as Account A, whose contact is untouched. Both accounts hit the exact same public Data API URL — the difference is enforced entirely by the RLS policies in Postgres.

**5. Invalid input fails safely** — [Screenshot 04](docs/screenshots/04-invalid-input-empty-name.png): submitting the add-contact form with no name shows an inline "Name is required." error and makes no network request. The same rule exists as a `CHECK` constraint in Postgres (`contacts_name_not_blank`) so it holds even for a request that skips the UI.

**6. Schema & RLS ownership rule** — see [Database schema](#database-schema) and [Authentication & Row Level Security](#authentication--row-level-security) above.

**7. No committed secrets** — `.env.local` (real credentials) is git-ignored; only `.env.example` (placeholders) is committed. `DATABASE_URL` is never read by the deployed app and was never added to Vercel's environment variables. You can verify the repo's history is clean:

```bash
git log -p --all -- .env.local          # no output: this file was never committed
git grep -n "postgresql://" $(git rev-list --all) 2>/dev/null | grep -v ".env.example"
```

## Known limitations & next steps

- **Client-side route guards, not server-side.** Because auth state lives in the browser (Managed Better Auth issues a JWT the SDK holds client-side) rather than in a Next.js-readable cookie, `/contacts` is protected by a client-side redirect (`lib/neon/use-auth-guard.ts`) rather than server middleware. This is a UX guard, not the security boundary — the real boundary is Postgres RLS, which holds regardless of what the client does.
- **No password reset / email verification flow** — out of scope for this assignment, but Managed Better Auth supports both and they'd be a natural next addition.
- **Client-side search/filter only operates on the currently loaded page** of contacts, which is fine at personal-networking scale (dozens to low hundreds of contacts) but wouldn't scale to a huge list without server-side pagination and search.
- **No contact photos or richer fields** (LinkedIn URL, tags, last-contacted date) — deliberately kept to the fields the assignment specifies.
- **Single Neon branch/environment** — a production app would likely add a preview/staging branch via Neon's branching before promoting schema changes.
