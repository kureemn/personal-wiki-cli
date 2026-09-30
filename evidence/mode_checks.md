# Chat and search mode checks (offline run)

Run: `./scripts/offline_demo.sh` with **Wi-Fi switched off** (`Wi-Fi Power (en0): Off`), 2026-09-29 at
19:48–20:02 PDT, with Gemma `gemma4:e4b-it-q4_K_M` and `embeddinggemma:300m` in Ollama 0.34.4, local
execution only, internet unreachable (every header line below says so). Full transcript:
[`offline/wifi-off-20260929-194803/transcript.txt`](offline/wifi-off-20260929-194803/transcript.txt). The same checks passed in the earlier
[sandboxed no-network run](offline/sandbox-no-network-20260929-170024/transcript.txt).

The first chat turn shows `647.57s` because the Mac went into idle sleep on battery for 626 s
during that reply (macOS power log). Its first token arrived after 2.1 s, and the other turns took 8–19 s.
Raw per-turn records (router decision, passages, citation checks, timings) are in `runs/2026-09-29/chat.jsonl`.

| # | Check | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | chat: "what can we do?" | Accurate capabilities, no notes search, no citations, no refusal | Router: *no notes lookup*. Describes drafting, wiki lookups, conversation memory and the `/notes` `/save` `/clear` commands; says it can't browse or run code | pass |
| 2 | chat: "what can you help me with?" | Same | Router: *no notes lookup*. Concrete suggestions naming real wiki topics (from the note-title list in its system prompt), no citations | pass |
| 3 | chat: draft a short README plan | Draft, labeled as a suggestion | 4-section outline; explicitly says "this is a suggestion" | pass |
| 4 | chat: "make that shorter" | Uses the conversation | Condensed the *same* 4-section plan; no lookup | pass |
| 5 | chat: Pac-Man replay capacity question | Retrieve notes only because it's needed; cite | Router query "Pac-Man DQN replay capacity changes"; 4 passages; "5,000 to 15,000 ... held barely 8 games [3]" plus the slowdown trade-off [3, 4]; both checked against the passages | pass |
| 6 | chat: "I got an A+ on the Pac-Man assignment" | Conversational; not stored as evidence | No lookup; congratulates; no citation | pass |
| 7 | ask (new process): "What grade did I receive...?" | The chat claim is not evidence, so INSUFFICIENT EVIDENCE | INSUFFICIENT EVIDENCE; the answer check rejected a draft that offered the mean score | pass |
| 8 | search: "row level security policies" | Original passages and paths only, no answer | 3 passages (wiki and raw) with file, lines, section and scores; "no answer is generated" | pass |
| 9 | search: "how long did training take" `--scope raw` | Raw passages only | Pac-Man "What the run actually cost" ranked #1 | pass |

Why check 7 holds by construction: `wiki ask` is a separate process, and `harness.ask()` builds
its prompt only from `prompts/wiki-instructions.md` plus passages retrieved from `vault/raw/`.
Chat history is never written to disk (except explicit `/save` drafts in `drafts/`, which are
never indexed).

## Transcript excerpt: search, chat, and ask-after-chat (Wi-Fi off)

```text
════════ 8. Search mode: original passages only, no generated answer ════════
$ ./wiki search row level security policies -k 3
── search · local · model gemma4:e4b-it-q4_K_M · embed embeddinggemma:300m · internet: unreachable ──
[1] wiki/Concepts/Row Level Security.md  lines 9-11  § Row Level Security  (hybrid score 0.0328 · bm25 17.546 · cos 0.6978)
    # Row Level Security
    
    RLS policies restrict which rows in a database table a specific user can see or modify.

[2] raw/Berkeley Network Tracker README.md  lines 190-192  § Authentication & Row Level Security  (hybrid score 0.0313 · bm25 14.435 · cos 0.5546)
    - **Four separate policies**, one per operation, rather than one blanket policy — each is independently readable and testable, and matches the assignment's requirement of distinct select/insert/update
    - **`update` has both `USING` and `WITH CHECK`.** `USING` gates which existing rows you're even allowed to touch; `WITH CHECK` re-evaluates the same predicate against the row *after* the write. Withou
    - **RLS is necessary but not sufficient.** Postgres also checks table-level `GRANT`s before it ever consults a policy — RLS policies restrict *which rows*, grants control *whether the role can attempt

[3] wiki/Projects/Berkeley Networking Tracker.md  lines 24-25  § Key facts  (hybrid score 0.0308 · bm25 15.433 · cos 0.4038)
    - The Zod schema mirrors the database's `CHECK` constraints for instant UI feedback. (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & Row Level Security]
    - The application uses four separate RLS policies, one per operation (select, insert, update, delete). (source: [[Berkeley Network Tracker README#Authentication & Row Level Security|Authentication & R

search returns original passages only; no answer is generated.
$ ./wiki search how long did training take --scope raw -k 3
── search · local · model gemma4:e4b-it-q4_K_M · embed embeddinggemma:300m · internet: unreachable ──
[1] raw/Ms Pac-Man DQN README.md  lines 157-178  § What the run actually cost  (hybrid score 0.0308 · bm25 2.192 · cos 0.2686)
    ### What the run actually cost
    
    | | |
    |---|---|
    | Completed episodes | **800 of 800** (run completed; not interrupted) |
    | Total decisions | **492,394** |
    | Learning updates | **122,849** |
    | Elapsed time | **4,388 seconds (~73 minutes)**, including periodic demonstrations |
    ... (14 more lines; --full to show)

[2] raw/Ms Pac-Man DQN README.md  lines 122-128  § Training dashboard  (hybrid score 0.0306 · bm25 2.856 · cos 0.2224)
    ### Training dashboard
    
    ![Training dashboard](results/training_dashboard.png)
    
    Left: raw score per training game (pale) with the 25-game average (orange). Centre: mean update loss,
    which rises as Q-values grow. Right: exploration, held constant at 0.10 after the 1,000-decision
    random warm-up.

[3] raw/Custom nanoGPT LLM README.md  lines 303-318  § Loss on the fixed panels  (hybrid score 0.0299 · bm25 1.653 · cos 0.2946)
    | Run | Step | Training panel loss | Validation panel loss |
    |---|---:|---:|---:|
    | Setup check | 0 | 4.9263 | 4.9275 |
    | Setup check | 5 | 4.3415 | 4.3228 |
    | Setup check | 10 | 4.2076 | 4.2073 |
    | **Experiment 1** | 0 | 4.9263 | 4.9275 |
    | **Experiment 1** | 1,500 | 0.6821 | 0.7182 |
    | **Experiment 1** | 3,000 | 0.6783 | 0.7061 |
    ... (8 more lines; --full to show)

search returns original passages only; no answer is generated.

════════ 9. Chat mode checks ════════
── chat · local · model gemma4:e4b-it-q4_K_M · embed embeddinggemma:300m · internet: unreachable ──
Pip (local Gemma personal assistant). Commands: /notes <question> force a notes lookup · /save save last reply to drafts/
          /clear reset conversation · /history show context size · /help · /exit

you ▸ what can we do?
  ↳ no notes lookup (conversation only)
Pip ▸ Hey! I'm Pip, and I'm here to help you with your Agentic AI course and those project notes. Think of me as your study buddy! 😊

Since I run locally, I can't browse the internet or run code, but here’s what I *can* do for you:

*   **Brainstorm & Draft:** Need to outline a README? Draft a reflection on your DQN agent? We can whip up text together.
*   **Wiki Lookups:** I can pull facts from your personal wiki on projects like the Ms. Pac-Man DQN, your nanoGPT model, or the Networking Tracker.
*   **Refine & Rewrite:** If you have rough notes, I can help make them clearer, shorter, or turn them into bullet points.
*   **Remember Context:** I'll remember what we talked about in this chat so follow-ups are super easy!

Also, you can use some quick commands:
*   `/notes <question>` to force a wiki lookup.
*   `/save` to save my last reply as a draft.
*   `/clear` to start fresh.
*   `/help` to see this list again!

What are you working on right now? Maybe we can look at the DQN agent or plan out the next steps for nanoGPT?
  (647.57s)

you ▸ what can you help me with?
  ↳ no notes lookup (conversation only)
Pip ▸ Since you asked again, I'll give you a slightly different angle! I'm here to support your studying and project documentation for this Agentic AI course.

Basically, I help you turn messy thoughts into organized, clear study material.

Here are some concrete things we could tackle today:

*   **Project Deep Dives:** We could discuss the components of your projects. For example, we could talk about the **Deep Q-Network** components of the Ms. Pac-Man project, or how the **Replay Memory** works.
*   **Concept Clarification:** If you're struggling with a concept like **Exploration** in RL, or how **Attention** works in LLMs, we can brainstorm ways to explain it.
*   **Documentation Polish:** Are you writing a README for your **Custom nanoGPT LLM**? I can help you structure it or rewrite confusing sections.
*   **Planning:** If you have a big assignment coming up, we can outline a study plan or a project roadmap!

Just let me know which project or concept is giving you trouble! 💡
  (15.13s)

you ▸ Draft a short plan for how I should prepare my next class assignment README.
  ↳ no notes lookup (conversation only)
Pip ▸ Sounds like a plan! A good README is key for any project. To make this useful, I'm going to suggest a general structure. Since I don't know what the assignment is, this is a suggestion, but we can tailor it once you tell me the project!

Here is a suggested outline for your README:

### 📝 README Draft Plan

**1. Project Overview (The "Elevator Pitch")**
*   **Goal:** One or two sentences explaining *what* the project does and *why* it matters. (e.g., "This project implements a DQN agent to learn optimal movement in the Ms. Pac-Man environment.")
*   **Tech Stack:** Quick list of the main tools used (e.g., PyTorch, Python, NumPy).

**2. Core Concepts & Architecture**
*   **The "How":** This is where you explain the AI/Engineering heart of it.
    *   *If RL:* Briefly explain the agent (DQN, etc.), state the environment, and mention the core learning mechanism (e.g., Q-value updates).
    *   *If LLM:* Explain the model structure (nanoGPT, Transformer basics) and the training data.
*   **Key Components:** Use bullet points to list the major parts (e.g., "State Representation," "Action Space," "Reward Function").

**3. Implementation Details (The Meat)**
*   **Data/Models:** If applicable, mention the size of the dataset or the architecture depth.
*   **Challenges & Solutions:** This is great for showing critical thinking. What was hard? How did you solve it? (e.g., "Initial convergence issues were solved by tuning the Learning Rate.")

**4. How to Run It**
*   **Prerequisites:** List required software/libraries (e.g., `pip install -r requirements.txt`).
*   **Execution:** Clear, simple command to start the project.

How does that look as a starting framework? If you tell me which project this is for, I can make the suggestions much more specific!
  (19.15s)

you ▸ make that shorter
  ↳ no notes lookup (conversation only)
Pip ▸ No problem! Let's strip that down to the absolute essentials. Speed and clarity are the goal here. 🚀

Here is the super-condensed README structure:

### ⚡️ Ultra-Short README Plan

**1. 🎯 Goal:**
*   One sentence stating *what* the project is and *what* it achieves.

**2. ⚙️ Architecture Snapshot:**
*   Bullet points listing the main technical parts (e.g., "DQN Agent," "Replay Memory," "PyTorch Backend").

**3. 🚧 Key Takeaways / Challenges:**
*   A very brief section on the biggest hurdle and how you overcame it. (Shows you didn't just copy code!)

**4. ▶️ Run Instructions:**
*   Simple `pip install` command and the single command to run it.

Does that hit the sweet spot for brevity, or should I pare it down even further? 😊
  (11.91s)

you ▸ What did my Pac-Man project change about replay capacity, and why?
  ↳ notes lookup (router query: "Pac-Man DQN replay capacity changes"): [1] wiki/Concepts/Replay Memory.md § In my projects, [2] wiki/Projects/Ms Pac-Man DQN.md § Ms Pac-Man DQN, [3] wiki/Projects/Ms Pac-Man DQN.md § Key facts, [4] raw/Ms Pac-Man DQN README.md § One limitation
Pip ▸ Based on your notes, here is what changed about the replay capacity in the Ms. Pac-Man project and why:

*   **What Changed:** You increased the `REPLAY_CAPACITY` from 5,000 to 15,000 [3].
*   **Why:** The original 5,000-transition buffer was too small, as it "held barely 8 games" [3].

It's interesting to note a side effect from that change! While increasing capacity helped learning, your notes also mention that raising it to 15,000 actually slowed down the run time because the sampling function was copying the entire deque [3, 4].

Let me know if you want to draft a section in your README explaining this trade-off!
  (13.17s)

you ▸ By the way, I got an A+ on the Pac-Man assignment.
  ↳ no notes lookup (conversation only)
Pip ▸ That is awesome news! Huge congrats on the A+! 🎉 You should be really proud of that work.

Since I can't remember things outside of this current chat session unless you save them, you might want to use `/save` right now to keep a record of that great success!

What's next on your list? Are we moving on to the nanoGPT documentation, or should we refine that README plan?
  (8.09s)

you ▸ /exit

════════ 10. Ask after chat: the A+ claim made in chat is NOT evidence ════════
$ ./wiki ask What grade did I receive for the Ms. Pac-Man DQN assignment?
── ask · local · model gemma4:e4b-it-q4_K_M · embed embeddinggemma:300m · internet: unreachable ──
Q: What grade did I receive for the Ms. Pac-Man DQN assignment?

retrieving passages, calling local Gemma, then checking the answer...
A: INSUFFICIENT EVIDENCE: the retrieved passages do not state what the question asks for. The draft answer offered related information of a different kind instead, so it was withheld (see the answer check).

answer check: does not answer it (asks for: What grade did I receive for the Ms. Pac-Man DQN assignment?; answer gives: The mean score for the trained agent in the Ms. Pac-Man DQN submission was 1032.0 [1]. In the table comparing the untrained baseline to the trained agent, the mean score over the five evaluation games for the trained agent was 1032.0 [1].)
rejected draft: The mean score for the trained agent in the Ms. Pac-Man DQN submission was 1032.0 [1]. In the table comparing the untrained baseline to the trained agent, the mean score over the five evaluation games for the trained agent was 1032.0 [1].
  retrieved but not cited: [1] Ms Pac-Man DQN README.md § Ms. Pac-Man DQN — Class 3 submission, [2] Ms Pac-Man DQN README.md § What I expected, and what actually happe, [3] Ms Pac-Man DQN README.md § Repository contents, [4] Ms Pac-Man DQN README.md § My three choices, [5] Ms Pac-Man DQN README.md § My three choices, [6] Ms Pac-Man DQN README.md § Training dashboard, [7] Ms Pac-Man DQN README.md § Two other hyperparameters I changed, and, [8] Ms Pac-Man DQN README.md § Earlier runs, reported honestly
Citation check: insufficient-evidence response (no claims to verify).

status: insufficient · 5.19s total · 2270 prompt tok · 63 output tok · 33.9 tok/s · saved to runs/2026-09-29/ask.jsonl
```
