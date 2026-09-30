# Profile update contract
ProfileRepository.updateIfVersion returns false on optimistic conflict. Reads use a
shared cache-aside layer; cache misses can repopulate committed state while an update
transaction is still open.
