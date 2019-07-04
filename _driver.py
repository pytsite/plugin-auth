"""PytSite Auth Plugin Drivers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Iterator, List, Tuple
from abc import ABC, abstractmethod
from plugins.query import Query
from . import _model


class Authentication(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Get name of the driver
        """
        pass

    @property
    def name(self) -> str:
        """Get name of the driver
        """
        return self.get_name()

    @abstractmethod
    def get_description(self) -> str:
        """Get description of the driver
        """
        pass

    @property
    def description(self) -> str:
        """Get description of the driver
        """
        return self.get_description()

    @abstractmethod
    def sign_up(self, data: dict) -> _model.AbstractUser:
        """Register a new user
        """
        pass

    @abstractmethod
    def sign_in(self, data: dict) -> _model.AbstractUser:
        """Authenticate an existing user
        """
        pass

    @abstractmethod
    def sign_out(self, user: _model.AbstractUser):
        """End user's session
        """
        pass


class Storage(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def create_role(self, name: str, description: str = '') -> _model.AbstractRole:
        pass

    @abstractmethod
    def get_role(self, name: str = None, uid: str = None) -> _model.AbstractRole:
        pass

    @abstractmethod
    def find_roles(self, query: Query = None, sort: List[Tuple[str, int]] = None, limit: int = None,
                   skip: int = 0) -> Iterator[_model.AbstractRole]:
        pass

    @abstractmethod
    def create_user(self, login: str, password: str = None) -> _model.AbstractUser:
        pass

    @abstractmethod
    def get_user(self, login: str = None, nickname: str = None, uid: str = None) -> _model.AbstractUser:
        pass

    @abstractmethod
    def find_users(self, query: Query = None, sort: List[Tuple[str, int]] = None, limit: int = None,
                   skip: int = 0) -> Iterator[_model.AbstractUser]:
        pass

    @abstractmethod
    def count_users(self, query: Query = None) -> int:
        pass

    @abstractmethod
    def count_roles(self, query: Query = None) -> int:
        pass
