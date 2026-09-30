# Test 3: Answer connects two sources

| Field | Value |
|---|---|
| Question | Which compute device did I train the Pac-Man agent and the nanoGPT models on, and how long did the training take for each? |
| Interaction mode | `ask` (standalone, no chat history, no persona) |
| Execution | local (Ollama on this Mac), no online fallback |
| Model | `gemma4:e4b-it-q4_K_M` · embeddings `embeddinggemma:300m` |
| Internet during run | **unreachable** |
| Run at | 2026-09-29T19:49:38-07:00 |
| Status | `answered` |
| Response time | 19.52 s total; model 14.37 s, first token 11.13 s, 3161 prompt / 114 output tokens, 35.1 tok/s |
| Memory (Ollama model runners: `ps` RSS incl. mapped weights; macOS `footprint` private) | runner 370c2879f176: resident 6,667 MB, private 1874 MB; runner 0800cbac9c20: resident 619 MB, private 107 MB |
| Raw log | `runs/2026-09-29/ask.jsonl` |

## Expected (written before the run)

- **Behavior:** Pac-Man: Apple M1 Pro with the PyTorch MPS backend, ~73 minutes (4,388 s) for 800 episodes. nanoGPT: same M1 Pro but DEVICE="cpu", training loop 16.6 s (starter) and 18.7 s (expanded). Each claim cited to its own README.
- **Sources:** `raw/Ms Pac-Man DQN README.md`, `raw/Custom nanoGPT LLM README.md`
- **Passage:** Pac-Man 'What the run actually cost' table (Elapsed time 4,388 seconds, Hardware ... PyTorch MPS backend); nanoGPT '## The runs' table (Training-loop time 16.6 s / 18.7 s) and 'DEVICE="cpu" as in the course notebook'

## Actual answer (verbatim)

> The Pac-Man agent was trained on Apple M1 Pro hardware with the PyTorch MPS backend [4]. The training for the Pac-Man agent took 4,388 seconds (~73 minutes) [4]. The nanoGPT models were trained using Apple M1 Pro (16 GB) on macOS 26.6.2 with `DEVICE="cpu"` [1]. The training times for the nanoGPT runs were 16.6 s for Experiment 1 and 18.7 s for Experiment 2 [2].

## Answer check (second local Gemma call, question + draft only)

- Question asks for: Which compute device did I train the Pac-Man agent and the nanoGPT models on, and how long did the training take for each?
- Draft provides: The compute device for the Pac-Man agent was Apple M1 Pro hardware, and the training took 4,388 seconds (~73 minutes). The compute device for the nanoGPT models was Apple M1 Pro (16 GB) on macOS 26.6.2 with `DEVICE="cpu"`, and the training times were 16.6 s for Experiment 1 and 18.7 s for Experiment 2.
- Verdict: **answers it** (4.83 s)

## Citations

- [1] `raw/Custom nanoGPT LLM README.md` lines 272-280, § The runs
- [2] `raw/Custom nanoGPT LLM README.md` lines 260-271, § The runs
- [4] `raw/Ms Pac-Man DQN README.md` lines 157-178, § What the run actually cost

## Automatic checks

- Expected source(s) retrieved: yes (ranks [1, 2, 3, 4, 5, 6, 7, 8])
- Expected source(s) cited: yes
- Citations to non-retrieved passages: none
- Factual sentences without a citation: 0
- Numbers not found in cited passages: none
- Contains expected keyword (mps): yes

## Assessment (by hand, after opening the cited passages)

**Pass: grounded, correct, and combines two sources.** Pac-Man: [4] ('What the run actually cost') gives Apple M1 Pro, PyTorch MPS backend and 4,388 s (~73 min). nanoGPT: [1] gives `DEVICE="cpu"` on the M1 Pro, and [2] gives the 16.6 s and 18.7 s training-loop times. One nuance is lost: the README says the 4,388 s *includes periodic demonstrations*, and the answer does not mention it. This needed hybrid retrieval: with plain BM25 (retrieval v1) neither expected passage was retrieved.

## Retrieved passages (in the order given to the model)

### [1] `raw/Custom nanoGPT LLM README.md` lines 272-280, § The runs ← expected source
score 0.0305 (hybrid; bm25 6.794, cosine 0.5274)

````text
| Config, summary | – | [config](llm_runs/20260921T061558_478156Z/config.json), [summary](llm_runs/20260921T061558_478156Z/training_summary.json), [vocab report](llm_runs/20260921T061558_478156Z/vocabulary_report.json), [manifest](llm_runs/20260921T061558_478156Z/corpus_manifest.json) | [config](llm_runs/20260921T062609_432761Z/config.json), [summary](llm_runs/20260921T062609_432761Z/training_summary.json), [vocab report](llm_runs/20260921T062609_432761Z/vocabulary_report.json), [manifest](llm_runs/20260921T062609_432761Z/corpus_manifest.json) |

Hardware: Apple M1 Pro (16 GB), macOS 26.6.2, Python 3.12.14, PyTorch 2.14.0, `DEVICE="cpu"`
as in the course notebook. Seed 42, batch 32, 2 layers, 4 heads, 64-dim, block size 48.

**What stayed fixed:** seed, model shape, batch size, steps, learning rate and schedule,
eval suite, loss-panel sampling seeds, sampling seed and generation settings.
**What training changed:** only the weights. **What changed only at inference:** temperature
and prompts. Neither changes any weight: the eval runner asserts the model hash is unchanged.
````

### [2] `raw/Custom nanoGPT LLM README.md` lines 260-271, § The runs ← expected source
score 0.0299 (hybrid; bm25 7.08, cosine 0.4959)

````text
## The runs

| | Setup check | Experiment 1 (starter) | Experiment 2 (expanded) |
|---|---|---|---|
| Run folder | [`20260921T061526_247767Z`](llm_runs/20260921T061526_247767Z/) | [`20260921T061558_478156Z`](llm_runs/20260921T061558_478156Z/) | [`20260921T062609_432761Z`](llm_runs/20260921T062609_432761Z/) |
| Completed steps | 10 / 10 | **3,000 / 3,000** | **3,000 / 3,000** |
| Interrupted? | no | no | no |
| Training-loop time | 0.26 s | 16.6 s | 18.7 s |
| Parameters | 111,872 | 111,872 | 132,928 (bigger embedding table: +329 × 64) |
| Vocabulary (incl. `<UNK>` `<BOS>` `<EOS>`) | 136 | 136 | 465 |
| Unique passages → train / validation | 4,592 → 4,132 / 460 | 4,592 → 4,132 / 460 | 6,157 → 5,541 / 616 |
| Unknown-token rate, train / held-out | 0% / 0% | 0% / 0% | 0% / 0.015% (one word, *his*, occurred only in a validation passage) |
````

### [3] `raw/Custom nanoGPT LLM README.md` lines 1-13, § Building a Custom LLM with nanoGPT: Class 4 submission ← expected source
score 0.0293 (hybrid; bm25 5.609, cosine 0.5154)

````text
# Building a Custom LLM with nanoGPT: Class 4 submission

I trained Karpathy's actual nanoGPT (2 blocks, 4 heads, 64-number embeddings, 48-token
context, word tokens) from scratch **twice**, and evaluated each model on the fixed
48-case language suite before and after training:

1. **Experiment 1, starter corpus:** the notebook's synthetic classroom sentences only.
2. **Experiment 2, expanded corpus:** the same sentences plus 1,565 teaching sentences I
   wrote for four extension categories: **grammar, opposites, everyday knowledge,
   categories/analogies**.

Steps (3,000), learning rate (0.001), seed, model size and eval suite were identical, so
**the corpus is the only thing that changed**.
````

### [4] `raw/Ms Pac-Man DQN README.md` lines 157-178, § What the run actually cost ← expected source
score 0.0281 (hybrid; bm25 4.831, cosine 0.4989)

````text
### What the run actually cost

| | |
|---|---|
| Completed episodes | **800 of 800** (run completed; not interrupted) |
| Total decisions | **492,394** |
| Learning updates | **122,849** |
| Elapsed time | **4,388 seconds (~73 minutes)**, including periodic demonstrations |
| Hardware | Apple M1 Pro, 16 GB RAM, macOS 26.6.2, PyTorch **MPS** backend |
| Software | Python 3.12.14, torch 2.14.0, gymnasium 1.3.0, ale-py 0.11.2 |

This run completed normally and performed a large number of learning updates. Neither this run nor
either earlier run was interrupted, and none finished with zero learning updates.

Evidence files: **[`config.json`](results/config.json)** ·
**[`training.csv`](results/training.csv)** ·
**[`training_summary.json`](results/training_summary.json)** ·
**[`comparison.json`](results/comparison.json)** ·
**[`baseline.json`](results/baseline.json)** ·
**[`demo_scores.json`](results/demo_scores.json)**

---
````

### [5] `raw/Ms Pac-Man DQN README.md` lines 15-36, § Open and run the notebook ← expected source
score 0.0279 (hybrid; bm25 5.563, cosine 0.4656)

````text
## Open and run the notebook

**Colab:** [open `pacman_dqn.ipynb` in Google Colab](https://colab.research.google.com/github/kureemn/pacman-dqn-submission/blob/main/pacman_dqn.ipynb),
select **Runtime → Change runtime type → GPU**, then **Runtime → Run all**. The first cell installs
the packages it needs.

**Local Jupyter or VS Code:**

```sh
git clone https://github.com/kureemn/pacman-dqn-submission.git
cd pacman-dqn-submission
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m jupyter lab pacman_dqn.ipynb
```

Select a Python 3.11–3.13 kernel and choose **Run All**. CUDA, Apple Silicon MPS, and CPU are
detected automatically. Reproducing the submitted run takes about 73 minutes on an Apple M1 Pro.

The executed notebook in this repository, **[`pacman_dqn.ipynb`](pacman_dqn.ipynb)**, retains all
outputs from the final run, so the results can be inspected without rerunning anything.
````

### [6] `raw/Ms Pac-Man DQN README.md` lines 46-51, § My three choices ← expected source
score 0.0273 (hybrid; bm25 7.687, cosine 0.4452)

````text
## My three choices

| Setting | Value | Why |
|---|---|---|
| **Exploration** | `0.10` | Evaluation runs at 5% exploration, so training at 20% put the agent in a noticeably noisier world than the one it is graded in. In Ms. Pac-Man a single random step into a ghost ends a life, so a high constant epsilon both suppresses scores and pollutes replay with deaths the policy did not choose. 10% keeps genuine exploration while staying closer to evaluation conditions. Measured directly: run 2 at 0.20 scored 768; run 3 at 0.10 scored 1032. |
| **Episodes** | `800` | Training is fast on this hardware (~11 episodes/minute), so episode budget was the cheapest lever available. Earlier runs showed 100 episodes was far too short to generalize (+12 points) and 400 was still improving at the end. 800 episodes gave 122,849 learning updates — enough for the policy to consolidate rather than just track recent experience. |
````

### [7] `raw/Custom nanoGPT LLM README.md` lines 809-818, § What I learned ← expected source
score 0.0265 (hybrid; bm25 5.424, cosine 0.4568)

````text
word in only 7 sentences, and 2 of them say "two dogs **were** playing". So the model
     learned that *dogs* goes with past tense, not that *dogs* is plural, and it picked
     *was* out of is/am/was/are. The plural rule itself did get learned — "the cats" gives
     *are* at 96% — just not for a word it barely saw. Rare words don't inherit a rule.
   - **"a salmon is a" → *bird*.** On its own, the model answers this correctly: *fish* at
     0.26. The eval puts one sentence in front of it ("a robin is a bird ."), and the
     answer collapses to *farm*. The reason is in the pipeline: the notebook splits text at
     every ".", so each sentence becomes its own training passage and the model never once
     saw words continue after a period. It knows the fact and cannot use it across a
     sentence boundary. That is the single change I would make next.
````

### [8] `raw/Custom nanoGPT LLM README.md` lines 290-301, § Loss on the fixed panels ← expected source
score 0.0264 (hybrid; bm25 4.577, cosine 0.4648)

````text
### Loss on the fixed panels

Both plots use **fixed panels of 20 training and 20 validation documents**, averaging all
non-padding next-token targets. They are small estimates, not full-corpus losses, and the
two runs are **not comparable to each other**: different vocabularies mean different
starting points and different prediction problems.

| Experiment 1, starter ([`history.json`](llm_runs/20260921T061558_478156Z/history.json), [`training.csv`](llm_runs/20260921T061558_478156Z/training.csv)) | Experiment 2, expanded ([`history.json`](llm_runs/20260921T062609_432761Z/history.json), [`training.csv`](llm_runs/20260921T062609_432761Z/training.csv)) |
|---|---|
| ![Experiment 1 loss](llm_runs/20260921T061558_478156Z/training_curves.svg) | ![Experiment 2 loss](llm_runs/20260921T062609_432761Z/training_curves.svg) |

Every measured value:
````
