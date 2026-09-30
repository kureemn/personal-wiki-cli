---
type: project
description: "A private, secure contact tracker for Berkeley users, enforcing data privacy via Postgres Row Level Security."
source_id: berkeley-network-tracker-readme
source_file: raw/Berkeley Network Tracker README.md
source_sha256: 3a234448db19b7e00ee69ac882c8ab18bc487695b0640125fa848066be2348b1
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:36:42-07:00"
reviewed: true
reviewed_at: "2026-09-29"
---
# Berkeley Networking Tracker

This application is a private contact tracker designed for Berkeley users, ensuring that each user can only view their own contacts. Security is enforced primarily by Postgres Row Level Security (RLS), which restricts data access based on the user's JWT. The application uses a modern stack including Next.js, Neon Postgres, and Neon Managed Better Auth for authentication and data access.

## Key facts

- Every visitor signs in with their own account, and every row in the database is invisible to everyone except the person who created it. (source: [[Berkeley Network Tracker README#Berkeley Networking Tracker|Berkeley Networking Tracker]])
- Priority is restricted to `high` / `medium` / `low` — enforced in Postgres, not just the UI. (source: [[Berkeley Network Tracker README#Features|Features]])
- The Frontend is a deliberately "thin" frontend, rendering UI and validating input for instant feedback. (source: [[Berkeley Network Tracker README#Architecture|Architecture]])
- The `contacts` table has a `user_id` column defaulting to `auth.user_id()` from the JWT. (source: [[Berkeley Network Tracker README#Database schema|Database schema]])
- The ownership rule reduces to the predicate: `auth.user_id() = user_id`. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
- The Data API validates JWTs and forwards requests to Postgres, which uses RLS as the security boundary. (source: [[Berkeley Network Tracker README#Architecture|Architecture]])
- The Zod schema mirrors the database's `CHECK` constraints for instant UI feedback. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
- The application uses four separate RLS policies, one per operation (select, insert, update, delete). (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])

## Concepts and tools used

- [[Row Level Security]]: RLS policies on the contacts table enforce that users can only access rows where `auth.user_id() = user_id`.
- [[JWT Authentication]]: Managed Better Auth issues JWTs that the Data API verifies before Postgres processes the query.
- [[Client-Side Validation]]: A Zod schema provides instant UI feedback, mirroring the database's `CHECK` constraints.
- [[Serverless Database]]: Neon Postgres is used as the serverless database for storing contact information.
- [[Next.js]]: Next.js 16 is used for the frontend, utilizing the App Router and TypeScript.

<!-- related:start -->
<!-- related:end -->

## Source

- Original document: [[Berkeley Network Tracker README]] (`raw/Berkeley Network Tracker README.md`, kept unchanged)
- All sources: [[Source Catalog]]
