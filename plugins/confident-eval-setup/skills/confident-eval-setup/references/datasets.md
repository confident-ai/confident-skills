# Datasets

A dataset is a set of **goldens**: the test cases Confident AI sends through
the AI connection. Each dataset is either single-turn or multi-turn, decided by
its first goldens.

## Golden Fields

Single-turn goldens (one input, one answer):

| Field | Required | What it is |
| --- | --- | --- |
| `input` | Yes | What the end user sends the app. |
| `expectedOutput` | No | The ideal answer, for correctness-style metrics. |
| `context` | No | Ground-truth facts the answer should rely on (list of strings). |
| `expectedTools` | No | The tools an agent should call. |
| `additionalMetadata` | No | Any object, available to the payload as `golden.additional_metadata`. |
| `customColumnKeyValues` | No | String columns, e.g. `{ "category": "billing" }`. |
| `tags` | No | Labels for filtering. |

Multi-turn goldens (a conversation Confident AI simulates):

| Field | Required | What it is |
| --- | --- | --- |
| `scenario` | Yes | The situation the simulated user is in and what they want. |
| `expectedOutcome` | No | How the conversation should end. |
| `userDescription` | No | Who the simulated user is. |
| `turns` | No | Opening turns, each `{ "role": "user" \| "assistant", "content": "..." }`. |
| `context` | No | Ground-truth facts. |

Don't send `actualOutput`: the AI connection generates it on each run.

## Building Goldens From the User's Files

- **CSV:** map columns by meaning, not name. A `question`, `prompt`, or `query`
  column becomes `input`; `answer`, `expected`, or `ground_truth` becomes
  `expectedOutput`. Other columns go in `customColumnKeyValues`. Ask when a
  column's meaning is unclear.
- **JSON / JSONL:** map each object the same way.
- **No file:** draft goldens with the user from the app's purpose, and keep
  them few (10–20) and varied, covering the main tasks and a few edge cases.
  Never present drafted goldens as real user data.

Show the user the goldens before pushing.

## `push_dataset`

```json
{
  "alias": "support-faq",
  "finalized": true,
  "goldens": [
    {
      "input": "How do I reset my password?",
      "expectedOutput": "Go to Settings → Security and choose Reset password."
    }
  ]
}
```

- `alias` is unique in the project. A new alias creates the dataset; an
  existing one gets the goldens appended.
- Every golden in one call must be the same kind, and match an existing
  dataset's kind.
- `finalized: true` marks every golden in the call ready to evaluate. Only
  finalized goldens are evaluated from the dataset page.
- A golden with an `id` (from `pull_dataset`) updates that golden instead of
  adding a new one.
- The response includes the dataset's `id` and its `link` on the platform.
  Give the user that link.
