# Task: repair cross-layer order autosave recovery

The order editor passes a normal save smoke test, but production traces show two
reliability failures:

- a transport timeout after a successful save can produce duplicate audit/business
  effects when the client retries;
- a stale editor can silently overwrite a newer concurrent edit after receiving a
  version conflict.

Inspect both the frontend and backend code. Use the opaque `probe` tool for
runtime evidence, then implement the minimal complete repair.

Requirements:

- preserve the public module exports and function/class method signatures;
- transport retries for one logical edit must converge to one committed edit and
  one audit effect;
- a semantic version conflict must not be converted into an automatic overwrite;
- local editor version/value must advance only from a confirmed server result;
- separate user edits must remain separate operations;
- do not disable retries or optimistic concurrency.

Run `./run_visible_tests.sh` and black-box validation before finishing.
