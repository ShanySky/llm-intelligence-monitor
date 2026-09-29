public interface FailureInjector { void afterReserve(String orderId); static FailureInjector none(){return id->{};} }
