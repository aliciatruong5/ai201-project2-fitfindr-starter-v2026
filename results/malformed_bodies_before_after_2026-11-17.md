# serve.py: malformed request bodies, before and after

Produced by sending the same 8 bodies to `POST /ask` on a running `serve.py`
(`PORT=5001`, model cache off) and counting the lines added to `logs/serve.jsonl`
for each. The "before" run used `serve.py` as committed in `91d60de`; the
"after" run used it with the type check added at the top of `ask()`. Pasted from
the terminal output of those two runs.

## Before

```
query is a number            status 500  log lines added 0
body is a JSON list          status 500  log lines added 0
body is a JSON string        status 500  log lines added 0
query is a list              status 500  log lines added 0
query is null                status 400  log lines added 1
query is blank               status 400  log lines added 1
body is not JSON             status 400  log lines added 1
empty object                 status 400  log lines added 1
tracebacks in server output: 4
```

## After

```
query is a number            status 400  log lines added 1
body is a JSON list          status 400  log lines added 1
body is a JSON string        status 400  log lines added 1
query is a list              status 400  log lines added 1
query is null                status 400  log lines added 1
query is blank               status 400  log lines added 1
body is not JSON             status 400  log lines added 1
empty object                 status 400  log lines added 1
tracebacks in server output: 0
```

## Normal requests still work (after)

```
200 completed  model_calls 2  selected_item lst_002   "vintage graphic tee under $30"
200 no_match   model_calls 0  selected_item None      "designer ballgown size XXS under $5"
```
