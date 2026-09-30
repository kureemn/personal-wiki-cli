---
type: concept
description: RLS policies restrict which rows in a database table a specific user can see or modify.
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:26:23-07:00"
reviewed: true
reviewed_at: "2026-09-29"
definition_source: model general knowledge (not from sources)
---
# Row Level Security

**General definition** *(written by Gemma from general knowledge, not taken from my sources)*: RLS policies restrict which rows in a database table a specific user can see or modify.

## In my projects

<!-- from:berkeley-network-tracker-readme -->
- [[Berkeley Networking Tracker]]: RLS policies on the contacts table enforce that users can only access rows where `auth.user_id() = user_id`. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
<!-- /from:berkeley-network-tracker-readme -->

## Related concepts

Added during review. Each link says why the two ideas are connected in my projects.

- [[JWT Authentication]]: Every policy compares `auth.user_id()`, which reads the `sub` claim of the signed-in user's JWT. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
- [[Client-Side Validation]]: Browser-side checks are conveniences; RLS holds regardless of what the client does. (source: [[Berkeley Network Tracker README#Known limitations & next steps|Known limitations & next steps]])
- [[Serverless Database]]: The policies live in, and are enforced by, the Neon Postgres database. (source: [[Berkeley Network Tracker README#Technology stack|Technology stack]])

## Source

Each line above links to the section of the original document it came from. See [[Source Catalog]].
