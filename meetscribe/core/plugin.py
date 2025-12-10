"""
Plugin system for MeetScribe.

Provides plugin discovery, loading, validation, and registry for
third-party provider extensions.
"""

import inspect
import logging
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .providers import ConvertProvider, InputProvider, LLMProvider, OutputRenderer

# Import entry_points based on Python version
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


# Entry point group names for each provider type
ENTRY_POINT_GROUPS = {
    "input": "meetscribe.plugins.input",
    "converter": "meetscribe.plugins.converter",
    "llm": "meetscribe.plugins.llm",
    "output": "meetscribe.plugins.output",
}

# Base classes for each provider type
PROVIDER_BASE_CLASSES = {
    "input": InputProvider,
    "converter": ConvertProvider,
    "llm": LLMProvider,
    "output": OutputRenderer,
}


@dataclass
class PluginMetadata:
    """
    Metadata about a registered plugin.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version string
        provider_type: Type of provider (input, converter, llm, output)
        provider_class: Class name of the provider
        description: Optional plugin description
        author: Optional author name
        homepage: Optional homepage URL
        dependencies: List of required dependencies
    """

    name: str
    version: str
    provider_type: str
    provider_class: str
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


class PluginRegistry:
    """
    Singleton registry for managing plugin providers.

    Stores registered plugins and provides lookup functionality.
    """

    _instance: Optional["PluginRegistry"] = None

    def __new__(cls) -> "PluginRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, Type] = {}
            cls._instance._metadata: Dict[str, PluginMetadata] = {}
        return cls._instance

    def register(
        self,
        name: str,
        provider_class: Type,
        metadata: PluginMetadata,
    ) -> None:
        """
        Register a plugin provider.

        Args:
            name: Unique plugin identifier
            provider_class: Provider class to register
            metadata: Plugin metadata
        """
        self._plugins[name] = provider_class
        self._metadata[name] = metadata
        logger.debug(f"Registered plugin: {name} (v{metadata.version})")

    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            name: Plugin identifier

        Returns:
            True if plugin was unregistered, False if not found
        """
        if name in self._plugins:
            del self._plugins[name]
            del self._metadata[name]
            logger.debug(f"Unregistered plugin: {name}")
            return True
        return False

    def has_plugin(self, name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            name: Plugin identifier

        Returns:
            True if plugin exists
        """
        return name in self._plugins

    def get_plugin_class(self, name: str) -> Optional[Type]:
        """
        Get a plugin class by name.

        Args:
            name: Plugin identifier

        Returns:
            Provider class or None if not found
        """
        return self._plugins.get(name)

    def get_plugin_metadata(self, name: str) -> Optional[PluginMetadata]:
        """
        Get plugin metadata by name.

        Args:
            name: Plugin identifier

        Returns:
            PluginMetadata or None if not found
        """
        return self._metadata.get(name)

    def get_all_plugins(self) -> Dict[str, Type]:
        """
        Get all registered plugins.

        Returns:
            Dictionary of plugin name to class
        """
        return dict(self._plugins)

    def get_plugins_by_type(self, provider_type: str) -> Dict[str, Type]:
        """
        Get plugins filtered by provider type.

        Args:
            provider_type: Type to filter by (input, converter, llm, output)

        Returns:
            Dictionary of matching plugins
        """
        return {
            name: cls
            for name, cls in self._plugins.items()
            if self._metadata.get(name, PluginMetadata("", "", "", "")).provider_type
            == provider_type
        }


class PluginValidator:
    """
    Validates plugin classes for correctness.

    Checks that plugins properly implement required interfaces.
    """

    def validate_provider_class(
        self,
        provider_class: Type,
        provider_type: str,
    ) -> Tuple[bool, List[str]]:
        """
        Validate a provider class.

        Args:
            provider_class: Class to validate
            provider_type: Expected provider type

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        # Check provider type is known
        if provider_type not in PROVIDER_BASE_CLASSES:
            errors.append(f"Unknown provider type: {provider_type}")
            return False, errors

        base_class = PROVIDER_BASE_CLASSES[provider_type]

        # Check class inherits from correct base
        if not issubclass(provider_class, base_class):
            errors.append(
                f"Provider class must inherit from {base_class.__name__}, "
                f"got {provider_class.__bases__}"
            )
            return False, errors

        # Check abstract methods are implemented
        abstract_methods = getattr(base_class, "__abstractmethods__", set())
        for method_name in abstract_methods:
            method = getattr(provider_class, method_name, None)
            if method is None:
                errors.append(f"Missing required method: {method_name}")
            elif getattr(method, "__isabstractmethod__", False):
                errors.append(f"Abstract method not implemented: {method_name}")

        # Try to instantiate to catch any runtime issues
        try:
            # Check if the class can be called (not actually instantiate)
            if inspect.isabstract(provider_class):
                errors.append(
                    "Provider class is still abstract, " "must implement all abstract methods"
                )
        except Exception as e:
            errors.append(f"Failed to validate class: {e}")

        return len(errors) == 0, errors


class PluginDiscovery:
    """
    Discovers plugins from entry points.

    Uses Python's entry_points mechanism for plugin discovery.
    """

    def discover_entry_points(
        self,
        provider_type: str,
    ) -> List[Tuple[str, Type, Optional[PluginMetadata]]]:
        """
        Discover plugins for a specific provider type.

        Args:
            provider_type: Type of provider to discover

        Returns:
            List of (name, class, metadata) tuples
        """
        group = ENTRY_POINT_GROUPS.get(provider_type)
        if not group:
            logger.warning(f"Unknown provider type for discovery: {provider_type}")
            return []

        discovered = []

        try:
            # Get entry points - handle both old and new API
            eps = entry_points()

            # Handle different return types from entry_points()
            if isinstance(eps, dict):
                points = eps.get(group, [])
            else:
                # Python 3.10+ returns SelectableGroups
                points = eps.get(group, [])

            for ep in points:
                try:
                    provider_class = ep.load()

                    # Try to get metadata from class
                    metadata = self._extract_metadata(ep.name, provider_class, provider_type)

                    discovered.append((ep.name, provider_class, metadata))
                    logger.debug(f"Discovered plugin: {ep.name} from {ep.value}")

                except ImportError as e:
                    logger.warning(f"Failed to load plugin {ep.name}: {e}")
                except Exception as e:
                    logger.error(f"Error loading plugin {ep.name}: {e}")

        except Exception as e:
            logger.error(f"Error discovering entry points for {provider_type}: {e}")

        return discovered

    def discover_all(self) -> Dict[str, List[Tuple[str, Type, Optional[PluginMetadata]]]]:
        """
        Discover all plugins for all provider types.

        Returns:
            Dictionary of provider_type to list of discovered plugins
        """
        return {
            provider_type: self.discover_entry_points(provider_type)
            for provider_type in ENTRY_POINT_GROUPS
        }

    def _extract_metadata(
        self,
        name: str,
        provider_class: Type,
        provider_type: str,
    ) -> PluginMetadata:
        """
        Extract metadata from a plugin class.

        Args:
            name: Plugin name from entry point
            provider_class: The loaded class
            provider_type: Type of provider

        Returns:
            PluginMetadata instance
        """
        # Try to get metadata from class attributes
        version = getattr(provider_class, "__version__", "0.0.0")
        description = getattr(provider_class, "__description__", None)
        author = getattr(provider_class, "__author__", None)
        homepage = getattr(provider_class, "__homepage__", None)
        dependencies = getattr(provider_class, "__dependencies__", [])

        return PluginMetadata(
            name=name,
            version=str(version),
            provider_type=provider_type,
            provider_class=provider_class.__name__,
            description=description,
            author=author,
            homepage=homepage,
            dependencies=dependencies,
        )


class PluginLoader:
    """
    Loads and instantiates plugins.

    Provides a consistent interface for creating plugin instances.
    """

    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,
        validate: bool = False,
    ):
        """
        Initialize loader.

        Args:
            registry: Plugin registry to use (defaults to singleton)
            validate: Whether to validate plugins before loading
        """
        self.registry = registry or PluginRegistry()
        self.validate = validate
        self.validator = PluginValidator() if validate else None

    def load(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Any:
        """
        Load and instantiate a plugin.

        Args:
            name: Plugin identifier
            config: Configuration to pass to plugin

        Returns:
            Plugin instance

        Raises:
            ValueError: If plugin not found or validation fails
        """
        provider_class = self.registry.get_plugin_class(name)

        if provider_class is None:
            raise ValueError(f"Plugin not found: {name}")

        if self.validate and self.validator:
            metadata = self.registry.get_plugin_metadata(name)
            provider_type = metadata.provider_type if metadata else "unknown"

            is_valid, errors = self.validator.validate_provider_class(provider_class, provider_type)

            if not is_valid:
                raise ValueError(f"Plugin validation failed for {name}: {'; '.join(errors)}")

        return provider_class(config)


def initialize_plugins(
    auto_discover: bool = True,
    validate: bool = True,
) -> PluginRegistry:
    """
    Initialize the plugin system.

    Args:
        auto_discover: Whether to auto-discover entry point plugins
        validate: Whether to validate discovered plugins

    Returns:
        The plugin registry instance
    """
    registry = PluginRegistry()
    validator = PluginValidator() if validate else None

    if auto_discover:
        discovery = PluginDiscovery()
        all_plugins = discovery.discover_all()

        for provider_type, plugins in all_plugins.items():
            for name, provider_class, metadata in plugins:
                if validate and validator:
                    is_valid, errors = validator.validate_provider_class(
                        provider_class, provider_type
                    )
                    if not is_valid:
                        logger.warning(f"Skipping invalid plugin {name}: {'; '.join(errors)}")
                        continue

                if metadata:
                    registry.register(name, provider_class, metadata)

    logger.info(f"Plugin system initialized with {len(registry.get_all_plugins())} plugins")
    return registry
