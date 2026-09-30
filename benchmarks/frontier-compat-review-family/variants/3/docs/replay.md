# Replay retention

The replay service stores six months of original events. During the producer rollback
window, replay must remain consumable by both old and compatibility consumers.
Irreversible removal of legacy fields belongs after the rollback gate closes.
