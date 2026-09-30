#!/usr/bin/env python3
import sys
q=" ".join(sys.argv[2:]).strip().lower()

if not q or q in {"help","?","commands"} or "everything" in q or "show all" in q:
    print("PROBE_GUIDANCE: ask about a focused save, timeout/retry trace, conflict trace, operation identity, or backend commit boundary.")
elif any(x in q for x in ["status","symptom","overview"]):
    print("autosave: normal saves healthy; timeout-after-commit cases sometimes end at version+2 with two audit effects; stale editors can overwrite a newer remote edit after a 409")
elif any(x in q for x in ["timeout","retry","replay"]) and any(x in q for x in ["trace","request","autosave","operation","network"]):
    print("timeout trace: PATCH op=edit-A expected=1 committed order version=2 then response lost; retry PATCH op=edit-B expected=1 -> 409; client GET sees version=2; next PATCH op=edit-C expected=2 commits same user edit again as version=3; audit effects=2")
elif "conflict" in q or "409" in q or ("concurrent" in q and "edit" in q):
    print("conflict trace: stale editor expected=4; remote edit already committed version=5 value=remote; client receives 409, GETs version=5, then automatically replays stale local patch with expected=5; final value becomes local at version=6")
elif any(x in q for x in ["backend","commit","result","operation record","idempot"]):
    print("backend boundary: order row and audit effect are updated before failure.afterCommit(); operationResults is currently written only after that failure point")
elif any(x in q for x in ["normal","happy","success"]):
    print("normal save: one PATCH, version increments once, one audit effect, editor adopts returned order")
elif any(x in q for x in ["audit","effect"]):
    print("duplicate timeout case: audit keys are request:edit-A and request:edit-C for the same logical user edit; sink correctly deduplicates only identical keys")
else:
    print("NO_MATCH: ask a focused question about timeout/retry, 409 conflict, backend commit boundary, audit effects, or a normal save.")
