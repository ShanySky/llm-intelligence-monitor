const { saveOrder } = require("./orderEditor");

class OfflineQueue {
  constructor(storage) {
    this.storage = storage;
  }

  enqueue(state, patch) {
    this.storage.items.push({
      id: state.id,
      expectedVersion: state.version,
      value: patch.value,
    });
  }

  async flush(api) {
    while (this.storage.items.length) {
      const item = this.storage.items[0];
      const state = { id: item.id, value: null, version: item.expectedVersion };
      await saveOrder(api, state, { value: item.value });
      this.storage.items.shift();
    }
  }
}

module.exports = { OfflineQueue };
