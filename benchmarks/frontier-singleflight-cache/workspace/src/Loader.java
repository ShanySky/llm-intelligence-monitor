@FunctionalInterface
public interface Loader<K,V> {
    V load(K key) throws Exception;
}
