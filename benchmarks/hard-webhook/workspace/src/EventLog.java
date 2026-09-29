import java.util.*; public final class EventLog { private final Set<String> ids=new HashSet<>(); public boolean record(String id){return ids.add(id);} public int size(){return ids.size();} }
