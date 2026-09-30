import java.util.Map;

public final class FilterEngine {
    public boolean matches(String expression, Map<String, String> record) {
        if (expression == null) throw new IllegalArgumentException("expression");
        Parser parser = new Parser(expression, record);
        boolean result = parser.parseOr();
        if (parser.token.kind != Kind.END) throw new IllegalArgumentException("unexpected token");
        return result;
    }

    private enum Kind { IDENT, STRING, EQ, NE, LPAREN, RPAREN, END }

    private static final class Token {
        final Kind kind;
        final String text;
        Token(Kind kind, String text) { this.kind = kind; this.text = text; }
    }

    private static final class Parser {
        private final String input;
        private final Map<String, String> record;
        private int offset;
        private Token token;

        Parser(String input, Map<String, String> record) {
            this.input = input;
            this.record = record;
            next();
        }

        boolean parseOr() {
            boolean value = parseAnd();
            while (keyword("OR")) {
                next();
                boolean right = parseAnd();
                value = value || right;
            }
            return value;
        }

        boolean parseAnd() {
            boolean value = parseUnary();
            while (keyword("AND")) {
                next();
                boolean right = parseUnary();
                value = value && right;
            }
            return value;
        }

        boolean parseUnary() {
            if (keyword("NOT")) {
                next();
                return !parseUnary();
            }
            if (token.kind == Kind.LPAREN) {
                next();
                boolean value = parseOr();
                require(Kind.RPAREN);
                next();
                return value;
            }
            return parsePredicate();
        }

        boolean parsePredicate() {
            require(Kind.IDENT);
            String field = token.text;
            next();
            if (token.kind == Kind.EQ || token.kind == Kind.NE) {
                boolean unequal = token.kind == Kind.NE;
                next();
                require(Kind.STRING);
                String expected = token.text;
                next();
                String actual = record == null ? null : record.get(field);
                return unequal ? !expected.equals(actual) : expected.equals(actual);
            }
            if (keyword("IS")) {
                next();
                boolean negate = false;
                if (keyword("NOT")) { negate = true; next(); }
                if (!keyword("NULL")) throw new IllegalArgumentException("expected NULL");
                next();
                String actual = record == null ? null : record.get(field);
                return negate ? actual != null : actual == null;
            }
            throw new IllegalArgumentException("expected predicate operator");
        }

        private boolean keyword(String value) {
            return token.kind == Kind.IDENT && token.text.equalsIgnoreCase(value);
        }

        private void require(Kind kind) {
            if (token.kind != kind) throw new IllegalArgumentException("expected " + kind);
        }

        private void next() {
            while (offset < input.length() && Character.isWhitespace(input.charAt(offset))) offset++;
            if (offset == input.length()) { token = new Token(Kind.END, ""); return; }
            char c = input.charAt(offset++);
            switch (c) {
                case '(' -> token = new Token(Kind.LPAREN, "(");
                case ')' -> token = new Token(Kind.RPAREN, ")");
                case '=' -> token = new Token(Kind.EQ, "=");
                case '!' -> {
                    if (offset >= input.length() || input.charAt(offset++) != '=')
                        throw new IllegalArgumentException("invalid operator");
                    token = new Token(Kind.NE, "!=");
                }
                case '"' -> token = readString();
                default -> {
                    if (!identifierChar(c)) throw new IllegalArgumentException("invalid character");
                    int start = offset - 1;
                    while (offset < input.length() && identifierChar(input.charAt(offset))) offset++;
                    token = new Token(Kind.IDENT, input.substring(start, offset));
                }
            }
        }

        private Token readString() {
            StringBuilder value = new StringBuilder();
            while (offset < input.length()) {
                char c = input.charAt(offset++);
                if (c == '"') return new Token(Kind.STRING, value.toString());
                if (c == '\\') {
                    if (offset >= input.length()) throw new IllegalArgumentException("invalid escape");
                    char escaped = input.charAt(offset++);
                    if (escaped != '"' && escaped != '\\') throw new IllegalArgumentException("invalid escape");
                    value.append(escaped);
                } else value.append(c);
            }
            throw new IllegalArgumentException("unterminated string");
        }

        private static boolean identifierChar(char c) {
            return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                   (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-';
        }
    }
}
