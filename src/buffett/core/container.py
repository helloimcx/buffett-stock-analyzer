"""
Dependency Injection Container

This module implements a lightweight dependency injection container to manage
component dependencies and support SOLID principles throughout the application.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Callable, Optional, Union
from functools import wraps
import inspect

from ..exceptions.base import BuffettException


T = TypeVar('T')


class DependencyResolutionError(BuffettException):
    """Raised when a dependency cannot be resolved."""

    def __init__(self, dependency_type: Type[T], message: str = None):
        self.dependency_type = dependency_type
        self.message = message or f"Cannot resolve dependency: {dependency_type.__name__}"
        super().__init__(self.message, error_code="DEPENDENCY_RESOLUTION_ERROR")


class Container:
    """
    Simple dependency injection container.

    Supports:
    - Singleton and transient lifetimes
    - Factory functions
    - Interface-to-implementation bindings
    - Circular dependency detection
    """

    def __init__(self, name: str = "default"):
        """Initialize container with given name."""
        self.name = name
        self._services: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._resolution_stack: set = set()

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None
    ) -> 'Container':
        """
        Register a singleton service.

        Args:
            interface: The service interface type
            implementation: Implementation class (if using class-based registration)
            factory: Factory function (if using factory-based registration)

        Returns:
            Self for method chaining
        """
        # If no implementation provided, use interface as implementation
        if implementation is None and factory is None:
            implementation = interface

        self._services[interface] = {
            'lifetime': 'singleton',
            'implementation': implementation,
            'factory': factory
        }
        return self

    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None
    ) -> 'Container':
        """
        Register a transient service (new instance each time).

        Args:
            interface: The service interface type
            implementation: Implementation class (if using class-based registration)
            factory: Factory function (if using factory-based registration)

        Returns:
            Self for method chaining
        """
        # If no implementation provided, use interface as implementation
        if implementation is None and factory is None:
            implementation = interface

        self._services[interface] = {
            'lifetime': 'transient',
            'implementation': implementation,
            'factory': factory
        }
        return self

    def register_instance(self, interface: Type[T], instance: T) -> 'Container':
        """
        Register a specific instance as singleton.

        Args:
            interface: The service interface type
            instance: The instance to register

        Returns:
            Self for method chaining
        """
        self._services[interface] = {
            'lifetime': 'singleton',
            'implementation': None,
            'factory': None,
            'instance': instance
        }
        self._singletons[interface] = instance
        return self

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency.

        Args:
            interface: The service interface type to resolve

        Returns:
            The resolved service instance

        Raises:
            DependencyResolutionError: If the dependency cannot be resolved
        """
        # Check for circular dependencies
        if interface in self._resolution_stack:
            raise DependencyResolutionError(
                interface,
                f"Circular dependency detected for {interface.__name__}"
            )

        # Check if service is registered
        if interface not in self._services:
            raise DependencyResolutionError(
                interface,
                f"Service {interface.__name__} is not registered"
            )

        service_config = self._services[interface]

        # If it's a pre-registered instance, return it
        if 'instance' in service_config:
            return service_config['instance']

        # If it's a singleton and already created, return it
        if service_config['lifetime'] == 'singleton' and interface in self._singletons:
            return self._singletons[interface]

        # Add to resolution stack for circular dependency detection
        self._resolution_stack.add(interface)

        try:
            # Resolve the dependency
            if service_config['factory']:
                instance = self._resolve_with_factory(service_config['factory'])
            else:
                instance = self._resolve_with_class(service_config['implementation'])

            # Store singleton instances
            if service_config['lifetime'] == 'singleton':
                self._singletons[interface] = instance

            return instance

        finally:
            # Remove from resolution stack
            self._resolution_stack.discard(interface)

    def _resolve_with_factory(self, factory: Callable[[], T]) -> T:
        """Resolve dependency using factory function."""
        # Inject dependencies into factory if needed
        sig = inspect.signature(factory)
        if sig.parameters:
            kwargs = self._resolve_parameters(sig)
            return factory(**kwargs)
        return factory()

    def _resolve_with_class(self, implementation: Type[T]) -> T:
        """Resolve dependency by instantiating class with constructor injection."""
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)

        # Resolve constructor parameters
        kwargs = self._resolve_parameters(sig)

        # Create instance
        return implementation(**kwargs)

    def _resolve_parameters(self, sig: inspect.Signature) -> Dict[str, Any]:
        """Resolve parameters for function/class constructor."""
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Try to resolve from type annotation
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation

                # Skip if it's not a registered service
                if param_type in self._services:
                    kwargs[param_name] = self.resolve(param_type)
                # Handle Optional types
                elif hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
                    args = param_type.__args__
                    # Check if it's Optional[T] (Union[T, None])
                    if len(args) == 2 and type(None) in args:
                        non_none_type = args[0] if args[1] is type(None) else args[1]
                        if non_none_type in self._services:
                            kwargs[param_name] = self.resolve(non_none_type)
                # Use default value if available
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default

        return kwargs

    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return interface in self._services

    def clear(self) -> None:
        """Clear all registrations and singleton instances."""
        self._services.clear()
        self._singletons.clear()
        self._resolution_stack.clear()

    def get_singleton_instances(self) -> Dict[Type, Any]:
        """Get all singleton instances (useful for debugging)."""
        return self._singletons.copy()


# Global default container
default_container = Container("default")


def inject(interface: Type[T]) -> Any:
    """
    Decorator for dependency injection in functions and methods.

    Example:
        @inject(IDataService)
        def my_function(data_service: IDataService):
            return data_service.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve dependencies from function signature
            sig = inspect.signature(func)

            # Skip 'self' for instance methods
            param_start = 1 if len(args) > 0 and hasattr(args[0], '__class__') else 0

            for param_name, param in list(sig.parameters.items())[param_start:]:
                if param_name not in kwargs:
                    # Try to resolve from type annotation
                    if param.annotation != inspect.Parameter.empty:
                        if default_container.is_registered(param.annotation):
                            kwargs[param_name] = default_container.resolve(param.annotation)

            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_container(name: str = None) -> Container:
    """Get a container by name or the default container."""
    return default_container if name is None else default_container