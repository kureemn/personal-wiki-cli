---
type: concept
description: Validation logic implemented in the client-side code to provide immediate user feedback before data submission.
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:26:23-07:00"
reviewed: true
reviewed_at: "2026-09-29"
definition_source: model general knowledge (not from sources)
---
# Client-Side Validation

**General definition** *(written by Gemma from general knowledge, not taken from my sources)*: Validation logic implemented in the client-side code to provide immediate user feedback before data submission.

## In my projects

<!-- from:berkeley-network-tracker-readme -->
- [[Berkeley Networking Tracker]]: A Zod schema provides instant UI feedback, mirroring the database's `CHECK` constraints. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]])
<!-- /from:berkeley-network-tracker-readme -->

## Related concepts

Added during review. Each link says why the two ideas are connected in my projects.

- [[Row Level Security]]: Client-side checks give instant feedback only; the README calls the client route guard "a UX guard, not the security boundary", which is Postgres RLS. (source: [[Berkeley Network Tracker README#Known limitations & next steps|Known limitations & next steps]])
- [[Next.js]]: The instant-feedback validation runs in the thin Next.js frontend. (source: [[Berkeley Network Tracker README#Architecture|Architecture]])

## Source

Each line above links to the section of the original document it came from. See [[Source Catalog]].
