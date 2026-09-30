---
type: project
description: "A Deep Q-Network trained to play ALE/MsPacman-v5, achieving a mean score of 1032.0."
source_id: ms-pac-man-dqn-readme
source_file: raw/Ms Pac-Man DQN README.md
source_sha256: 877f75d540bf2334255e2e68c5a7eec8d9b04fa11aac3b13a35d37950704d5c2
generated_by: "gemma4:e4b-it-q4_K_M"
generated_at: "2026-09-29T17:05:44-07:00"
reviewed: false
---
# Ms Pac-Man DQN

The submitted run trained the DQN agent for 800 episodes, more than doubling the mean score of the untrained baseline from 492.0 to 1032.0. The agent learns by observing stacked grayscale images and receiving rewards based on in-game points. Key tuning involved setting Exploration to 0.10 and increasing Replay Capacity to 15,000.

## Key facts

- The submitted run trained for 800 episodes and more than doubled the mean score of the untrained baseline. (source: [[Ms Pac-Man DQN README#Ms. Pac-Man DQN — Class 3 submission|Ms. Pac-Man DQN — Class 3 submission]])
- Mean score over the five evaluation games for the trained agent was 1032.0, compared to 492.0 for the untrained baseline. (source: [[Ms Pac-Man DQN README#Ms. Pac-Man DQN — Class 3 submission|Ms. Pac-Man DQN — Class 3 submission]])
- The chosen Exploration value was 0.10 to keep genuine exploration while staying closer to evaluation conditions. (source: [[Ms Pac-Man DQN README#My three choices|My three choices]])
- The Learning rate was kept at 0.0001, as raising it on an unstable setup generally makes it worse. (source: [[Ms Pac-Man DQN README#My three choices|My three choices]])
- REPLAY_CAPACITY was increased from 5,000 to 15,000 because a 5,000-transition buffer held barely 8 games. (source: [[Ms Pac-Man DQN README#My three choices|My three choices]])
- The mean update loss rose from 0.02 to about 0.14 and plateaued, reflecting the scale of what is being learned. (source: [[Ms Pac-Man DQN README#What I expected, and what actually happened|What I expected, and what actually happened]])
- The mean score across five seeds improved by 540.0, with seed 2 (202) improving by 910. (source: [[Ms Pac-Man DQN README#All five evaluation scores|All five evaluation scores]])
- The run took 4,388 seconds (~73 minutes) on an Apple M1 Pro using the PyTorch MPS backend. (source: [[Ms Pac-Man DQN README#What the run actually cost|What the run actually cost]])

## Concepts and tools used

- [[Deep Q-Network]]: The agent uses a convolutional network to estimate the future value of each of the nine moves.
- [[Replay Memory]]: Experiences go into a replay memory, and batches of 32 are sampled from it to adjust the network.
- [[Exploration]]: Training at 20% exploration put the agent in a noticeably noisier world than the one it is graded in.
- [[Learning Rate]]: The learning rate was kept at the notebook's reference value of 0.0001.
- [[PyTorch]]: The run utilized the PyTorch MPS backend on the Apple M1 Pro hardware.

<!-- related:start -->
<!-- related:end -->

## Source

- Original document: [[Ms Pac-Man DQN README]] (`raw/Ms Pac-Man DQN README.md`, kept unchanged)
- All sources: [[Source Catalog]]
