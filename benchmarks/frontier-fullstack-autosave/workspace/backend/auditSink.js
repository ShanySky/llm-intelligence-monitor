class AuditSink {
  constructor() {
    this.keys = new Set();
    this.events = [];
  }

  emit(idempotencyKey, order) {
    if (this.keys.has(idempotencyKey)) return;
    this.keys.add(idempotencyKey);
    this.events.push({
      key: idempotencyKey,
      id: order.id,
      version: order.version,
      value: order.value,
    });
  }

  count() {
    return this.events.length;
  }
}

module.exports = { AuditSink };
