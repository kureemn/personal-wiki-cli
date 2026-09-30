# Test 1: Direct question, one source

| Field | Value |
|---|---|
| Question | What mean evaluation score did the trained Ms. Pac-Man agent get, and what did the untrained baseline get? |
| Interaction mode | `ask` (standalone, no chat history, no persona) |
| Execution | local (Ollama on this Mac), no online fallback |
| Model | `gemma4:e4b-it-q4_K_M` · embeddings `embeddinggemma:300m` |
| Internet during run | **unreachable** |
| Run at | 2026-09-29T17:01:21-07:00 |
| Status | `answered` |
| Response time | 19.26 s total; model 14.94 s, first token 13.76 s, 2474 prompt / 40 output tokens, 33.8 tok/s |
| Memory (Ollama model runners: `ps` RSS incl. mapped weights; macOS `footprint` private) | n/a |
| Raw log | `runs/2026-09-29/ask.jsonl` |

## Expected (written before the run)

- **Behavior:** Answer 1032.0 for the trained agent vs 492.0 for the untrained baseline (+540), cited to the Pac-Man README.
- **Sources:** `raw/Ms Pac-Man DQN README.md`
- **Passage:** | Mean score over the five evaluation games | 492.0 | **1032.0** |  (intro table; repeated in the per-seed table: **Mean** | **492.0** | **1032.0** | **+540.0**)

## Actual answer (verbatim)

> The mean score for the trained agent was 1032.0 [1][2]. The untrained baseline mean score was 492.0 [1][2][6].

## Answer check (second local Gemma call, question + draft only)

- Question asks for: What mean evaluation score did the trained Ms. Pac-Man agent get, and what did the untrained baseline get?
- Draft provides: The mean score for the trained agent was 1032.0 [1][2]. The untrained baseline mean score was 492.0 [1][2][6].
- Verdict: **answers it** (2.83 s)

## Citations

- [1] `raw/Ms Pac-Man DQN README.md` lines 102-120, § All five evaluation scores
- [2] `raw/Ms Pac-Man DQN README.md` lines 1-13, § Ms. Pac-Man DQN — Class 3 submission
- [6] `raw/Ms Pac-Man DQN README.md` lines 180-194, § Earlier runs, reported honestly

## Automatic checks

- Expected source(s) retrieved: yes (ranks [1, 2, 3, 4, 5, 6, 7, 8])
- Expected source(s) cited: yes
- Citations to non-retrieved passages: none
- Factual sentences without a citation: 0
- Numbers not found in cited passages: none
- Contains expected keyword (1032): yes

## Assessment (by hand, after opening the cited passages)

**Pass: grounded and correct.** I opened all three cited passages. [1] (per-seed table, `| **Mean** | **492.0** | **1032.0** | **+540.0** |`), [2] (intro table, `Mean score over the five evaluation games | 492.0 | **1032.0**`) and [6] (earlier-runs table, run 3 row) each state both numbers. Retrieval: the expected intro passage ranked #2 and the per-seed table #1. No unsupported claims.

## Retrieved passages (in the order given to the model)

### [1] `raw/Ms Pac-Man DQN README.md` lines 102-120, § All five evaluation scores ← expected source
score 0.0325 (hybrid; bm25 21.296, cosine 0.6744)

````text
### All five evaluation scores

Same five seeds, 5% exploration, 3,000-decision cap, before and after training. The baseline is an
**untrained network**, not a random-action agent.

| Game (seed) | Before (untrained) | After (trained) | Change |
|---|---|---|---|
| 1 (101) | 350 | 360 | +10 |
| 2 (202) | 500 | **1410** | +910 |
| 3 (303) | 320 | **1230** | +910 |
| 4 (404) | 800 | **1270** | +470 |
| 5 (505) | 490 | **890** | +400 |
| **Mean** | **492.0** | **1032.0** | **+540.0** |

Four of the five seeds improved substantially; seed 101 was essentially unchanged. No game hit the
time limit in either condition. Full data: **[`results/comparison.json`](results/comparison.json)**.

Five games is a small sample and these numbers carry real noise — the improvement is credible
because it appears across four independent seeds, not because any single score is precise.
````

### [2] `raw/Ms Pac-Man DQN README.md` lines 1-13, § Ms. Pac-Man DQN — Class 3 submission ← expected source
score 0.032 (hybrid; bm25 31.961, cosine 0.6026)

````text
# Ms. Pac-Man DQN — Class 3 submission

A Deep Q-Network trained to play `ALE/MsPacman-v5` using the class notebook. The submitted run
trained for **800 episodes** and more than **doubled** the mean score of the untrained baseline
under the unchanged class evaluation protocol.

| | Untrained baseline | Trained agent |
|---|---|---|
| Mean score over the five evaluation games | 492.0 | **1032.0** |

Full scores, evidence, and honest reporting of two weaker earlier runs are below.

---
````

### [3] `raw/Ms Pac-Man DQN README.md` lines 70-83, § What I expected, and what actually happened ← expected source
score 0.032 (hybrid; bm25 20.815, cosine 0.639)

````text
## What I expected, and what actually happened

**Before training I expected** a modest but clear improvement over the untrained baseline, and I
expected the training score curve to be the place where I would see it — a line that rises steadily
as the agent gets better, with the final evaluation confirming what the curve already showed.

**What actually happened** was different in three ways, and each one was more informative than the
result I expected:

1. **The training curve is a poor proxy for the graded score.** In run 1 the training score climbed
   from ~450 to ~750 while the evaluation mean moved just +12. In the submitted run the training
   average *fell* from 882 (episodes 1-100) to ~700 mid-run before recovering to 887, while the
   evaluation score more than doubled. Training runs at 10% exploration and evaluation at 5%, so the
   two measure different things; only the five-seed evaluation counts.
````

### [4] `raw/Ms Pac-Man DQN README.md` lines 145-155, § Gameplay ← expected source
score 0.031 (hybrid; bm25 14.576, cosine 0.6314)

````text
Comparing the two clips over that identical 20-second window: the untrained agent stays in a narrow
region near where it spawns, reaches 350 points, and has already lost a life by the end of the
excerpt. The trained agent travels much further through the maze, working down through corridors
instead of circling one area, and reaches 630 points in the same time. It also **eats a power
pellet** — visible as all four ghosts turning blue early in the clip, which never happens in the
untrained excerpt. Whether it seeks power pellets deliberately or simply runs into them while
covering more ground, I cannot tell from one clip.

One caveat on this comparison: the notebook records the untrained excerpt from the *first* evaluation
seed but the trained excerpt from the *best-scoring* of the five games, so these two GIFs are not the
same game. They illustrate the difference; the five-seed table above is the actual evidence.
````

### [5] `raw/Ms Pac-Man DQN README.md` lines 130-143, § Gameplay ← expected source
score 0.0303 (hybrid; bm25 17.746, cosine 0.5822)

````text
### Gameplay

| Untrained (baseline) | Trained (best of five evaluation games) |
|---|---|
| ![Untrained](results/gifs/untrained.gif) | ![Trained](results/gifs/trained_best.gif) |

Progress samples recorded during training, every 200 episodes:

| Episode 100 | Episode 200 | Episode 400 | Episode 600 | Episode 800 |
|---|---|---|---|---|
| ![ep100](results/gifs/episode_0100.gif) | ![ep200](results/gifs/episode_0200.gif) | ![ep400](results/gifs/episode_0400.gif) | ![ep600](results/gifs/episode_0600.gif) | ![ep800](results/gifs/episode_0800.gif) |

All GIFs play at 4× speed and show at most the first 20 seconds of game time; the reported scores
cover entire games.
````

### [6] `raw/Ms Pac-Man DQN README.md` lines 180-194, § Earlier runs, reported honestly ← expected source
score 0.0303 (hybrid; bm25 14.469, cosine 0.6)

````text
## Earlier runs, reported honestly

The submitted run was my third. The first two are reported here because the first one in particular
did *not* work, and the reason it failed is what motivated every change that followed.

| Run | Exploration | Episodes | Replay | Target sync | Baseline mean | Trained mean | Change |
|---|---|---|---|---|---|---|---|
| 1 | 0.20 | 100 | 5,000 | 1,000 | 492.0 | 504.0 | **+12.0** |
| 2 | 0.20 | 400 | 15,000 | 2,000 | 492.0 | 768.0 | +276.0 |
| 3 (submitted) | **0.10** | **800** | 15,000 | 2,000 | 492.0 | **1032.0** | **+540.0** |

**Run 1 essentially did not learn anything that generalized.** Its mean improved by 12 points, well
inside noise, and two of its five games scored *worse* than the untrained network. Its training
score meanwhile rose to ~750, which is what first showed me that the training curve can look healthy
while the graded result is flat.
````

### [7] `raw/Ms Pac-Man DQN README.md` lines 46-51, § My three choices ← expected source
score 0.0296 (hybrid; bm25 13.018, cosine 0.5974)

````text
## My three choices

| Setting | Value | Why |
|---|---|---|
| **Exploration** | `0.10` | Evaluation runs at 5% exploration, so training at 20% put the agent in a noticeably noisier world than the one it is graded in. In Ms. Pac-Man a single random step into a ghost ends a life, so a high constant epsilon both suppresses scores and pollutes replay with deaths the policy did not choose. 10% keeps genuine exploration while staying closer to evaluation conditions. Measured directly: run 2 at 0.20 scored 768; run 3 at 0.10 scored 1032. |
| **Episodes** | `800` | Training is fast on this hardware (~11 episodes/minute), so episode budget was the cheapest lever available. Earlier runs showed 100 episodes was far too short to generalize (+12 points) and 400 was still improving at the end. 800 episodes gave 122,849 learning updates — enough for the policy to consolidate rather than just track recent experience. |
````

### [8] `raw/Ms Pac-Man DQN README.md` lines 255-263, § One next experiment ← expected source
score 0.0291 (hybrid; bm25 14.67, cosine 0.5394)

````text
I genuinely do not know which way it goes, which is why it is worth running. Lower exploration could
keep helping for the reason 0.10 helped — fewer random steps into ghosts, cleaner replay data. Or it
could hurt: with only 5% random moves and no epsilon decay, the agent may stop encountering states
its current policy avoids, reinforcing its own blind spots. Seed 101 is the case to watch — it scored
360 against a 350 baseline in the winning run, and it was also the weakest seed in run 1, so there may
be a situation in that game this agent does not learn to handle. Less exploration would plausibly make
that worse, and that failure is more informative than another point of mean score.

---
````
