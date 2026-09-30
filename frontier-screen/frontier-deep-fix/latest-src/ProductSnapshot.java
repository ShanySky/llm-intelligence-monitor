import java.math.BigDecimal;

public record ProductSnapshot(long id, long version, BigDecimal price) {}
