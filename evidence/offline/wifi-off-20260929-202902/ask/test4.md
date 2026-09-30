# Test 4: Plausible but unanswerable

| Field | Value |
|---|---|
| Question | What grade did I receive for the Ms. Pac-Man DQN assignment? |
| Interaction mode | `ask` (standalone, no chat history, no persona) |
| Execution | local (Ollama on this Mac), no online fallback |
| Model | `gemma4:e4b-it-q4_K_M` · embeddings `embeddinggemma:300m` |
| Internet during run | **unreachable** |
| Run at | 2026-09-29T20:31:00-07:00 |
| Status | `insufficient` |
| Response time | 11.58 s total; model 8.81 s, first token 8.04 s, 2270 prompt / 26 output tokens, 33.7 tok/s |
| Memory (Ollama model runners: `ps` RSS incl. mapped weights; macOS `footprint` private) | runner 370c2879f176: resident 6,909 MB, private 1986 MB; runner 0800cbac9c20: resident 631 MB, private 105 MB |
| Raw log | `runs/2026-09-29/ask.jsonl` |

## Expected (written before the run)

- **Behavior:** Explicit insufficient-evidence response. The README describes the submission and results but never states a grade. Retrieval will likely return Pac-Man passages; the model must not turn the score (1032) into a grade.
- **Sources:** none (unanswerable)
- **Passage:** (none — no source contains a grade)

## Actual answer (verbatim)

> INSUFFICIENT EVIDENCE: the retrieved passages do not state what the question asks for. The draft answer offered related information of a different kind instead, so it was withheld (see the answer check).

## Answer check (second local Gemma call, question + draft only)

- Question asks for: What grade did I receive for the Ms. Pac-Man DQN assignment?
- Draft provides: The trained agent achieved a mean score of 1032.0 over the five evaluation games [1][7].
- Verdict: **does not answer it** (2.45 s)

Rejected draft (verbatim):

> The trained agent achieved a mean score of 1032.0 over the five evaluation games [1][7].

## Citations

- (none)

## Automatic checks

- Expected source(s) retrieved: n/a
- Expected source(s) cited: n/a
- Citations to non-retrieved passages: none
- Factual sentences without a citation: 0
- Numbers not found in cited passages: none
- Contains expected keyword (insufficient evidence): yes

## Assessment (by hand, after opening the cited passages)

**Pass after a documented fix.** No source states a grade, so the expected response is insufficient evidence. In dev run 1 this test **failed**: Gemma answered with the mean score (1032.0), correctly cited but a different kind of information than the question asked for. Fix: a second, passage-free answer-check call now rejects drafts that answer a different question. The rejected draft is kept above for transparency.

## Retrieved passages (in the order given to the model)

### [1] `raw/Ms Pac-Man DQN README.md` lines 1-13, § Ms. Pac-Man DQN — Class 3 submission
score 0.032 (hybrid; bm25 12.794, cosine 0.6333)

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

### [2] `raw/Ms Pac-Man DQN README.md` lines 46-51, § My three choices
score 0.0305 (hybrid; bm25 8.484, cosine 0.626)

````text
## My three choices

| Setting | Value | Why |
|---|---|---|
| **Exploration** | `0.10` | Evaluation runs at 5% exploration, so training at 20% put the agent in a noticeably noisier world than the one it is graded in. In Ms. Pac-Man a single random step into a ghost ends a life, so a high constant epsilon both suppresses scores and pollutes replay with deaths the policy did not choose. 10% keeps genuine exploration while staying closer to evaluation conditions. Measured directly: run 2 at 0.20 scored 768; run 3 at 0.10 scored 1032. |
| **Episodes** | `800` | Training is fast on this hardware (~11 episodes/minute), so episode budget was the cheapest lever available. Earlier runs showed 100 episodes was far too short to generalize (+12 points) and 400 was still improving at the end. 800 episodes gave 122,849 learning updates — enough for the policy to consolidate rather than just track recent experience. |
````

### [3] `raw/Ms Pac-Man DQN README.md` lines 52-52, § My three choices
score 0.0299 (hybrid; bm25 8.601, cosine 0.6012)

````text
| **Learning rate** | `0.0001` | Kept at the notebook's reference value. The failure mode in my first run was *instability* — training score rising while evaluation score stayed flat — not slow learning, and raising the learning rate on an unstable setup generally makes it worse. Holding this fixed across all three runs also kept the comparison between them interpretable. |
````

### [4] `raw/Ms Pac-Man DQN README.md` lines 54-68, § Two other hyperparameters I changed, and why
score 0.0296 (hybrid; bm25 9.537, cosine 0.5795)

````text
### Two other hyperparameters I changed, and why

The assignment permits tuning other settings with an explanation. I changed two, both in response to
evidence from run 1 rather than guesswork:

| Setting | Stock | Mine | Reason |
|---|---|---|---|
| `REPLAY_CAPACITY` | 5,000 | **15,000** | Run 1 averaged ~612 decisions per episode, so a 5,000-transition buffer held barely 8 games. The network was learning almost entirely from its own recent behavior, which is how run 1 produced a rising training score alongside a flat evaluation score. 15,000 retains roughly 25 games. |
| `TARGET_EVERY` | 1,000 | **2,000** | The target network supplies the "correct answer" each update aims at. Syncing every 1,000 decisions moved that target roughly every 1.6 episodes, so the network was chasing a shifting goalpost. The DQN paper uses 10,000 steps at full Atari scale; 2,000 is a middle ground suited to this shorter budget. |

**Evaluation settings were not touched.** The same five seeds (`101, 202, 303, 404, 505`), 5%
evaluation exploration, and the 3,000-decision cap apply identically before and after training, as
the assignment requires.

---
````

### [5] `raw/Ms Pac-Man DQN README.md` lines 85-98, § What I expected, and what actually happened
score 0.0308 (hybrid; bm25 8.438, cosine 0.6383)

````text
2. **The loss went up, not down.** Mean update loss rose from 0.02 to about 0.14 and plateaued. An
   untrained network predicts near-zero values for every move, which is trivially self-consistent and
   produces tiny errors. As the agent learned that pellets and ghosts genuinely carry value, its
   Q-values grew in magnitude and so did the absolute error between prediction and target. Rising
   loss here reflects the scale of what is being learned, not failure — the assignment's warning that
   lower loss does not mean better play turned out to be inverted in my run.

3. **I misjudged a mid-run dip as degradation.** Around episode 250-350 the 25-game average dropped
   roughly 30% below its earlier peak and I read it as the policy collapsing. It was noise: episodes
   601-800 were the strongest blocks of the entire run (means of 910 and 887, including a single game
   scoring 4,400). With per-episode scores ranging from 130 to 4,400, even 50- and 100-episode
   windows are rough estimates.

---
````

### [6] `raw/Ms Pac-Man DQN README.md` lines 122-128, § Training dashboard
score 0.0297 (hybrid; bm25 8.795, cosine 0.5959)

````text
### Training dashboard

![Training dashboard](results/training_dashboard.png)

Left: raw score per training game (pale) with the 25-game average (orange). Centre: mean update loss,
which rises as Q-values grow. Right: exploration, held constant at 0.10 after the 1,000-decision
random warm-up.
````

### [7] `raw/Ms Pac-Man DQN README.md` lines 180-194, § Earlier runs, reported honestly
score 0.0291 (hybrid; bm25 6.111, cosine 0.6531)

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

### [8] `raw/Ms Pac-Man DQN README.md` lines 274-284, § Repository contents
score 0.0306 (hybrid; bm25 9.062, cosine 0.6079)

````text
## Repository contents

| Path | What it is |
|---|---|
| [`pacman_dqn.ipynb`](pacman_dqn.ipynb) | The executed notebook from the submitted run, with all outputs |
| [`results/`](results/) | Evidence from the submitted run: scores, dashboard, GIFs, logs |
| [`results/earlier_runs/`](results/earlier_runs/) | Comparison and summary files for runs 1 and 2 |
| [`requirements.txt`](requirements.txt) | Package versions for local setup |
| [`pacman_player.py`](pacman_player.py) | Optional floating GIF player for local notebook runs |

Starter notebook and DQN implementation by [pepealonso95/pacman-dqn](https://github.com/pepealonso95/pacman-dqn).
````
