---
type: concept
description: "A buffer used in reinforcement learning to store past experiences, allowing the agent to sample data randomly for training."
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:30:26-07:00"
reviewed: true
reviewed_at: "2026-09-29"
definition_source: model general knowledge (not from sources)
---
# Replay Memory

**General definition** *(written by Gemma from general knowledge, not taken from my sources)*: A buffer used in reinforcement learning to store past experiences, allowing the agent to sample data randomly for training.

## In my projects

<!-- from:ms-pac-man-dqn-readme -->
- [[Ms Pac-Man DQN]]: Experiences go into a replay memory, and batches of 32 are sampled from it to adjust the network. (source: [[Ms Pac-Man DQN README#How the agent works, in plain language|How the agent works, in plain language]])
<!-- /from:ms-pac-man-dqn-readme -->

## Related concepts

Added during review. Each link says why the two ideas are connected in my projects.

- [[Deep Q-Network]]: Replay memory supplies the training batches for the Deep Q-Network. (source: [[Ms Pac-Man DQN README#How the agent works, in plain language|How the agent works, in plain language]])

## Source

Each line above links to the section of the original document it came from. See [[Source Catalog]].
