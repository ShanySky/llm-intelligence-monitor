public final class ProfileService {
  @Transactional
  public void rename(long id,long expectedVersion,String name){
    repo.updateIfVersion(id,expectedVersion,name);
    cache.evict(id);
  }
}
