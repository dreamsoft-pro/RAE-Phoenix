# feniks/core/plugins/manager.py
import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type
from feniks.infra.logging import get_logger
from .base import LanguagePlugin

logger = get_logger("plugin.manager")

class PluginManager:
    """Dynamically discovers and manages language plugins for RAE-Phoenix."""
    
    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugins: Dict[str, LanguagePlugin] = {}
        # Resolve path relative to this file
        base_dir = Path(__file__).resolve().parent.parent.parent / "plugins"
        self.plugin_dir = plugin_dir or str(base_dir)
        self._load_plugins()

    def _load_plugins(self):
        """Discovers and loads all classes inheriting from LanguagePlugin."""
        logger.info(f"Scanning for plugins in: {self.plugin_dir}")
        if not Path(self.plugin_dir).exists():
            logger.warning(f"Plugin directory {self.plugin_dir} does not exist.")
            return

        # Add to sys.path to allow importlib to find it
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        for _, name, is_pkg in pkgutil.iter_modules([self.plugin_dir]):
            if is_pkg:
                continue
            try:
                module = importlib.import_module(name)
                for item_name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, LanguagePlugin) and obj is not LanguagePlugin:
                        plugin_instance = obj()
                        self.plugins[plugin_instance.name] = plugin_instance
                        logger.info(f"Loaded plugin: {plugin_instance.name} supporting {plugin_instance.supported_extensions}")
            except Exception as e:
                logger.error(f"Failed to load plugin module {name}: {e}")

    def get_plugin_for_file(self, file_path: str) -> Optional[LanguagePlugin]:
        """Routes a file to the appropriate plugin based on extension."""
        for plugin in self.plugins.values():
            if plugin.can_handle(file_path):
                return plugin
        return None

    def get_plugin_by_name(self, name: str) -> Optional[LanguagePlugin]:
        """Fetches a plugin explicitly by name."""
        return self.plugins.get(name)

    def list_available_plugins(self) -> List[str]:
        return list(self.plugins.keys())
