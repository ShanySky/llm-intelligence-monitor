# Production constraints

- MySQL 5.7, table `orders`, approximately 80 million rows.
- Rolling deploy: v1 and v2 overlap for 15-30 minutes.
- Rollback from v2 to v1 must remain safe for one full release.
- No migration step may hold a table-blocking lock for roughly more than two seconds.
- Historical data must eventually be represented by the new fields.
