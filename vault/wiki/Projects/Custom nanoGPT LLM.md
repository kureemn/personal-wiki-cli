---
type: project
description: "Karpathy's nanoGPT trained from scratch twice (starter vs expanded corpus): 20/48 vs 32/48 on a fixed language eval suite."
source_id: custom-nanogpt-llm-readme
source_file: raw/Custom nanoGPT LLM README.md
source_sha256: 8b446fde420117d6ea89ca726779fd0d642a723d0b987d75ba1c8eabd83fe9e8
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:39:06-07:00"
reviewed: true
reviewed_at: "2026-09-29"
---
# Custom nanoGPT LLM

The author trained nanoGPT twice using a starter and an expanded corpus, evaluating performance on a fixed 48-case language suite. The expanded corpus, containing 1,565 synthetic teaching sentences, improved performance significantly, particularly in new wording transfer. Analysis shows the model learns patterns but is constrained by its training pipeline, especially regarding cross-sentence context.

## Key facts

- The model was trained twice using nanoGPT with 2 blocks, 4 heads, 64-number embeddings, and 48-token context. (source: [[Custom nanoGPT LLM README#Building a Custom LLM with nanoGPT Class 4 submission|Building a Custom LLM with nanoGPT: Class 4 submission]])
- Experiment 2 used an expanded corpus containing the starter sentences plus 1,565 teaching sentences across four extension categories. (source: [[Custom nanoGPT LLM README#Building a Custom LLM with nanoGPT Class 4 submission|Building a Custom LLM with nanoGPT: Class 4 submission]])
- The expanded corpus resulted in an accuracy among scorable of 88.9% when trained, compared to 30.6% untrained. (source: [[Custom nanoGPT LLM README#Building a Custom LLM with nanoGPT Class 4 submission|Building a Custom LLM with nanoGPT: Class 4 submission]])
- The model's vocabulary for Experiment 2 contained 465 unique tokens. (source: [[Custom nanoGPT LLM README#The runs|The runs]])
- The author's audit showed 0 violations of 5 rules across all 48 cases regarding data leakage. (source: [[Custom nanoGPT LLM README#Leakage checks|Leakage checks]])
- The model's attention mechanism is causal, meaning it only attends to earlier and current tokens. (source: [[Custom nanoGPT LLM README#Attention uses earlier context only|Attention uses earlier context only]])
- Training grew the length of the 'customer' embedding vector from 0.158 to 0.620. (source: [[Custom nanoGPT LLM README#One word text → ID → vector|One word: text → ID → vector]])
- New-wording transfer (`starter_transfer`) rose from 4/8 with the starter corpus to 8/8 with the expanded corpus. (source: [[Custom nanoGPT LLM README#By group and category|By group and category]])

## Concepts and tools used

- [[Language Model]]: The nanoGPT model was used to predict the next token based on the input prefix.
- [[Attention]]: The model's attention mechanism was analyzed to show it only attends to earlier and current tokens.
- [[Embedding Vector]]: The meaning-bearing object is the vector stored in the embedding table, which training changed.
- [[Learning Rate]]: The learning rate was set to 0.001, which was a standard AdamW size for this small model.
- [[nanoGPT]]: The author trained Karpathy's actual nanoGPT from scratch for this submission.
- [[PyTorch]]: Training ran on PyTorch 2.14.0 with `DEVICE="cpu"` (added during review).

<!-- related:start -->
## Related projects

- [[Ms Pac-Man DQN]]: also uses [[Learning Rate]], [[PyTorch]]
<!-- related:end -->

## Source

- Original document: [[Custom nanoGPT LLM README]] (`raw/Custom nanoGPT LLM README.md`, kept unchanged)
- All sources: [[Source Catalog]]
