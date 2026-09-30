class AuditSink {
  constructor() {
    this.keys = new Set();
    this.events = [];
  }
  emit(key, order) {
    if (this.keys.has(key)) return;
    this.keys.add(key);
    this.events.push({ key, id: order.id, version: order.version, value: order.value });
  }
  count() { return this.events.length; }
}
module.exports = { AuditSink };
