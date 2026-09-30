public final class FeedService {
  public Page page(String token,int limit){
    int offset=token==null?0:Integer.parseInt(token);
    List<Row> rows=store.currentRowsSorted().stream().skip(offset).limit(limit).toList();
    return new Page(rows,rows.size()<limit?null:String.valueOf(offset+rows.size()));
  }
}
