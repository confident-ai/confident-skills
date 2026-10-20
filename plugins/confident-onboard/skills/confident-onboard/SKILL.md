---
name: confident-onboard
description: >
  Onboard a user to Confident AI from inside their coding agent: sign in
  through the browser, pick or create a project, save the API key to
  .env.local without the agent ever seeing it, add tracing to their AI app,
  run it on 7 to 10 inputs, and confirm the traces arrived. TRIGGER when the
  user pastes the Confident AI onboarding prompt, or asks to get started with,
  sign up for, log in to, or onboard to Confident AI from their codebase. DO
  NOT TRIGGER when the project already has a working CONFIDENT_API_KEY and the
  user only wants tracing changed (use `confident-tracing` or `confident-otel`),
  or to manage organizations, members, or keys (use `confident-client`).
license: Apache-2.0
metadata:
  author: Confident AI
  version: "1.0.0"
  category: onboarding
  tags: "confident-ai, onboarding, login, tracing, observability"
  compatibility: "Needs Python 3.8+ to run the bundled helper script, a browser for sign-in, and network access to Confident AI."
---

# Confident AI Onboarding

Take a user from nothing to their first traces in Confident AI, inside this
conversation. You do the sign-in plumbing and the code; the user only approves
the sign-in in their browser and answers a question or two.

The order is fixed: **sign in, choose a project, save the key, instrument, run
a batch, verify.** Do not skip ahead. Nothing is evaluated here; this is
tracing.

## Safety rules

- **Never read the key.** Do not open, print, cat, grep, or parse `.env.local`,
  and never echo `CONFIDENT_API_KEY`. The helper script writes it there and
  never prints it. Load it at run time without displaying it (see
  `references/instrument.md`).
- Never paste the key, the setup token, or the sign-in device code into code,
  commands, logs, or chat. The `url` and `code` the script prints for the user
  are fine to show.
- Never hardcode the key or add it to `.env` or any file other than
  `.env.local`.
- Tracing only: no evaluations, metrics, datasets, or refactors.
- Do not commit or push.

## The helper script

All Confident AI calls go through `scripts/confident_onboard.py`, next to this
file. Every command prints one JSON object. Exit code 0 means done, 1 means an
error (read `error`), 2 means still waiting.

If this skill was not installed as a plugin and you are reading it from a URL,
download the script to a temporary folder outside the project, never into it:

```sh
curl -fsSL -o "${TMPDIR:-/tmp}/confident_onboard.py" \
  https://raw.githubusercontent.com/confident-ai/confident-skills/main/plugins/confident-onboard/skills/confident-onboard/scripts/confident_onboard.py
```

Read `references/instrument.md` from the same place
(`.../confident-onboard/references/instrument.md`) when you reach step 5.

Run every command from the application's folder, or pass `--project-dir`.
Below, `onboard` is short for `python3 <path>/confident_onboard.py`. Use
`python` if `python3` is missing; if neither exists, stop and tell the user
Python 3.8+ is needed.

For an EU account, add `--region eu` to `login`.

## Workflow

### 1. Check the folder

Confirm you are in the application the user wants traced. Run `git status`.
If there are uncommitted changes, tell the user your edits will be mixed in
with them and ask whether to continue. If it is not a Git repository, say so
and ask whether to continue.

### 2. Reuse a key that already works

Run `onboard check-key`.

- `accepted`: the project already has a working key. Ask the user whether to
  use it (recommended, skips sign-in) or sign in for a new one. To use it, go to
  step 5.
- `none` or `rejected`: continue to step 3.

### 3. Sign in

Run `onboard login`. It opens the browser and prints a `url` and a `code`.
Show them to the user in a short message on their own lines, for example:

> Approve the sign-in in your browser. If it did not open, go to:
> <url>
> Check that it shows this code: **<code>**

Then run `onboard wait`. It waits up to four minutes and exits with:

- `0` and `status: signed_in`: go to step 4.
- `2` and `status: pending`: remind the user to approve it, then run `onboard
  wait` again. The link lasts ten minutes; after that run `onboard login` again.
- `1`: show the error. If the user denied it or the link expired, start over
  with `onboard login`.

### 4. Choose or create the project

`wait` prints `account`:

- **`existing`**: it lists `projects`. Only projects with `canCreateApiKey:
  true` can be used. If there is exactly one, use it and tell the user which.
  If there are several, ask the user which one (name them, not ids). If there
  are none, stop: the user needs an admin to give them API key access.
  Then run `onboard complete --project-id <id>`.
- **`new`**: it lists `questions` to create their organization and first
  project. Ask the user each one, using its `prompt`, offering its `options`
  for `single_select` and `multi_select`, and its `defaultValue` when present.
  Ask them together in one message when you can. Respect `required`,
  `maxLength`, and `minSelections`. For `multi_select`, if the user picks an
  option marked `exclusive`, send only that one; if they pick one with
  `acceptsCustomValue`, ask its `customPrompt` and send their text in place of
  that option's value. Build a JSON object of question `id` to answer: a string
  for `text`, the option `value` for `single_select`, an array of values for
  `multi_select`. Then run
  `onboard complete --answers '<json>'`, or write the JSON to a temporary file
  outside the project and pass `--answers @<file>`.

`complete` saves the key to `.env.local` with mode 0600, adds `.env.local` to
`.gitignore` if Git is not already ignoring it, and prints `projectId`,
`region`, `otelEndpoint`, `shellKeyDiffers`, and `tracesUrl`. Tell the user the
key was saved to `.env.local` and kept out of Git. If `complete` fails because
the login was already used, run `onboard login` again.

### 5. Instrument the application

Read `references/instrument.md` and follow it. It covers the
`confident-trace` SDK for Python and TypeScript, OpenTelemetry for other
languages, and how the run command loads `.env.local` without reading it.
Carry these values from `complete` or `check-key` into it:

- `otelEndpoint`: for an EU key, set `CONFIDENT_OTEL_ENDPOINT` to it.
- `shellKeyDiffers: true`: the user's shell exports a different key, for
  another project, so the run command must override it with the `.env.local`
  value.

### 6. Run it on 7 to 10 inputs

Follow the batch section of `references/instrument.md`: one input first to
prove tracing works, then the full batch, one input after another, each its
own trace. Never fake a run, mock the model, or stub a call. If the app needs a
secret or a service you do not have, stop here and tell the user exactly what
is needed and the exact command to run once they have it.

### 7. Verify the traces arrived

Run `onboard verify`. It polls for up to three minutes for traces sent since
the key was saved and stops once it sees 7. Pass `--expect <n>` if you ran a
different number.

- `0` and `status: found`: report `traceCount` and `tracesUrl`.
- `2` and `status: timeout`: ingestion can lag. Run `onboard verify` once more.
  If still nothing, check that the run command loaded `.env.local`, that an EU
  key had its endpoint set, and that tracing was flushed or shut down before
  the process exited. Fix and rerun the batch once, then verify again.
- `1`: show the error and the `tracesUrl`.

Never claim traces arrived unless `verify` found them.

## Final report

Tell the user, in a few plain sentences:

- which project the key belongs to, and that it is saved in `.env.local` and
  ignored by Git;
- the files you changed and the integrations you used;
- the run command, on its own line, to send more traces;
- how many traces arrived, with the `tracesUrl` link to open them;
- anything left for them to do, such as a secret to provide.

Leave every change in place on failure. Do not remove instrumentation or the
key.

## References

| Topic | File |
| --- | --- |
| Adding tracing, loading the key, and running the batch | `references/instrument.md` |
| The helper script and its commands | `scripts/confident_onboard.py` |
