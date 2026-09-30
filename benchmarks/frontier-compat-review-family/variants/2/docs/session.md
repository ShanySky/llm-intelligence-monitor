# Session identity

session_key is allocated once when the logical session is created and remains the
business identity used for revocation and audit correlation. Refresh may rotate the
JWT but must preserve the same session_key.
