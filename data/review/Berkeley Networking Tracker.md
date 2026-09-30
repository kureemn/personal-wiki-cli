---
type: project
description: "A private, secure contact tracker for Berkeley users, enforcing data privacy via Postgres Row Level Security."
source_id: berkeley-network-tracker-readme
source_file: raw/Berkeley Network Tracker README.md
source_sha256: 3a234448db19b7e00ee69ac882c8ab18bc487695b0640125fa848066be2348b1
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T20:22:57-07:00"
reviewed: false
---
# Berkeley Networking Tracker

This application is a private contact tracker designed for Berkeley users, ensuring that each user can only view their own contacts. Security is enforced primarily by Postgres Row Level Security (RLS), which restricts data access based on the user's JWT. The stack utilizes Next.js for the frontend and Neon Postgres with Managed Better Auth for backend services.

## Key facts

- Every visitor signs in with their own account, and every row in the database is invisible to everyone except the person who created it, enforced by Postgres itself. (source: [[Berkeley Network Tracker README#Berkeley Networking Tracker|Berkeley Networking Tracker]])
- Priority is restricted to `high` / `medium` / `low` — enforced in Postgres, not just the UI. (source: [[Berkeley Network Tracker README#Features|Features]])
- The frontend is a deliberately "thin" frontend, rendering UI and validating input for instant feedback, but holds no privileged credentials. (source: [[Berkeley Network Tracker README#Architecture|Architecture]])
- The ownership rule on contacts reduces to one predicate — `auth.user_id() = user_id`. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
- The Zod schema in `lib/validation.ts` mirrors the same rules as `CHECK` constraints so the UI can show an inline error instantly. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
- The deployed app never reads the `DATABASE_URL`; it is only touched when running the migration script locally. (source: [[Berkeley Network Tracker README#Environment variables|Environment variables]])

## Concepts and tools used

- [[Row Level Security]]: RLS policies on the contacts table enforce that users can only access rows where `auth.user_id() = user_id`.
- [[JWT Authentication]]: Managed Better Auth issues JWTs that the Data API verifies, allowing Postgres to read the user ID via `auth.user_id()`.
- [[Client-Side Validation]]: A Zod schema provides instant UI feedback by validating input before it reaches Postgres.
- [[Next.js]]: Next.js 16 is used for the frontend, leveraging the App Router and TypeScript.
- [[Neon Postgres]]: Neon Postgres hosts the contacts table, its CHECK constraints, and the RLS policies.

<!-- related:start -->
<!-- related:end -->

## Source

- Original document: [[Berkeley Network Tracker README]] (`raw/Berkeley Network Tracker README.md`, kept unchanged)
- All sources: [[Source Catalog]]
