# Local test dependency admission (zero model calls)

| Case | Status | Offline baseline | Offline reference | Seconds |
|---|---|---:|---:|---:|
| axios__axios-5316 | offline_agent_ready | 1 | 0 | 98 |
| google__gson-2158 | offline_agent_ready | 1 | 0 | 73 |
| google__gson-2311 | offline_agent_ready | 1 | 0 | 121 |

**Ready: 3/3.** Tests and source unmodified; model never sees hidden patches.
