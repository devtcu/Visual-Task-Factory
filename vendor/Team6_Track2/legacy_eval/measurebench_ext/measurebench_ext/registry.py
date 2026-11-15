"""Small local registry for procedural instrument renderers."""

GENERATORS = {}

def register(name):
    def decorator(function):
        if name in GENERATORS:
            raise ValueError(f"Duplicate instrument generator: {name}")
        GENERATORS[name] = function
        return function
    return decorator

def list_generators():
    return tuple(GENERATORS)

