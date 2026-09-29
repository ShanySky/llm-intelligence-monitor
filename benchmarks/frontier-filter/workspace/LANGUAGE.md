# Filter language

Entry point:

`FilterEngine.matches(String expression, Map<String,String> record)`

Grammar, from lowest to highest precedence:

- `expr := orExpr`
- `orExpr := andExpr (OR andExpr)*`
- `andExpr := unaryExpr (AND unaryExpr)*`
- `unaryExpr := NOT unaryExpr | '(' expr ')' | predicate`
- `predicate := IDENT '=' STRING`
- `predicate := IDENT '!=' STRING`
- `predicate := IDENT IS NULL`
- `predicate := IDENT IS NOT NULL`

Semantics:

1. Keywords AND, OR, NOT, IS, NULL are case-insensitive.
2. Identifiers are case-sensitive and contain letters, digits, underscore, dot,
   or dash. They may not be quoted.
3. STRING is double quoted. Inside it, `\\"` means a quote and `\\` means a
   backslash. Other backslash escapes are invalid.
4. A missing identifier is treated as null.
5. `field = "x"` is false for null; `field != "x"` is true for null.
6. Parentheses may be nested.
7. Whitespace may appear between tokens; no whitespace is required around
   parentheses.
8. The entire input must be consumed. Empty input, dangling operators,
   unbalanced parentheses, invalid escapes, unterminated strings, or unexpected
   tokens must throw IllegalArgumentException.
