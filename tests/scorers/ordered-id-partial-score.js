module.exports = (output, context) => {
  const vars = context?.vars ?? {};
  const required = String(vars.required_ids ?? '')
    .split(',').map(x => x.trim()).filter(Boolean);
  const allowed = new Set(
    String(vars.allowed_ids ?? vars.required_ids ?? '')
      .split(',').map(x => x.trim()).filter(Boolean)
  );
  const precedence = String(vars.precedence ?? '')
    .split(';').map(x => x.trim()).filter(Boolean)
    .map(x => x.split('<').map(y => y.trim()))
    .filter(x => x.length === 2 && x[0] && x[1]);

  const ids = String(output ?? '').toUpperCase().match(/[A-Z]+\d+/g) ?? [];
  const unique = [...new Set(ids)];
  const selected = new Set(unique);
  const requiredSet = new Set(required);

  const hit = required.filter(x => selected.has(x)).length;
  const recall = required.length ? hit / required.length : 0;
  const recognized = unique.filter(x => allowed.has(x));
  const precision = unique.length ? hit / unique.length : 0;
  const duplicatePenalty = ids.length ? Math.max(0, (ids.length - unique.length) / ids.length) : 0;

  let orderScore = 1;
  if (precedence.length) {
    let ok = 0;
    for (const [a,b] of precedence) {
      const ia = unique.indexOf(a);
      const ib = unique.indexOf(b);
      if (ia >= 0 && ib >= 0 && ia < ib) ok += 1;
    }
    orderScore = ok / precedence.length;
  }

  const score = Math.max(0, Math.min(1,
    0.60 * recall + 0.20 * precision + 0.20 * orderScore - 0.10 * duplicatePenalty
  ));
  return {
    pass: score >= 0.98,
    score,
    reason: `recall=${recall.toFixed(2)}, precision=${precision.toFixed(2)}, order=${orderScore.toFixed(2)}`,
    namedScores: {
      required_recall: recall,
      selection_precision: precision,
      ordering: orderScore,
    },
  };
};
