// Deterministic evaluator for the optional cumulative INPUT token guard.
// A single in-flight API response can go beyond the pre-call threshold;
// after completion an over-limit response is INVALID for quality comparison.
export function inputBudgetExhausted(used,limit,precallStopped=false,precall=false){
  const n=Number(used??0),max=Number(limit??0);
  if(!Number.isFinite(n)||n<0)return true;
  if(!Number.isFinite(max)||max<=0)return Boolean(precallStopped);
  return Boolean(precallStopped) || (precall ? n>=max : n>max);
}
