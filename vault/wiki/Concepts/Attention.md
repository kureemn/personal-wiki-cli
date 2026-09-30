---
type: concept
description: Attention mechanisms allow a model to weigh the importance of different parts of the input sequence when processing a token.
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:34:45-07:00"
reviewed: true
reviewed_at: "2026-09-29"
definition_source: model general knowledge (not from sources)
---
# Attention

**General definition** *(written by Gemma from general knowledge, not taken from my sources)*: Attention mechanisms allow a model to weigh the importance of different parts of the input sequence when processing a token.

## In my projects

<!-- from:custom-nanogpt-llm-readme -->
- [[Custom nanoGPT LLM]]: The model's attention mechanism was analyzed to show it only attends to earlier and current tokens. (source: [[Custom nanoGPT LLM README#Attention uses earlier context only|Attention uses earlier context only]])
<!-- /from:custom-nanogpt-llm-readme -->

## Related concepts

Added during review. Each link says why the two ideas are connected in my projects.

- [[Language Model]]: Attention is how the model uses earlier words as context to predict the next word; the causal mask blocks later words. (source: [[Custom nanoGPT LLM README#What I learned|What I learned]])
- [[Embedding Vector]]: Both are parts of the same nanoGPT model: embeddings turn token IDs into vectors, attention combines information from earlier positions. (source: [[Custom nanoGPT LLM README#What I learned|What I learned]])

## Source

Each line above links to the section of the original document it came from. See [[Source Catalog]].
