import java.util.*;

public final class FilterEngine {
    public boolean matches(String expression, Map<String,String> record) {
        // Legacy evaluator: intentionally simplistic. It only understands
        // predicates joined left-to-right with AND/OR.
        List<String> tokens = new ArrayList<>(Arrays.asList(expression.trim().split("\\s+")));
        if (tokens.size() < 3) {
            throw new IllegalArgumentException("expression");
        }

        boolean value = predicate(tokens.get(0), tokens.get(1), tokens.get(2), record);
        int i = 3;
        while (i < tokens.size()) {
            String op = tokens.get(i++);
            if (i + 2 >= tokens.size()) {
                throw new IllegalArgumentException("dangling operator");
            }
            boolean rhs = predicate(tokens.get(i), tokens.get(i + 1), tokens.get(i + 2), record);
            i += 3;
            if (op.equalsIgnoreCase("AND")) {
                value = value && rhs;
            } else if (op.equalsIgnoreCase("OR")) {
                value = value || rhs;
            } else {
                throw new IllegalArgumentException("operator");
            }
        }
        return value;
    }

    private boolean predicate(String field, String op, String raw, Map<String,String> record) {
        if (!raw.startsWith("\"") || !raw.endsWith("\"")) {
            throw new IllegalArgumentException("string");
        }
        String expected = raw.substring(1, raw.length() - 1);
        String actual = record.get(field);
        return switch (op) {
            case "=" -> Objects.equals(actual, expected);
            case "!=" -> !Objects.equals(actual, expected);
            default -> throw new IllegalArgumentException("predicate");
        };
    }
}
