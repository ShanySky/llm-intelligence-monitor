public final class LegacyCustomerService {
  public Customer write(long id,String name){
    Customer current=store.get(id);
    Customer replacement=new Customer(id,name);
    store.save(replacement);
    return replacement;
  }
}
