"""
metaprogramming registry
decorator-based plugin registry pattern for dynamically registering
and discovering custom scoring criteria and hard constraint filters at runtime
"""

from typing import Callable, Dict, Any, Type
import functools

# global registry
_CRITERIA_REGISTRY: Dict[str, Callable[..., float]] = {}
_FILTER_REGISTRY: Dict[str, Type] = {}

# decorator to dynamically register a custom criterion evaluation function
def register_criterion(name: str):
    def decorator(func: Callable[..., float]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        _CRITERIA_REGISTRY[name] = func
        return wrapper
    return decorator

# decorator to dynamically register a custom filter strategy class
def register_filter(name: str):
    def decorator(cls: Type):
        _FILTER_REGISTRY[name] = cls
        return cls
    return decorator

# returns a copy of all registered criteria functions
def get_registered_criteria() -> Dict[str, Callable[..., float]]:
    return _CRITERIA_REGISTRY.copy()

# returns a copy of all registered filter classes
def get_registered_filters() -> Dict[str, Type]:
    return _FILTER_REGISTRY.copy()