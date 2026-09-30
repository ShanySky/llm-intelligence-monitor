# Legacy tokens

Some sessions created before the kid rollout still carry no kid. During the grace
window, those tokens are verified only against retained overlap keys belonging to
the token's issuer. Keys from another issuer must never become fallback candidates.
