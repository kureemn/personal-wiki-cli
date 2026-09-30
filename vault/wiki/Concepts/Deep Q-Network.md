---
type: concept
description: A type of reinforcement learning algorithm that uses a neural network to estimate the optimal action-value function (Q-value).
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T16:30:26-07:00"
reviewed: true
reviewed_at: "2026-09-29"
definition_source: model general knowledge (not from sources)
---
# Deep Q-Network

**General definition** *(written by Gemma from general knowledge, not taken from my sources)*: A type of reinforcement learning algorithm that uses a neural network to estimate the optimal action-value function (Q-value).

## In my projects

<!-- from:ms-pac-man-dqn-readme -->
- [[Ms Pac-Man DQN]]: The agent uses a convolutional network to estimate the future value of each of the nine moves. (source: [[Ms Pac-Man DQN README#How the agent works, in plain language|How the agent works, in plain language]])
<!-- /from:ms-pac-man-dqn-readme -->

## Related concepts

Added during review. Each link says why the two ideas are connected in my projects.

- [[Replay Memory]]: The network is trained on batches of 32 experiences sampled from replay memory. (source: [[Ms Pac-Man DQN README#How the agent works, in plain language|How the agent works, in plain language]])
- [[Exploration]]: The agent mostly picks its highest-valued move and occasionally moves at random; exploration sets how often. (source: [[Ms Pac-Man DQN README#How the agent works, in plain language|How the agent works, in plain language]])
- [[PyTorch]]: The Pac-Man DQN was trained with PyTorch on the Apple M1 Pro's MPS backend. (source: [[Ms Pac-Man DQN README#What the run actually cost|What the run actually cost]])

## Source

Each line above links to the section of the original document it came from. See [[Source Catalog]].
