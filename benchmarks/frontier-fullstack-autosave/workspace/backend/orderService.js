const { ApiError } = require("./errors");

class OrderService {
  constructor(audit, failure = null) {
    this.audit = audit;
    this.failure = failure || { afterCommit() {} };
    this.orders = new Map();
    this.operationResults = new Map();
  }

  seed(id, value, version = 1) {
    this.orders.set(id, { id, value, version });
  }

  get(id) {
    const row = this.orders.get(id);
    if (!row) throw new ApiError("NOT_FOUND", "order not found");
    return { ...row };
  }

  patch(req) {
    const prior = this.operationResults.get(req.operationId);
    if (prior) return clone(prior);

    const row = this.orders.get(req.id);
    if (!row) throw new ApiError("NOT_FOUND", "order not found");
    if (row.version !== req.expectedVersion) {
      throw new ApiError("CONFLICT", "expected version is stale");
    }

    row.value = req.value;
    row.version += 1;

    const result = { order: { ...row } };
    this.audit.emit("request:" + req.operationId, row);

    this.failure.afterCommit(req.operationId);

    this.operationResults.set(req.operationId, clone(result));
    return clone(result);
  }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

module.exports = { OrderService };
