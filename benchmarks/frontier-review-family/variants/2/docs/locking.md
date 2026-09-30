# Locking contract
All two-resource operations must acquire locks in ascending resource-id order across
all code paths and instances.
