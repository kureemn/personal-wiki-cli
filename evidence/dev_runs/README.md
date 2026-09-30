# Development runs (internet was reachable; kept to show what changed)

These ran on the same Mac with the same local model while I was building the harness. The
Wi-Fi was on (each card records `Internet during run: reachable`), but every model call went
to the local Ollama server; there is no online mode. The **graded offline results** are in
[`../offline/`](../offline/).

| Run | Harness state | Test 1 | Test 2 | Test 3 | Test 4 (unanswerable) |
|---|---|---|---|---|---|
| [run1](run1/) | hybrid retrieval, single answer call | pass | pass | pass | **FAIL**: answered "mean score 1032.0" for a *grade* question ([card](run1/test4.md)) |
| [run2](run2/) | + answer-check call (`prompts/answer-check.md`) | pass | pass | pass | pass: INSUFFICIENT EVIDENCE, rejected draft shown ([card](run2/test4.md)) |

Run 1 and run 2 cards were rendered by the harness version of that time (run 1 has no
answer-check section because that step did not exist yet).
