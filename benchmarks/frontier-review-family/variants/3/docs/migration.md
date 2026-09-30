# Online migration contract
Backfill captures source version and value while live writers continue. A delayed
backfill item must never overwrite a newer live update. Legacy writes must preserve an
already assigned stable customer key during the compatibility window.
