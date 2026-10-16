# Project Resources

The resources a project holds: prompts, datasets, traces, spans, threads,
metrics, test runs, evaluations, and the rest. Every method here needs a
**Project API Key** (`CONFIDENT_PROJ_API_KEY`). See `references/quickstart.md`
to create a client.

Each operation is shown for both Python and TypeScript — use the code block
matching your project.

Every resource client follows the same shape: `list()`, `get(id)`,
`create(...)`, `update(id, ...)`, `delete(id)`, plus whatever the resource
adds. A `list()` returns an envelope whose rows sit on a named field.

## Prompts

`client.prompts` works by id; `client.prompt(id)` is a handle that holds the id
and the pulled commit.

### Pull a prompt

`pull()` fills the handle from one commit and returns it. Choose the commit with
at most one of `commit`, `version` or `label`; `branch` narrows a commit lookup.

The pulled commit is **cached on disk and re-pulled in the background every
`refresh` seconds** (60 by default), so editing a prompt on Confident AI reaches
a running process without a deploy. Pass `refresh=0` to turn the cache and the
refresh off together, which is what you want while iterating on the prompt.

```python
prompt = client.prompt("<PROMPT-ID>")

prompt.pull(label="production")          # by label
prompt.pull(version="00.00.01")          # by version
prompt.pull(commit="bab04ce")            # by commit hash
prompt.pull()                            # latest commit on main
prompt.pull(refresh=0)                   # always hit the API

print(prompt.alias, prompt.hash, prompt.type)
```

```typescript
const prompt = client.prompt("<PROMPT-ID>");

await prompt.pull({ label: "production" });
await prompt.pull({ version: "00.00.01" });
await prompt.pull({ commit: "bab04ce" });
await prompt.pull();
await prompt.pull({ refresh: 0 });

console.log(prompt.alias, prompt.hash, prompt.type);
```

### Interpolate

Renders the pulled template with your variables, without calling the API.
Returns a string for a text prompt and a list of messages for a messages prompt.

```python
text = prompt.interpolate(name="Joe", product="Confident AI")
```

```typescript
const text = prompt.interpolate({ name: "Joe", product: "Confident AI" });
```

### Push a new commit

Set the template on the handle, then push. `alias` identifies the prompt and is
created if it does not exist. Send `text` or `messages`, never both.

```python
from confident_ai.common.types import PromptType
from confident_ai.prompts import PromptInterpolationType

prompt = client.prompt(alias="greeting")
prompt.text = "Hello {name}, welcome to {product}"
prompt.type = PromptType.TEXT
prompt.interpolation_type = PromptInterpolationType.FSTRING

pushed = prompt.push()
print(pushed.prompt_id, pushed.hash)
```

```typescript
import { PromptType } from "confident-ai/common";
import { PromptInterpolationType } from "confident-ai/prompts";

const prompt = client.prompt(undefined, { alias: "greeting" });
prompt.text = "Hello {name}, welcome to {product}";
prompt.type = PromptType.TEXT;
prompt.interpolationType = PromptInterpolationType.FSTRING;

const pushed = await prompt.push();
console.log(pushed.promptId, pushed.hash);
```

### Versions, commits and branches

```python
prompts = client.prompts.list()          # rows on `.prompts`

prompt.list_versions()                   # rows on `.versions`
prompt.list_commits(branch="experiment") # rows on `.commits`
prompt.list_branches()                   # rows on `.branches`

branch = prompt.create_branch("experiment")
prompt.push(branch="experiment")
prompt.update_branch(branch.id, "experiment-v2")
prompt.delete_branch(branch.id)

prompt.create_version()                  # release the head commit of main
prompt.create_version(hash="bab04ce")     # release a specific commit
```

```typescript
const prompts = await client.prompts.list();

await prompt.listVersions();
await prompt.listCommits("experiment");
await prompt.listBranches();

const branch = await prompt.createBranch("experiment");
await prompt.push({ branch: "experiment" });
await prompt.updateBranch(branch.id, "experiment-v2");
await prompt.deleteBranch(branch.id);

await prompt.createVersion();
await prompt.createVersion("bab04ce");
```

## Datasets

A dataset holds **goldens** — single-turn (carrying `input`) or multi-turn
(carrying `scenario`). Every golden in one dataset is of the same kind, decided
by the dataset's `multi_turn`.

### Pull, edit, push

`push()` **upserts**: a golden carrying an `id` is updated in place, one without
an `id` is created. So the round trip is pull, edit the list, push.

```python
from confident_ai.datasets import SingleTurnGolden

dataset = client.dataset("<DATASET-ID>").pull()
print(dataset.alias, len(dataset.goldens))

dataset.goldens[0].expected_output = "Paris, France"      # updated in place
dataset.goldens.append(
    SingleTurnGolden(input="What is the capital of Peru?", expectedOutput="Lima")
)                                                          # created
dataset.push()
```

```typescript
import { SingleTurnGolden } from "confident-ai/datasets";

const dataset = await client.dataset("<DATASET-ID>").pull();
console.log(dataset.alias, dataset.goldens!.length);

(dataset.goldens![0] as SingleTurnGolden).expectedOutput = "Paris, France";
dataset.goldens!.push({
  input: "What is the capital of Peru?",
  expectedOutput: "Lima",
});
await dataset.push();
```

`pull(version=...)` pulls a specific version, and `pull(finalized="false")`
pulls the goldens still awaiting review instead of the finalized ones.

### One golden at a time

```python
dataset.get_golden("<GOLDEN-ID>")
dataset.create_golden(SingleTurnGolden(input="What is the capital of Chile?"))
dataset.update_golden(dataset.goldens[0])   # the golden carries its own id
dataset.delete_golden("<GOLDEN-ID>")
```

```typescript
await dataset.getGolden("<GOLDEN-ID>");
await dataset.createGolden({ input: "What is the capital of Chile?" });
await dataset.updateGolden(dataset.goldens![0]);
await dataset.deleteGolden("<GOLDEN-ID>");
```

### Versions and evaluation

```python
datasets = client.datasets.list()        # rows on `.datasets`
dataset.list_versions()                  # rows on `.versions`
dataset.create_version()

run = dataset.run_evaluation(
    "Answer Quality", identifier="Nightly", prompt_alias="greeting"
)
```

```typescript
const datasets = await client.datasets.list();
await dataset.listVersions();
await dataset.createVersion();

const run = await dataset.runEvaluation("Answer Quality", {
  identifier: "Nightly",
});
```

## Traces, Spans and Threads

A trace is one request through your application; spans are the steps inside it;
a thread groups traces into a conversation. These are usually written by a
tracing SDK and read back here.

All three list with **cursor pagination**: pass `page_size`, then the `cursor`
from the previous page.

```python
from confident_ai.common import Environment

traces = client.traces.list(page_size=25, environment=Environment.PRODUCTION)
for trace in traces.traces:
    print(trace.uuid, trace.name, trace.status)

next_page = client.traces.list(page_size=25, cursor=traces.next_cursor)

trace = client.traces.get("<TRACE-UUID>")
span = client.spans.get("<SPAN-UUID>")
thread = client.threads.get("<THREAD-ID>")

# Narrow spans by what they are and what they used
from confident_ai.common import SpanType

llm_spans = client.spans.list(
    type=SpanType.LLM, model="gpt-4o", has_error="false"
)
```

```typescript
import { Environment } from "confident-ai/common";

const traces = await client.traces.list({
  pageSize: 25,
  environment: Environment.PRODUCTION,
});
traces.traces.forEach((trace) =>
  console.log(trace.uuid, trace.name, trace.status),
);

// `nextCursor` is `string | null` and `cursor` takes `string | undefined`,
// so convert when paging.
const nextPage = await client.traces.list({
  pageSize: 25,
  cursor: traces.nextCursor ?? undefined,
});

const trace = await client.traces.get("<TRACE-UUID>");
const span = await client.spans.get("<SPAN-UUID>");
const thread = await client.threads.get("<THREAD-ID>");
```

Ingesting a trace directly is possible with `client.traces.create(...)`, which
takes the trace's `uuid`, `start_time`, `end_time` and its `spans`. Prefer a
tracing SDK for anything running in production.

## Metrics and Metric Collections

A **metric** defines how something is scored; a **metric collection** bundles
metrics with the settings an evaluation runs them under. Collections are what
you name when running an evaluation.

```python
from confident_ai.metric_collections import MetricSettingConfig

metrics = client.metrics.list()                    # rows on `.metrics`
metric = client.metrics.create(
    "Answer Relevancy",
    criteria="Does the output answer the input?",
)

collections = client.metric_collections.list()     # rows on `.metric_collections`
collection = client.metric_collections.create(
    "Answer Quality",
    metrics_settings=[MetricSettingConfig(metricId=metric.id)],
)
```

```typescript
const metrics = await client.metrics.list();
const metric = await client.metrics.create("Answer Relevancy", {
  criteria: "Does the output answer the input?",
});

const collections = await client.metricCollections.list();
```

## Evaluations

`client.evaluate` scores things that already exist, or runs a set of test cases.

```python
client.evaluate.evaluate_trace("<TRACE-UUID>", "Answer Quality")
client.evaluate.evaluate_span("<SPAN-UUID>", "Answer Quality")
client.evaluate.evaluate_thread("<THREAD-ID>", "Answer Quality")

result = client.evaluate.run_evals(
    "Answer Quality",
    [{"input": "What is the capital of Peru?", "actualOutput": "Lima"}],
    identifier="Nightly",
)
```

```typescript
await client.evaluate.evaluateTrace("<TRACE-UUID>", "Answer Quality");
await client.evaluate.evaluateSpan("<SPAN-UUID>", "Answer Quality");
await client.evaluate.evaluateThread("<THREAD-ID>", "Answer Quality");
```

## Test Runs

A test run groups test case results. `list()` pages with `page` / `page_size`
and filters by `status`.

```python
runs = client.test_runs.list(page=1, page_size=25, status="COMPLETED")
for summary in runs.test_runs:
    print(summary.id, summary.status, summary.tests_passed, summary.tests_failed)

# `create` returns a reference carrying only `id`; read the run back with
# `get` for its status and results.
created = client.test_runs.create(
    metric_collection="Answer Quality", identifier="Nightly"
)
test_run = client.test_runs.get(created.id)

client.test_runs.submit_test_case_result("<TEST-CASE-ID>", actual_output="Lima")
```

```typescript
const runs = await client.testRuns.list({ page: 1, pageSize: 25 });
runs.testRuns.forEach((summary) => console.log(summary.id, summary.status));

const created = await client.testRuns.create("Answer Quality", "Nightly");
const testRun = await client.testRuns.get(created.id);
```

## Everything Else

The remaining resources follow the same `list` / `get` / `create` / `update` /
`delete` shape. Read the method for its arguments — each carries the route's own
summary and description as a docstring (Python) or JSDoc (TypeScript).

| Client | What it holds | Beyond CRUD |
| --- | --- | --- |
| `client.dashboards` | dashboards and their widgets | `query`, `create_widget`, `query_widget` |
| `client.widgets` | ad-hoc widget queries | `query_ad_hoc` |
| `client.annotations` | human ratings on traces and spans | — |
| `client.annotation_queues` | review queues and their items | `add_items`, `annotate_item`, `batch_annotate_items` |
| `client.annotation_forms` | the forms a queue collects | — |
| `client.classifiers` | classifiers and their labels | `generate_labels`, `*_label` |
| `client.rt_frameworks` | red teaming frameworks | `run`, `*_risk_category` |
| `client.attack_methods` | red teaming attack methods | `reset` |
| `client.vulnerabilities` | red teaming vulnerabilities | — |
| `client.personas` | simulated user personas | — |
| `client.evaluation_rules` | rules that trigger evaluations | — |
| `client.scheduled_alerts` | alerts on metric thresholds | — |
| `client.reports` / `client.report_templates` | generated reports | — |
| `client.export_destinations` / `client.export_schedules` | where and when data is exported | — |
| `client.forwarding_connectors` | forwarding traces onward | — |
| `client.ai_connections` | connections to model providers | `ping` |
| `client.mcp_servers` | MCP servers available to agents | `connect` |
| `client.model_costs` | per-model pricing | — |
| `client.transformers` | code that reshapes ingested data | `test_code` |
| `client.metrics_data` | raw metric results | `list` |
| `client.metrics_batch` | batch metric creation | `create` |
| `client.governance` | assess a project against its policy | `assess` |

## Next Steps

- Configure the project key — `references/quickstart.md`.
- The whole surface and the two scopes — `references/introduction.md`.
