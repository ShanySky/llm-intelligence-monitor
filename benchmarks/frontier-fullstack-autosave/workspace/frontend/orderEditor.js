let seq = 0;

function nextOperationId() {
  seq += 1;
  return "edit-" + Date.now() + "-" + seq + "-" + Math.random();
}

async function saveOrder(api, state, patch) {
  state.version += 1;

  for (let attempt = 0; attempt < 2; attempt += 1) {
    const operationId = nextOperationId();
    try {
      const result = await api.patch({
        id: state.id,
        expectedVersion: state.version - 1,
        operationId,
        value: patch.value,
      });
      state.value = result.order.value;
      state.version = result.order.version;
      return result.order;
    } catch (err) {
      if (err && err.code === "TIMEOUT") {
        continue;
      }
      if (err && err.code === "CONFLICT") {
        const current = await api.get(state.id);
        state.version = current.version;
        continue;
      }
      throw err;
    }
  }

  const error = new Error("save retries exhausted");
  error.code = "RETRY_EXHAUSTED";
  throw error;
}

module.exports = { saveOrder };
