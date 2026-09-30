const { saveOrder } = require("./frontend/orderEditor");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");

(async () => {
  const audit = new AuditSink();
  const service = new OrderService(audit);
  service.seed("o-1", "draft", 1);

  const api = {
    patch: async (req) => service.patch(req),
    get: async (id) => service.get(id),
  };

  const state = { id: "o-1", value: "draft", version: 1 };
  const saved = await saveOrder(api, state, { value: "ready" });

  if (saved.value !== "ready" || saved.version !== 2) throw new Error("save");
  if (state.value !== "ready" || state.version !== 2) throw new Error("state");
  if (audit.count() !== 1) throw new Error("audit");

  console.log("VISIBLE_TEST_PASS");
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
