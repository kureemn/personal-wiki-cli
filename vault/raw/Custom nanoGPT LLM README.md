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

| Experiment | Stage | Correct / 48 | Scorable / 48 | Accuracy among scorable | Strict top‑1 / 48 ¹ | Full results |
|---|---|---|---|---|---|---|
| Starter corpus | Untrained | 9 | 24 | 37.5% | 0 | [untrained](llm_runs/20260921T061558_478156Z/language_evals/untrained/) |
| Starter corpus | Trained | **20** | 24 | 83.3% | 10 | [final](llm_runs/20260921T061558_478156Z/language_evals/final/) |
| Expanded corpus | Untrained | 11 | 36 | 30.6% | 0 | [untrained](llm_runs/20260921T062609_432761Z/language_evals/untrained/) |
| Expanded corpus | Trained | **32** | 36 | 88.9% | 14 | [final](llm_runs/20260921T062609_432761Z/language_evals/final/) |

¹ *Strict top‑1* is my extra diagnostic, not the official score. It counts a case only
when the expected word is the model's single most likely next token over the **whole**
vocabulary. The official metric only compares the four answer choices.

**Headline:** the extension made 12 more cases scorable (coverage 50% → 75%). Trained on
it, the model answered 8 of those 12 correctly, and 4 of the 8 are strict top‑1 answers.
New-wording transfer rose from 4/8 to 8/8. That is a **public development benchmark**
result, not evidence of general language ability. Several wins are narrow, and the failures
below are the most informative part of the experiment.

---

## Contents

- [Repository map](#repository-map)
- [How to run everything](#how-to-run-everything)
- [My three choices and predictions](#my-three-choices-and-predictions)
- [Corpus sources, permissions and the extension design](#corpus-sources-permissions-and-the-extension-design)
- [The runs](#the-runs)
- [Learning evidence: tokens, vectors, gradients, loss](#learning-evidence)
- [The 48 fixed language evals](#the-48-fixed-language-evals)
- [Chat interface](#chat-interface)
- [What I learned](#what-i-learned)
- [Limitation and next experiment](#limitation-and-next-experiment)

## Repository map

| Path | What it is |
|---|---|
| [`custom_llm_starter.ipynb`](custom_llm_starter.ipynb) | **Executed notebook, Experiment 1** (starter corpus). All outputs retained. |
| [`custom_llm_expanded.ipynb`](custom_llm_expanded.ipynb) | **Executed notebook, Experiment 2** (expanded corpus). All outputs retained. |
| [`make_extension_corpus.py`](make_extension_corpus.py) | Generates my teaching files in `corpus/extension/`. Never reads `evals/`. |
| [`corpus/extension/`](corpus/extension/) | The 4 teaching files (1,565 sentences) used by Experiment 2. |
| [`empty_corpus/`](empty_corpus/) | Intentionally empty folder, so Experiment 1 uses classroom sentences only. |
| [`audit_corpus.py`](audit_corpus.py) | My leakage audit (5 rules) and vocabulary-coverage prediction, run **before** training. |
| [`evals/language_evals.json`](evals/language_evals.json) | The **unchanged** 48-case suite (SHA‑256 `e8affcd7…`, verified by the notebook). |
| [`run_evals.py`](run_evals.py), [`chat.py`](chat.py) | **Unchanged** course eval runner and terminal chat interface. |
| [`analyze_results.py`](analyze_results.py) | Builds the comparison tables, strict top‑1 diagnostic, probes and embedding neighbours. |
| [`llm_runs/20260921T061558_478156Z/`](llm_runs/20260921T061558_478156Z/) + [`.zip`](llm_runs/20260921T061558_478156Z.zip) | Experiment 1 results folder and ZIP. |
| [`llm_runs/20260921T062609_432761Z/`](llm_runs/20260921T062609_432761Z/) + [`.zip`](llm_runs/20260921T062609_432761Z.zip) | Experiment 2 results folder and ZIP. |
| [`llm_runs/20260921T061526_247767Z/`](llm_runs/20260921T061526_247767Z/) | The 10‑step setup check (pipeline test only). |
| [`evidence/`](evidence/) | Comparison tables, audit report, eval reruns from saved weights, chat transcript and screenshot. |
| `nanogpt_model.py` | Unmodified nanoGPT `model.py` at commit `3adf61e` ([MIT license](NANOGPT_LICENSE)). |

**Course files, not my results:** `custom_llm.ipynb` / `custom_llm.py` (the unexecuted
starter template), `examples/` and `legacy/` (the instructor's reference runs),
`STUDENT_README.md` (the README template) and `ASSIGNMENT.md` are unchanged from the
[upstream repository](https://github.com/pepealonso95/custom-llm). The course's
maintainer tests still use them. Every result in this README comes from my `llm_runs/`
folders listed above.

## How to run everything

Local, Python 3.12 (tested on an Apple M1 Pro, CPU):

```bash
git clone https://github.com/kureemn/custom-llm-submission.git
```

```bash
cd custom-llm-submission && python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt numpy nbconvert
```

`run_evals.py` hashes weights with `.numpy()`, so NumPy is needed even though the course's
`requirements.txt` does not list it.

**Retrain either experiment** (each takes about 30 seconds; creates a new `llm_runs/<timestamp>/`):

```bash
jupyter nbconvert --to notebook --execute custom_llm_starter.ipynb --output rerun_starter.ipynb
```

```bash
jupyter nbconvert --to notebook --execute custom_llm_expanded.ipynb --output rerun_expanded.ipynb
```

You can also open either notebook in Jupyter/VS Code and choose **Run All**. The only
differences from the course notebook are the settings cell and my written prediction cell.
The starter notebook points `CORPUS_FOLDER` at `empty_corpus/`, so it still reproduces the
classroom-only run now that `corpus/` contains my extension files.

**Regenerate and re-audit the teaching corpus:**

```bash
python make_extension_corpus.py
```

```bash
python audit_corpus.py --base llm_runs/20260921T061558_478156Z/corpus.txt --output evidence/extension_corpus_audit.json
```

**Rerun the 48 evals on the saved weights** (no training; use a fresh output folder):

```bash
python run_evals.py --model llm_runs/20260921T062609_432761Z/model.pt --output results/expanded-final
```

```bash
python run_evals.py --model llm_runs/20260921T062609_432761Z/model_untrained.pt --stage untrained --output results/expanded-untrained
```

I reran all four result sets from the saved `model.pt` / `model_untrained.pt` files
([`evidence/rerun_evals/`](evidence/rerun_evals/)). **All 4 × 48 case records, including the free
continuations, were identical** to the notebook's outputs, with matching model hashes.

**Rebuild the comparison tables and diagnostics:**

```bash
python analyze_results.py
```

**Chat with the trained model:** see [Chat interface](#chat-interface).

**Embedding viewer:** open [`embedding-viewer.html`](embedding-viewer.html) locally, choose
*Open your checkpoint*, and select `checkpoint.json` from either run folder.

## My three choices and predictions

The predictions were written into each notebook's *My prediction* cell **before** it
executed. They are quoted there in full; this is a summary.

| Setting | Experiment 1 | Experiment 2 | Why |
|---|---|---|---|
| Corpus | `CORPUS="classroom"`, `CORPUS_FOLDER="empty_corpus"` | `CORPUS="classroom"`, `CORPUS_FOLDER="corpus"` (4 extension files) | A clean baseline first, then the same pipeline with added teaching data, so the corpus is the only variable. |
| Training steps | 3,000 | 3,000 | One step = one AdamW update on 32 sampled passages. 3,000 steps ≈ 96,000 passage draws, about 23 visits per training passage in Exp. 1 and about 17 in Exp. 2. That is enough for these repetitive templates. The 10-step setup run confirmed the pipeline first. |
| Learning rate | 0.001 | 0.001 | A standard AdamW size for a model this small. The notebook warms up over 100 steps, then cosine-decays to 0.0001. **Too large** (e.g. 0.05): updates overshoot the minimum, the loss oscillates or goes non-finite, and the notebook stops. **Too small** (e.g. 1e-5): weights barely move in 3,000 steps and the text stays near random. |

**What I predicted vs what happened**

| Prediction | Observed |
|---|---|
| Loss starts near ln(vocab): ln(136) ≈ 4.9, and ln(466) ≈ 6.1 in Exp. 2 | ✅ 4.926 and 6.189 |
| Loss plateaus around 0.6–0.8, not 0, because templates leave real uncertainty | ✅ 0.678 / 0.706 (Exp. 1); Exp. 2 plateaued a bit higher, 0.787 / 0.903 |
| Validation tracks training closely | ✅ Exp. 1 gap 0.028; Exp. 2 gap 0.116, because the extension sentences vary more |
| `customer`'s neighbours become the other shopper nouns | ✅ shopper, client, buyer, subscriber, consumer (cosine 0.97–0.98) |
| Exp. 1 evals: 16 starter patterns mostly correct, new wording partial, 24 extension unscorable | ✅ 16/16, 4/8, 0/24 (all unscorable) |
| Exp. 2 coverage 36/48 | ✅ exactly 36 |
| Grammar 2–3/3 | ✅ 2/3 |
| Opposites uncertain, ~1/3 | ❌ **3/3**, with high confidence. The composition worked better than I expected (see probes). |
| Knowledge: light likely; umbrella at risk; ice uncertain | ✅ 1/3 (light only). The umbrella failed, but for a different reason than I predicted. |
| Categories 1–2/3, with the cross-sentence prompt out of distribution | ✅ 2/3. Both wins are weak, and the probes confirm the cross-sentence cause. |
| Starter patterns stay at 14–16/16 | ✅ 16/16 |

## Corpus sources, permissions and the extension design

**Sources and permissions.** Experiment 1 uses only the course's generated classroom
sentences. Experiment 2 adds four UTF-8 `.txt` files that I generated with
[`make_extension_corpus.py`](make_extension_corpus.py). The files are original synthetic text,
with no third-party documents, PDFs or personal data, so they are committed here (I added
`!/corpus/extension/` to `.gitignore`). No PDFs were used, so there was no extraction to
check. [`corpus_manifest.json`](llm_runs/20260921T062609_432761Z/corpus_manifest.json) shows 4
files, 1,565 passages, 1,565 unique, **0 warnings**. The previews and
[`corpus.txt`](llm_runs/20260921T062609_432761Z/corpus.txt) contain exactly the generated
sentences.

| File | Sentences | Teaches |
|---|---:|---|
| [`grammar.txt`](corpus/extension/grammar.txt) | 627 | Agreement (*one cat is*, *two cows are*, *i am*, *yesterday the hens were*) and tense (*yesterday he walked*, *every day she walks*, *right now they are walking*) for 11 nouns and 8 verbs |
| [`opposites.txt`](corpus/extension/opposites.txt) | 600 | 17 adjective pairs in contrasts (*the soup is hot , but the tea is cold .*) and 11 pairs in "opposite" statements |
| [`everyday_knowledge.txt`](corpus/extension/everyday_knowledge.txt) | 139 | water/ice/steam, umbrellas and rain, dark rooms and light, tools and their uses, told with different people and containers |
| [`categories.txt`](corpus/extension/categories.txt) | 199 | Category membership (birds, fish, trees, tools, vegetables, fruit, vehicles, fabrics, metals) and young → adult animals |

### Why these four categories

The notebook's chunker splits text at every `. ` (`re.split(r"(?<=[.!?])\s+|\n+")`), so
**every sentence becomes its own training passage**:

```text
chunk_text("the cup is not green . it is yellow . the cup is yellow .")
→ ['the cup is not green .', 'it is yellow .', 'the cup is yellow .']
```

Negation, reference, sequence and spatial evals all depend on a fact stated in an
*earlier sentence*, such as "the box is not red . it is blue . the box is". The model never
sees tokens after a "." inside a training passage, so no teaching file can show it that
pattern without changing the pipeline. Grammar, opposites and everyday knowledge are
**single-sentence** prompts, so the pipeline *can* teach them. The starter lacks their
vocabulary entirely (*bird*, *opposite*, *water*, *umbrella*…). I added
**categories/analogies** as a deliberate probe: its prompts have two sentences, and I
predicted the model would learn the facts but fail to use them after a preceding sentence.
The [probes](#why-it-passed-or-failed-mechanism-probes) confirm this.

### Design rules: teaching the skill without copying the exam

1. **Test items only in alternate phrasings.** hot/cold, empty/full, noisy/quiet,
   water/ice, umbrella/dry, dark/light, salmon/fish, apple/fruit and kitten/cat appear only
   in contrasts, descriptions and "one kind of" sentences, never in the eval's own frame.
2. **Eval frames only with other items, and never completed with that eval's answer *or*
   distractors.** *the opposite of big is small* is taught, but no "opposite" sentence uses
   hot, cold, fast, early or soft. *to hear music we turn on a radio* is taught, but no
   *turn on* sentence ends in light, pillow, spoon or shoe. That way the teaching data cannot
   nudge any particular choice. Grammar is the one exception, because the frame *is* the rule.
   Even there, the eval's subjects never appear in the frame: no "one bird", no "the dogs",
   no "yesterday she".
3. **Small, reused vocabulary.** The notebook keeps only the 509 most frequent training
   types. My first draft had 580 combined types, so rare eval words like *robin* and
   *freezes* would have become `<UNK>`. I rewrote it around a shared lexicon: **463
   combined types**, and every eval word appears in ≥ 5 passages.

A correct answer therefore requires **combining** a frame learned from other items with a
fact learned in a different sentence shape. It cannot be recalled from the corpus.

### Leakage checks

- **Notebook (built in):** 160 generated classroom passages containing the 16 reserved
  starter prefixes were removed *before* the split and vocabulary
  ([`eval_separation.json`](llm_runs/20260921T062609_432761Z/eval_separation.json), identical
  in both runs). Every imported file and final passage passed `reject_eval_leakage`, which
  raises on any exact normalized prompt.
- **My audit** ([`audit_corpus.py`](audit_corpus.py) →
  [`evidence/extension_corpus_audit.json`](evidence/extension_corpus_audit.json)): **0
  violations** of 5 rules across all 48 cases:
  1. exact prompt;
  2. "prompt tail + answer" n‑gram (e.g. *freezes into ice*, *salmon is a fish*, *dogs are*);
  3. any complete sentence of a multi-sentence prompt (e.g. *a robin is a bird .*);
  4. 30 design phrases (e.g. *opposite of hot*, *stay dry*, *turn on the light*);
  5. frame-completion regexes for rule 2.
- **Separation of paths:** `evals/`, `llm_runs/`, `evidence/` and chat transcripts are all
  outside `corpus/`. The generator never opens `evals/`. Nothing from eval outputs or chat
  went back into training.
- **Honest limits:** these are string checks. They cannot detect every paraphrase, and the
  assignment allows underlying *facts* to overlap. My closest calls are sentences that state
  a tested fact in different words:
  - *an umbrella keeps my sister dry in the rain*
  - *the salmon is one kind of fish*
  - *a kitten is a young cat*
  - *the soup is hot , but the tea is cold*

  I also read the public tests when choosing the categories and designing the text, so this
  is a **development benchmark, not an unseen test**.
- **No tuning on scores:** the corpus was revised twice *before any training*. Both
  revisions were driven by the audit (vocabulary cap, rare words, and the stricter rule 2),
  not by eval results. **Experiment 2 was trained exactly once.**

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
| Config, summary | – | [config](llm_runs/20260921T061558_478156Z/config.json), [summary](llm_runs/20260921T061558_478156Z/training_summary.json), [vocab report](llm_runs/20260921T061558_478156Z/vocabulary_report.json), [manifest](llm_runs/20260921T061558_478156Z/corpus_manifest.json) | [config](llm_runs/20260921T062609_432761Z/config.json), [summary](llm_runs/20260921T062609_432761Z/training_summary.json), [vocab report](llm_runs/20260921T062609_432761Z/vocabulary_report.json), [manifest](llm_runs/20260921T062609_432761Z/corpus_manifest.json) |

Hardware: Apple M1 Pro (16 GB), macOS 26.6.2, Python 3.12.14, PyTorch 2.14.0, `DEVICE="cpu"`
as in the course notebook. Seed 42, batch 32, 2 layers, 4 heads, 64-dim, block size 48.

**What stayed fixed:** seed, model shape, batch size, steps, learning rate and schedule,
eval suite, loss-panel sampling seeds, sampling seed and generation settings.
**What training changed:** only the weights. **What changed only at inference:** temperature
and prompts. Neither changes any weight: the eval runner asserts the model hash is unchanged.

The split is by **deduplicated passage, not by source file**. Held-out passages reuse the
training templates, so validation loss measures new *combinations* within familiar
templates. It does not measure generalization to new templates or domains. The
vocabulary is built from training passages only. The 509-type cap was never reached
(133 / 462 types), so no training word was dropped.

## Learning evidence

### Loss on the fixed panels

Both plots use **fixed panels of 20 training and 20 validation documents**, averaging all
non-padding next-token targets. They are small estimates, not full-corpus losses, and the
two runs are **not comparable to each other**: different vocabularies mean different
starting points and different prediction problems.

| Experiment 1, starter ([`history.json`](llm_runs/20260921T061558_478156Z/history.json), [`training.csv`](llm_runs/20260921T061558_478156Z/training.csv)) | Experiment 2, expanded ([`history.json`](llm_runs/20260921T062609_432761Z/history.json), [`training.csv`](llm_runs/20260921T062609_432761Z/training.csv)) |
|---|---|
| ![Experiment 1 loss](llm_runs/20260921T061558_478156Z/training_curves.svg) | ![Experiment 2 loss](llm_runs/20260921T062609_432761Z/training_curves.svg) |

Every measured value:

| Run | Step | Training panel loss | Validation panel loss |
|---|---:|---:|---:|
| Setup check | 0 | 4.9263 | 4.9275 |
| Setup check | 5 | 4.3415 | 4.3228 |
| Setup check | 10 | 4.2076 | 4.2073 |
| **Experiment 1** | 0 | 4.9263 | 4.9275 |
| **Experiment 1** | 1,500 | 0.6821 | 0.7182 |
| **Experiment 1** | 3,000 | 0.6783 | 0.7061 |
| **Experiment 2** | 0 | 6.1895 | 6.1677 |
| **Experiment 2** | 1,500 | 0.8093 | 0.9556 |
| **Experiment 2** | 3,000 | 0.7874 | 0.9034 |

Almost all learning happened in the first half. Both runs improved only slightly between
steps 1,500 and 3,000. Validation stayed close to training, so there is no sign of
overfitting. The expanded run has the larger gap because its extension sentences are more
varied, so held-out combinations are genuinely less predictable.

### Samples: untrained, halfway, final

Same sampling seed (2026), temperature 0.8, and 4 samples at every checkpoint.

**Experiment 1** ([step 0](llm_runs/20260921T061558_478156Z/samples/step_0000.txt) ·
[step 1500](llm_runs/20260921T061558_478156Z/samples/step_1500.txt) ·
[step 3000](llm_runs/20260921T061558_478156Z/samples/step_3000.txt))

| Step | Samples |
|---|---|
| 0 | *pear professor bond doctor course harvest team physician journey checking buyer delivery traffic report the lecturer item offering and system &lt;UNK&gt; taste recommended…* · *kitchen purchase journey product question discussion journey service . nurse local* · (2 more equally random) |
| 1,500 | *our school has a question about the new educator and lesson .* · *a review of risk helped us understand the different deposit .* · *we learned about the important website during a discussion of data .* · *our school has a question about the different instructor and course .* |
| 3,000 | *our school has a question about the new educator and lesson .* · *a review of risk helped us understand the different deposit .* · *the report about the nurse explains the health in detail .* · *the consumer compared the offering after checking the price .* |

**Experiment 2** ([step 0](llm_runs/20260921T062609_432761Z/samples/step_0000.txt) ·
[step 1500](llm_runs/20260921T062609_432761Z/samples/step_1500.txt) ·
[step 3000](llm_runs/20260921T062609_432761Z/samples/step_3000.txt))

| Step | Samples |
|---|---|
| 0 | *late noisy week eat gets early physician until person system ice dentist hungry plate old fish works it cool is cats tired…* (all 4 are 32-token word salad) |
| 1,500 | *today the kitchen focused on juice and the important banana .* · *a review of delivery helped us understand the different merchandise .* · ***every day she she plays in the park .*** · *a review of juice helped us understand the local apple .* |
| 3,000 | *today the hospital focused on care and the important nurse .* · *a review of harvest helped us understand the new pear .* · ***every day she she plays outside .*** · *a review of return helped us understand the local bond .* |

**Visible change:** at step 0, 7 of the 8 samples run to the 32-token limit, because EOS
is just one of 136 (or 465) roughly equally likely tokens. By step 1,500 the model has learned where
sentences end and reproduces grammatical templates.

**Lack of change:** between 1,500 and 3,000 the samples barely change, matching the flat
loss. In Experiment 2, the duplicated subject *every day she she plays…* appears at step
1,500 **and is still there at step 3,000**. More steps did not fix it.

**What the samples don't show:** 3 of 4 samples in Experiment 2 are still classroom
sentences, because about 75% of the passages are classroom text.

### One word: text → ID → vector

From [`tokenization.json`](llm_runs/20260921T062609_432761Z/tokenization.json) and
[`inspection.json`](llm_runs/20260921T062609_432761Z/inspection.json) (Experiment 2):

```text
text     today the kitchen focused on harvest and the different apple .
tokens   today | the | kitchen | focused | on | harvest | and | the | different | apple | .
IDs      1(<BOS>) 410 402 216 151 269 177 11 402 113 13 4 2(<EOS>)
inputs → targets   <BOS>→today, today→the, the→kitchen, kitchen→focused, focused→on …
```

The probe word **`customer` is ID 102** in Experiment 2, but **ID 28** in Experiment 1.
IDs are just row numbers in an alphabetically sorted vocabulary, so adding words shifted
it. The ID carries no meaning. The meaning-bearing object is row 102 of the 465 × 64
embedding table:

| | First 8 of the 64 numbers | Length (L2 norm) |
|---|---|---:|
| Before training | −0.0164, −0.0152, −0.0228, −0.0111, 0.0204, −0.0084, −0.0057, −0.0005, … | 0.158 |
| After training | 0.0645, −0.1708, 0.1043, −0.0050, 0.0768, −0.0005, −0.1004, 0.0777, … | 0.620 |

<details><summary>All 64 numbers, before and after (Experiment 2, <code>customer</code>)</summary>

```text
before: -0.0164 -0.0152 -0.0228 -0.0111 0.0204 -0.0084 -0.0057 -0.0005 0.0172 -0.001 0.018 0.0247 0.0351 0.0048 -0.0081 -0.0038 0.0033 0.0086 0.0083 -0.0307 0.0319 0.0076 -0.0339 -0.0001 0.0135 -0.0126 0.0069 0.0271 -0.0088 -0.0234 0.0274 0.0291 0.0032 -0.015 0.0012 -0.0005 0.0021 -0.0415 0.014 -0.0491 -0.0078 -0.0036 0.0271 0.0079 0.0152 0.011 0.0299 0.0254 -0.0247 -0.0049 0.0107 0.0232 -0.0002 0.0349 0.0054 -0.0205 0.0279 0.0362 0.0149 -0.0097 -0.0298 -0.0156 0.0106 -0.0153
after:  0.0645 -0.1708 0.1043 -0.005 0.0768 -0.0005 -0.1004 0.0777 0.0781 -0.0301 0.0684 -0.0892 -0.153 -0.0293 -0.0782 0.0165 0.1106 -0.1048 -0.1471 -0.0425 0.0264 -0.0252 -0.0058 -0.0061 0.0366 0.0558 0.0392 -0.035 0.0774 0.0601 0.1334 -0.047 -0.0082 -0.0501 -0.0183 0.0362 -0.0245 0.0425 0.02 -0.0549 -0.0492 0.0331 -0.0147 0.1559 0.0763 -0.0319 0.0355 0.0517 0.0394 0.0251 0.0244 0.1066 -0.0948 -0.022 0.0676 -0.1173 -0.047 0.107 0.1863 -0.0176 0.0906 -0.1224 -0.0801 -0.1192
```
Experiment 1's vectors are in [its inspection.json](llm_runs/20260921T061558_478156Z/inspection.json).
</details>

No single coordinate means "customer-ness". What changed is the vector's **direction
relative to other words**. Cosine nearest neighbours over all 64 dimensions
([`evidence/comparison.json`](evidence/comparison.json)):

| Run | Word | Neighbours before training (random) | Neighbours after training |
|---|---|---|---|
| Exp. 1 | customer | bus 0.21, educator 0.20, helped 0.20, bank 0.20, risk 0.20 | **shopper 0.98, client 0.98, buyer 0.98, subscriber 0.97, consumer 0.97** |
| Exp. 2 | customer | play 0.37, got 0.33, pine 0.30, stove 0.29, harvest 0.29 | shopper 0.98, client 0.98, subscriber 0.98, consumer 0.97, buyer 0.97 |
| Exp. 2 | hot | dinner 0.36, is 0.32, tutor 0.32, ladder 0.32, bake 0.30 | cold 0.70, warm 0.69, full 0.68, noisy 0.61, hard 0.58 |
| Exp. 2 | walked | mortgage 0.36, for 0.32, metal 0.30, pig 0.29, returned 0.29 | painted 0.76, jumped 0.74, cleaned 0.72, cooked 0.71, climbed 0.70 |
| Exp. 2 | salmon | puppy 0.34, be 0.33, winter 0.32, paints 0.31, early 0.25 | trout 0.74, carrot 0.72, robin 0.72, tuna 0.71, bean 0.70 |
| Exp. 2 | kitten | cows 0.39, he 0.32, soft 0.30, noisy 0.30, kind 0.29 | puppy 0.79, piglet 0.67, cub 0.66, tadpole 0.65, tool 0.64 |
| Exp. 2 | dogs | order 0.36, class 0.27, girls 0.26, off 0.26, saw 0.25 | onion 0.65, two 0.63, owl 0.61, turn 0.59, horses 0.59 |

Words that appear in the same slots end up pointing the same way:
- **Customer nouns:** the five customer nouns are interchangeable in the templates, and end at 0.97–0.98 similarity.
- **Past-tense verbs** cluster together.
- **salmon** sits with trout and tuna, but also with *carrot* and *robin*. All of them are nouns used in "the X is one kind of Y", which is a reminder that the neighbours reflect **shared contexts, not biology**.
- **dogs** has muddled neighbours, because it appeared in only 7 sentences. That foreshadows its eval failure.

### One real gradient and weight update

The notebook saved coordinate 0 of `customer`'s embedding across the very first AdamW step:

| Run | Before | Gradient | Learning rate at step 1 | After | Change |
|---|---:|---:|---:|---:|---:|
| Exp. 1 | −0.0575919 | **+0.000693** | 0.00001 | −0.0576019 | −0.0000100 |
| Exp. 2 | −0.0164004 | **−0.001230** | 0.00001 | −0.0163904 | +0.0000100 |

- **The gradient** is ∂loss/∂weight on the first batch. A positive gradient says "increasing
  this number would increase the loss".
- **The step size** is 0.001 × 1/100, because warmup starts the learning rate at 1% of its peak.
- **The update moves against the gradient's sign:** down when the gradient is positive (Exp. 1), up
  when it is negative (Exp. 2).
- **The size is exactly the learning rate, even though the two gradients differ by almost
  2×.** On Adam's first step, the normalized update m̂/√v̂ equals g/|g| = ±1. So every
  parameter moves by ≈ lr regardless of gradient size. AdamW's decoupled weight decay
  (0.01 × lr × weight ≈ 6e‑9) is negligible here.
- **Plain SGD would behave differently:** lr × gradient would move this weight by only 7e‑9.

Repeat that for all 111,872 / 132,928 parameters, 3,000 times, and the vector above grows
from length 0.16 to 0.62 in a useful direction.

### Next-token probabilities for the same prefix

Prefix **`the customer`** ([`inspection.json`](llm_runs/20260921T061558_478156Z/inspection.json)):

| Run | Before training (top 5) | After training (top 6) |
|---|---|---|
| Exp. 1 | customer 0.016, bus 0.011, educator 0.010, us 0.010, application 0.010 (≈ uniform 1/136 = 0.0074) | reviewed 0.178, recommended 0.171, ordered 0.169, selected 0.163, compared 0.160, returned 0.143 |
| Exp. 2 | customer 0.004, bottle 0.003, under 0.003, compared 0.003, data 0.003 (≈ 1/465) | compared 0.202, selected 0.179, recommended 0.168, reviewed 0.149, returned 0.143, ordered 0.141 |

After training, about 98% of the probability sits on exactly the six verbs the corpus uses
after "the customer", split almost evenly (≈ 1/6 each). The corpus chooses among those
verbs at random, so no model can do better than about 1/6 here. **That is why the loss
cannot reach 0**, and why it plateaus around 0.7.

### Attention uses earlier context only

Block 1, head 1, at the last position of `the customer` (the row that predicts the next
word): Exp. 1 attends **BOS 0.485, the 0.423, customer 0.092**; Exp. 2 attends 0.385 /
0.397 / 0.218. A causal mask sets future positions to −∞ before the softmax, so each row
sums to 1 over *earlier and current* tokens only. A prediction can never see the word it is
trying to predict. The later probes show attention's power and its limit. It can reach back
to "hot" several words earlier and produce "cold". But in two-sentence prompts, it also
reaches back to the *first* sentence's category and copies it.

### Temperature changes sampling, not weights

[`temperature_comparison.json`](llm_runs/20260921T062609_432761Z/temperature_comparison.json):
same trained weights, same seed, same starting token (BOS).

| T | Experiment 2 samples |
|---|---|
| 0.3 | *the team discussed the dentist and the treatment at the hospital .* · *the report about the buyer explains the purchase in detail .* · *the important client was mentioned in the order report yesterday .* · *the important bicycle was mentioned in the travel report yesterday .* |
| 0.8 | *today the hospital focused on care and the important nurse .* · *a review of harvest helped us understand the new pear .* · *every day she she plays outside .* · *a review of return helped us understand the local bond .* |
| 1.2 | ***coffee is many up gets .*** · *a review of route helped us understand the important bus .* · *right now they are over the house .* · *one boy is happy , but the song is sad .* |

Sampling divides the logits by T before the softmax:
- **T < 1** sharpens the distribution toward the top token. At 0.3 the samples are the most
  common template, and the least varied.
- **T > 1** flattens it, so rare tokens get sampled. At 1.2 the model produced the
  ungrammatical *coffee is many up gets*.

Experiment 1's 0.8 and 1.2 samples were **identical**
([file](llm_runs/20260921T061558_478156Z/temperature_comparison.json)). Its template-only
model is so confident (often p > 0.95 per token) that flattening rarely changes which token
the fixed random draw lands on. Temperature only matters where the model is genuinely
uncertain. No weights change at any temperature.

## The 48 fixed language evals

**Scoring (unchanged course runner):**
1. Feed only the prompt to the model.
2. Compare the next-token probabilities of the four answer choices. The highest wins; a tie scores 0.
3. If any prompt or choice word is outside the vocabulary, mark the case unscorable and count it as 0.

Separately, the runner samples a free 24-token continuation at T = 0.8 with a per-case
seed. The free text is **not** what gets scored. Suite SHA‑256
`e8affcd72841e3ed7da5c0b6b116327fe9f69c9abd66a1180d1d88ceaa3e17f7` is identical in all four
[summaries](llm_runs/20260921T062609_432761Z/language_evals/final/eval_summary.json).

**All four complete result sets** (each has `eval_cases.json`, `eval_results.json`,
`eval_results.csv`, `eval_summary.json`):
[starter untrained](llm_runs/20260921T061558_478156Z/language_evals/untrained/) ·
[starter trained](llm_runs/20260921T061558_478156Z/language_evals/final/) ·
[expanded untrained](llm_runs/20260921T062609_432761Z/language_evals/untrained/) ·
[expanded trained](llm_runs/20260921T062609_432761Z/language_evals/final/).
Each run folder also has `language_eval_comparison.json`. The reruns from saved weights
are in [`evidence/rerun_evals/`](evidence/rerun_evals/).

### All-case success, scorable accuracy, coverage

| | Starter untrained | Starter trained | Expanded untrained | Expanded trained |
|---|---:|---:|---:|---:|
| All-case success | 18.8% | 41.7% | 22.9% | **66.7%** |
| Accuracy among scorable | 37.5% | 83.3% | 30.6% | **88.9%** |
| Coverage (scorable / 48) | 50% | 50% | 75% | 75% |
| Strict top‑1 (my diagnostic) | 0 | 10 | 0 | 14 |

Coverage is a property of the **vocabulary**, so training cannot change it. Both
untrained models sit near the 25% chance level among scorable cases.

### By group and category

| Group | Starter untrained | Starter trained | Expanded untrained | Expanded trained |
|---|---|---|---|---|
| starter_patterns | 6/16 (16 scorable) | **16/16** | 4/16 (16) | **16/16** |
| starter_transfer (new wording) | 3/8 (8) | 4/8 | 1/8 (8) | **8/8** |
| extend_corpus | 0/24 (0) | 0/24 (0) | 6/24 (12) | **8/24 (12)** |

| Category | Starter untrained | Starter trained | Expanded untrained | Expanded trained |
|---|---|---|---|---|
| domain_context | 3/8 | 8/8 | 1/8 | 8/8 |
| domain_place | 3/8 | 8/8 | 3/8 | 8/8 |
| new_wording | 3/8 | 4/8 | 1/8 | 8/8 |
| grammar ★ | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (3 sc.) | **2/3** |
| opposites ★ | 0/3 (0 sc.) | 0/3 (0 sc.) | 2/3 (3 sc.) | **3/3** |
| everyday_knowledge ★ | 0/3 (0 sc.) | 0/3 (0 sc.) | 1/3 (3 sc.) | 1/3 |
| categories_and_analogies ★ | 0/3 (0 sc.) | 0/3 (0 sc.) | **3/3** (3 sc.) | 2/3 |
| negation | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) |
| reference | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) |
| sequence | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) |
| spatial_relations | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) | 0/3 (0 sc.) |

★ = the categories I extended. Note the **untrained** expanded model scored 3/3 on
categories and 2/3 on opposites **by pure chance**. On 3 cases, random guessing lands at
3/3 about 1.6% of the time per category. This is why I don't read single-category
before/after differences as evidence on their own, and why I added the strict top‑1 metric
and probes.

### Every case, both trained models

P(expected) is the probability of the correct word over the whole vocabulary. "Top‑1
(rank)" is the model's actual most likely next word, with the correct word's rank in
parentheses. The free continuation is the runner's unconstrained T = 0.8 sample, shown
exactly as saved.

| Case | Category | Expected | Starter trained | Expanded trained | P(expected), expanded | Expanded top‑1 (rank of expected) | Expanded free continuation |
|---|---|---|---|---|---|---|---|
| lang_01 | domain_context | service | service ✅ | service ✅ | 0.25 | order (2) | order in detail . |
| lang_02 | domain_context | quality | quality ✅ | quality ✅ | 0.25 | price (2) | price in detail . |
| lang_03 | domain_context | payment | payment ✅ | payment ✅ | 0.21 | risk (4) | payment in detail . |
| lang_04 | domain_context | juice | juice ✅ | juice ✅ | 0.3 | juice (1) | taste in detail . |
| lang_05 | domain_context | journey | journey ✅ | journey ✅ | 0.23 | travel (3) | route in detail . |
| lang_06 | domain_context | security | security ✅ | security ✅ | 0.22 | data (4) | data in detail . |
| lang_07 | domain_context | patient | patient ✅ | patient ✅ | 0.23 | health (3) | health in detail . |
| lang_08 | domain_context | lesson | lesson ✅ | lesson ✅ | 0.26 | lesson (1) | lesson in detail . |
| lang_09 | domain_place | store | store ✅ | store ✅ | 0.97 | store (1) | store . |
| lang_10 | domain_place | market | market ✅ | market ✅ | 0.97 | market (1) | market . |
| lang_11 | domain_place | bank | bank ✅ | bank ✅ | 0.96 | bank (1) | bank . |
| lang_12 | domain_place | kitchen | kitchen ✅ | kitchen ✅ | 0.96 | kitchen (1) | kitchen . |
| lang_13 | domain_place | station | station ✅ | station ✅ | 0.95 | station (1) | station . |
| lang_14 | domain_place | office | office ✅ | office ✅ | 0.95 | office (1) | office . |
| lang_15 | domain_place | hospital | hospital ✅ | hospital ✅ | 0.96 | hospital (1) | hospital . |
| lang_16 | domain_place | school | school ✅ | school ✅ | 0.97 | school (1) | school . |
| lang_17 | new_wording | health | health ✅ | health ✅ | 0.092 | hospital (2) | hospital kitchen . |
| lang_18 | new_wording | student | harvest ❌ | student ✅ | 0.071 | wall (4) | student is low . |
| lang_19 | new_wording | return | care ❌ | return ✅ | 0.18 | interest (4) | return in . |
| lang_20 | new_wording | fruit | fruit ✅ | fruit ✅ | 1.4e-05 | kitchen (157) | market . |
| lang_21 | new_wording | route | route ✅ | route ✅ | 0.0012 | different (30) | different tutor . |
| lang_22 | new_wording | update | treatment ❌ | update ✅ | 0.0049 | office (22) | kitchen . |
| lang_23 | new_wording | support | health ❌ | support ✅ | 0.17 | service (3) | service in . |
| lang_24 | new_wording | delivery | delivery ✅ | delivery ✅ | 0.00015 | local (28) | different merchandise . |
| lang_25 | grammar | is | out of vocabulary | is ✅ | 0.94 | **is (1)** | is loud . |
| lang_26 | grammar | are | out of vocabulary | was ❌ | 0.0022 | sleep (97) | jump on a fabric . |
| lang_27 | grammar | walked | out of vocabulary | walked ✅ | 0.16 | worked (2) | jumped into the river . |
| lang_28 | opposites | cold | out of vocabulary | cold ✅ | 0.86 | **cold (1)** | cold . |
| lang_29 | opposites | full | out of vocabulary | full ✅ | 0.57 | **full (1)** | full . |
| lang_30 | opposites | quiet | out of vocabulary | quiet ✅ | 0.86 | **quiet (1)** | quiet . |
| lang_31 | negation | blue | out of vocabulary | out of vocabulary | – | – | on . |
| lang_32 | negation | milk | out of vocabulary | out of vocabulary | – | – | the on . |
| lang_33 | negation | closed | out of vocabulary | out of vocabulary | – | – | on . |
| lang_34 | reference | maya | out of vocabulary | out of vocabulary | – | – | . |
| lang_35 | reference | finn | out of vocabulary | out of vocabulary | – | – | on . |
| lang_36 | reference | omar | out of vocabulary | out of vocabulary | – | – | the kitchen . |
| lang_37 | sequence | dry | out of vocabulary | out of vocabulary | – | – | on . |
| lang_38 | sequence | breakfast | out of vocabulary | out of vocabulary | – | – | empty . |
| lang_39 | sequence | bus | out of vocabulary | out of vocabulary | – | – | . |
| lang_40 | spatial_relations | book | out of vocabulary | out of vocabulary | – | – | light was on . |
| lang_41 | spatial_relations | below | out of vocabulary | out of vocabulary | – | – | late . |
| lang_42 | spatial_relations | right | out of vocabulary | out of vocabulary | – | – | on . |
| lang_43 | everyday_knowledge | ice | out of vocabulary | wood ❌ | 1.4e-06 | the (189) | the cup to got wet in the rain . |
| lang_44 | everyday_knowledge | dry | out of vocabulary | hungry ❌ | 0.00075 | cool (117) | cool . |
| lang_45 | everyday_knowledge | light | out of vocabulary | light ✅ | 0.02 | fan (6) | fan . |
| lang_46 | categories_and_analogies | fish | out of vocabulary | bird ❌ | 0.0093 | farm (25) | cow . |
| lang_47 | categories_and_analogies | cat | out of vocabulary | cat ✅ | 0.017 | ball (10) | another . |
| lang_48 | categories_and_analogies | fruit | out of vocabulary | fruit ✅ | 0.0068 | kitchen (23) | kitchen . |

Starter-run free continuations and probabilities are in its
[`eval_results.csv`](llm_runs/20260921T061558_478156Z/language_evals/final/eval_results.csv).
Its 24 extension cases were all out of vocabulary, and its continuations read like
*"payment in detail ."* for starter prompts.

### Four-choice score vs free continuation

They often disagree, and the difference matters:
- **Starter place prompts (lang_09–16):** the right word has p ≈ 0.96, and the free text
  says it too (*"store ."*). These are real learned associations.
- **Opposites (lang_28–30):** the answer is the top token, and the free continuation is
  exactly the answer (*"cold ."*, *"full ."*, *"quiet ."*).
- **lang_20 *fruit*, lang_24 *delivery*:** counted correct, but the correct word has
  probability 1e‑5 to 1e‑4 and rank 157 and 28. The free text says *"market ."* and
  *"different merchandise ."*. The model would never actually say the answer; it just
  ranked it above three even less likely words. **In Experiment 1, three of the four
  "correct" new-wording cases were like this** (fruit, route, delivery: every choice ≈ 1e‑5).
  Only *health* (0.16) was a real win.
- **lang_45 *light*** wins 0.020 against *spoon* 0.013, but the model's real answer is
  *"fan ."*. Its training frame "to cool the room we turn on a fan" is louder than the
  dark → light fact.

### What changed, and is it vocabulary or learned patterns?

The overall change is +12 correct (20 → 32). Four different things happened:

- **+0 from starter patterns.** They stayed at 16/16 even though classroom text is now only
  about 75% of each batch.
- **+4 from new wording (4/8 → 8/8): patterns, not vocabulary.** All 8 cases were already
  scorable. In Experiment 1, 7 of the 8 had near-zero probability (≈ 1e‑5) for every
  choice. The prompts change the template's subject ("*our hospital* discussed…"), and a
  template-only model was lost. The exception was lang_17, *health* 0.16. In Experiment 2, lang_17/18/19/23 put real mass on the answer (0.07–0.18).
  *My interpretation, not proven:* the extension's varied subjects ("yesterday the girl…",
  "the farmer uses…") made the model less bound to "the team discussed". lang_20/21/22/24
  are still weak wins, and **none** of the 8 is a strict top‑1 answer in either run.
- **+8 from extension cases (0 → 8): vocabulary first, then patterns.** Coverage was
  necessary but not sufficient. The untrained expanded model had the same coverage and got
  6/12 by luck. Training made 4 of the 8 strict top‑1 answers: *is*, *cold*, *full*,
  *quiet*. Only the weights changed between those two measurements, so those 4 are learned
  patterns.
- **4 extension failures (below).** In each, the knowledge exists in the model but is tied
  to the sentence shape it was taught in.

### Why it passed or failed: mechanism probes

[`analyze_results.py`](analyze_results.py) sends extra diagnostic prompts to the trained
expanded model. These are *not* eval cases and were never trained on. Top next tokens
([`evidence/comparison.json`](evidence/comparison.json)):

| Question | Prompt | Top next tokens |
|---|---|---|
| Opposites: eval prompt | `the opposite of hot is` | **cold 0.86**, hot 0.04, quiet 0.02 |
| Same frame, reversed pair (never taught, not an eval) | `the opposite of cold is` | **hot 0.80**, full 0.04, noisy 0.01 |
| Same frame, a contrast-only pair | `the opposite of fast is` | **slow 0.37**, fast 0.16, early 0.14 |
| No contrast word at all | `the soup is hot and the tea is` | **cold 0.86**, it 0.03, quiet 0.01 |
| Categories: eval prompt | `a robin is a bird . a salmon is a` | farm 0.18, kitchen 0.05, rain 0.04, park 0.03, bird 0.03 |
| Final clause alone | `a salmon is a` | **fish 0.26**, vegetable 0.18, bird 0.12 |
| Categories: eval prompt | `a carrot is a vegetable . an apple is a` | kitchen 0.26, tree 0.14, house 0.06 |
| Final clause alone | `an apple is a` | **fruit 0.74**, juice 0.06, taste 0.05 |
| Final clause alone | `a kitten grows into a` | tree 0.06, cup 0.05, dark 0.04 |
| Grammar: eval prompt | `the dogs` | sleep 0.09, were 0.08, focused 0.04, was 0.03 |
| Another subject with dogs | `two dogs` | **were 0.76**, are 0.05 |
| A trained plural | `the cats` | **are 0.96** |
| Knowledge: eval prompt | `water freezes into` | **the 0.97**, a 0.01 |
| Taught fact shape | `when the water in the cup gets very cold , it becomes` | **ice 0.97** |
| Knowledge: eval prompt | `a person uses an umbrella to stay` | cool 0.42, warm 0.13 |
| Taught fact shape | `an umbrella keeps the girl` | **dry 0.42** |

What this shows:

- **Opposites passed through real composition, but not "understanding".** The
  "the opposite of X is" frame was never taught with hot/cold. Yet the model answers
  cold, and it transfers to pairs it never saw in the frame (cold → hot, fast → slow).
  However, *"the soup is hot **and** the tea is"* also gives **cold 0.86**. The model
  learned "after *is*, produce the contrast partner of an earlier adjective". It ignores
  whether the sentence says *but*, *and* or *opposite*.
- **Category failure = cross-sentence context (the chunker).** The model *knows* salmon is
  a fish (0.26) and apple is a fruit (0.74) when asked in one sentence. The same question
  after a preceding sentence collapses to *farm* and *kitchen*. It has never seen a passage
  continue after a ".". The two "correct" category answers are weak wins (p = 0.017,
  0.007). And *kitten grows into a* fails even alone, because *cat* was never a
  "grows into a" completion (rule 2) and the model did not transfer kitten → cat into
  that frame.
- **"the dogs" failed because of how I constrained the data.** To avoid leakage, "dogs"
  never followed "the" and never preceded "are", so it appeared in only 7 sentences. Two of
  those are "two dogs **were** playing" and "many dogs **were** running". The model learned
  dogs ↔ *past tense* (were 0.76), so among is/am/was/are it picked the past form **was**.
  The plural rule transferred to a well-represented noun (*the cats* → are 0.96) but not to
  a rare one. This is a real side effect of my own leakage rules.
- **Knowledge failures: the facts are learned, but bound to the taught shape.** The water
  fact works in its taught form (*ice 0.97*). But "water freezes into" → **the** 0.97,
  because the grammar file contains "**into the**" 36 times ("jumped into the lake"),
  and that frame dominates. Likewise *an umbrella keeps the girl* → **dry**, while "…to stay" → cool/warm,
  because the tools frame taught *stay warm / stay cool*.

**Conclusion:** coverage was the gate. After that, the model succeeded exactly when the
eval's wording matched a mechanism it had learned (contrast partner, agreement for common
nouns). It failed when the wording triggered a different, more frequent frame, or needed
cross-sentence context. More training steps would not fix these failures. Changing the
data (and the chunker) would.

## Chat interface

**Launch** (after the setup in [How to run everything](#how-to-run-everything)):

```bash
python chat.py --model llm_runs/20260921T062609_432761Z/model.pt --transcript results/my-chat.json
```

Type a prompt, get a continuation, type another. `/quit` exits and saves the transcript.
This is the course's unchanged [`chat.py`](chat.py). It loads `model.pt`, which contains
the full weights *and* the saved vocabulary, so it runs the trained nanoGPT itself. There
is no external API and no canned text. The notebooks' section 10 is a second interface:
each executed notebook contains one real notebook chat turn (*"the customer"* → *"compared
the item after checking the price ."* for Experiment 2).

**Model identity:** Experiment 2, run `20260921T062609_432761Z`, 3,000 completed steps,
model SHA‑256 `d35055b7c9a186947b5245a4eeec76c1e58375af1c5891aa0b8c22026bd043cc`. The same
hash is recorded in the transcript and in the eval summary.

**Evidence:** two saved sessions with the same model.

1. **[`chat_transcript_typed_20260922_170005.json`](evidence/chat/chat_transcript_typed_20260922_170005.json)
   — the session I typed myself** (7 turns), shown in the screenshot below and in the table.
2. [`chat_transcript.json`](evidence/chat/chat_transcript.json) — a 6-turn scripted session
   driven by [`chat_demo.exp`](evidence/chat/chat_demo.exp), so it reproduces exactly. Its
   replies were generated live by the same weights.

Temperature is 0.8 in both, and turn *n* uses seed 2026 + *n*.

![Terminal chat session with the trained model](evidence/chat/chat_terminal_screenshot.png)

*The screenshot shows the scripted replay of session 1, because the original window had
already scrolled past the conversation. The replay sends the same prompts in the same
order, so `chat.py` uses the same seeds and every reply is identical to the typed
transcript, line for line. Both files are linked above.*

| # | My prompt | Model reply | What it shows |
|---|---|---|---|
| 1 | Do you know how I am? | day . | **Limitation.** 5 of 6 words are outside the 465-word vocabulary (`?, do, how, know, you`), so the model saw `<UNK> <UNK> <UNK> <UNK> i <UNK>` and had nothing to continue. |
| 2 | I'm a little confused | yesterday i walk played in the park . | **Limitation.** With only *a* known, it fell back to its most common sentence shape, and even that is ungrammatical (*walk played*). |
| 3 | What is the capital of NY? | . | **Limitation.** It is not a question answerer and holds no world facts. It knew only *is, the, of* and emitted an immediate end of sentence. |
| 4 | the customer | recommended the merchandise after checking the price . | A starter template reproduced correctly |
| 5 | the opposite of cold is | hot . | Correct on a pair never taught in that frame |
| 6 | one cat is | eating . | The agreement rule: singular subject → *is*, then a plausible state |
| 7 | the soup is hot , but the tea is | cold . | The contrast pattern, its most confident behaviour (cold at 92%) |

Turns 1–3 are the honest failure cases: this model is a next-word continuer with a
465-word vocabulary trained for 19 seconds, not an assistant. Turns 4–7 show it working on
text shaped like its training data. The scripted transcript adds one more instructive
failure: *a sparrow is a bird . a trout is a* → **vegetable**, although *a trout is a* alone
gives fish 0.20. That is the cross-sentence limitation again.

Every prompt starts fresh. There is no memory between turns, and prompts longer than 48
tokens keep only the most recent 48. Chatting never updates weights or writes to the corpus.

## What I learned

> My own answers, with the values from my two runs as support.

1. **What my corpus can teach, and why I held data back.** My corpus is the passages I
   trained on: 6,157 short sentences, 4,592 generated by the notebook and 1,565 I wrote
   myself. What it really teaches the model is **which words follow which** — the
   associations between words. It can't teach anything I didn't write down, and it can't
   use a word outside the 465 in its vocabulary. That shows up directly in the evals: 12 of
   the 48 cases couldn't even be scored, because their words never appear in my text. I
   held 10% of the passages back because **training loss only tells me how well the model
   fits sentences it has already seen**. The held-out passages never produced a gradient,
   so the fact that they score close to the training ones (0.903 vs 0.787) tells me it
   learned the patterns instead of memorizing individual sentences. It is still a weak
   test, because my held-out sentences reuse the same templates as the training ones.
2. **Token, ID, vector, embedding.** The token is the piece of text itself, like
   *customer*. The **ID tells the model which row to look up** — it is just an address. The
   vector is the 64 numbers stored in that row, and the embedding table is all 465 rows of
   them. My clearest evidence that the ID means nothing on its own: *customer* was ID 28 in
   Experiment 1 and ID 102 in Experiment 2. Same word, different row number, because I
   added words earlier in the alphabet. The numbers in the row are what carry the meaning,
   and those are what training changed: the vector grew from length 0.158 to 0.620, and its
   closest neighbours went from random words to *shopper, client, buyer*.
3. **Why it's a neural network, and how it learned.** It is a neural network because it is
   built from layers of **weighted sums**, and those weights are **learned from the data**
   rather than written by me — 132,928 of them here. Training is a loop: the model predicts
   what comes next, the loss says how wrong that prediction was, and the weights change a
   little to make better predictions next time. In numbers: the loss started at 6.19, which
   is just guessing (ln 465 ≈ 6.14), and ended at 0.79. The first update I saved shows one
   step of the loop: the gradient on `customer[0]` was +0.000693, and the weight moved
   −0.00001, against the gradient's direction. Repeat that for every weight, 3,000 times.
4. **What attention combines, and why it can't see ahead.** The model's whole job is
   predicting the next word, so **it can't be allowed to see that word** — if it could, there
   would be nothing to learn and the loss would go to zero without the model understanding
   anything. What it can do is look back. A word's meaning depends on what came before it,
   so attention looks at the earlier words to get context. At the last position of
   `the customer`, the first head puts 0.485 on `<BOS>`, 0.423 on *the* and 0.092 on
   *customer* — it is reading the earlier words, and the causal mask blocks everything
   after.
5. **How probabilities become text, and what temperature does.** The model writes **one
   word at a time**. At each step it produces a probability for every word that could come
   next, one is picked, added to the sentence, and the process repeats. Temperature shapes
   how that pick is made: **low is repetitive, high is more random**. At 0.3 my model wrote
   only its most common templates; at 1.2 it wrote *coffee is many up gets .* Nothing was
   retrained between those samples — same weights, same seed, only the sampling changed.
6. **Did it match my predictions, and what can I honestly conclude?** My conclusion is that
   **this small model learns the patterns that are in the data I gave it, and is mostly
   matching what it has seen**. Most of my predictions held: the losses, the neighbours of
   *customer*, the vocabulary coverage (36/48) and grammar all landed where I expected.
   Two surprises: opposites scored 3/3 when I predicted about 1/3, and the everyday
   knowledge cases failed for a different reason than I guessed — the model had learned the
   facts, but only in the sentence shape I taught them in. So a 66.7% score is not evidence
   that this model understands language. It is a public benchmark I could read while
   designing the corpus, on a model that answers well only when the wording matches what it
   was trained on.
7. **Two failures I can explain, and what they taught me.**
   - **"the dogs" → *was*.** This one is my own doing. To keep the test out of my training
     data, I never let "dogs" follow "the" and never let "are" follow "dogs". That left the
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

## Limitation and next experiment

**Observed limitation:** the model cannot use information from an earlier sentence. The
cause is the pipeline, not model capacity: `chunk_text` turns every sentence into its own
passage. The model knows *a salmon is a* → fish and *an apple is a* → fruit. It even
generalizes *a trout is a* → fish from a sentence it never trained on. Yet all three break
as soon as another sentence comes first. The same limitation is why negation, reference,
sequence and spatial remain 0/12, as unscorable (and unteachable) cases.

**Proposed next experiment:** change one thing, the chunker. Pack consecutive sentences
from the same line into one passage, up to 47 tokens, and only split at line breaks. The
classroom corpus is one sentence per line, so its passages would be byte-identical. Then:
- add multi-sentence teaching stories for negation and reference (*"the cup is not green
  . it is yellow . the cup is yellow ."*, with different objects from the evals);
- give *dogs* ordinary present-tense plural contexts ("many dogs play", "some dogs sleep");
- rerun the same 48 cases.

**Prediction:** the two-sentence category cases should recover to the one-sentence
probabilities (fish/fruit as top‑1), negation and reference should become scorable, and
some should become correct. The model is still small, so I would expect the
correction-pattern cases to be harder than simple recall.
