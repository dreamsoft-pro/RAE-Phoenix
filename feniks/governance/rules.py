from abc import ABC, abstractmethod

from feniks.core.models.types import SystemModel


class GovernanceRule(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def check(self, model: SystemModel) -> bool:
        pass
