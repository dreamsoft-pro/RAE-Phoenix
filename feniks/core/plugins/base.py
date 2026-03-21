# feniks/core/plugins/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class RefactorIntention(BaseModel):
    objective: str
    target_files: List[str]
    context: Dict[str, Any] = {}

class CreationSpec(BaseModel):
    objective: str
    target_path: str
    architecture_style: str
    context: Dict[str, Any] = {}

class LanguagePlugin(ABC):
    """Abstract Base Class defining the contract for all Language Plugins (DeepMind standard)."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The canonical name of the plugin (e.g., 'python', 'typescript')."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this plugin handles (e.g., ['.py'], ['.ts', '.tsx'])."""
        pass

    def can_handle(self, file_path: str) -> bool:
        """Determines if this plugin can process the given file."""
        return any(file_path.endswith(ext) for ext in self.supported_extensions)

    @abstractmethod
    async def execute_refactor(self, code: str, intention: RefactorIntention) -> str:
        """
        Executes an AST-driven refactor.
        Should leverage professional tools (libcst, ts-morph) for determinism.
        """
        pass

    @abstractmethod
    async def execute_create(self, spec: CreationSpec) -> str:
        """
        Generates new code scaffolding using AST/Templates.
        """
        pass
