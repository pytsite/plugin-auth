"""PytSite Auth Base Drivers.
"""
from typing import Iterable as _Iterable
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from . import _model

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Authentication(_ABC):
    @_abstractmethod
    def get_name(self) -> str:
        """Get name of the driver
        """
        pass

    @property
    def name(self) -> str:
        """Get name of the driver
        """
        return self.get_name()

    @_abstractmethod
    def get_description(self) -> str:
        """Get description of the driver
        """
        pass

    @property
    def description(self) -> str:
        """Get description of the driver
        """
        return self.get_description()

    @_abstractmethod
    def sign_up(self, data: dict) -> _model.AbstractUser:
        """Register a new user
        """
        pass

    @_abstractmethod
    def sign_in(self, data: dict) -> _model.AbstractUser:
        """Authenticate an existing user
        """
        pass

    @_abstractmethod
    def sign_out(self, user: _model.AbstractUser):
        """End user's session
        """
        pass


class Storage(_ABC):
    @_abstractmethod
    def get_name(self) -> str:
        pass

    @_abstractmethod
    def create_role(self, name: str, description: str = '') -> _model.AbstractRole:
        pass

    @_abstractmethod
    def get_role(self, name: str = None, uid: str = None) -> _model.AbstractRole:
        pass

    @_abstractmethod
    def get_roles(self, flt: dict = None, sort_field: str = None, sort_order: int = 1, limit: int = None,
                  skip: int = 0) -> _Iterable[_model.AbstractRole]:
        pass

    @_abstractmethod
    def create_user(self, login: str, password: str = None) -> _model.AbstractUser:
        pass

    @_abstractmethod
    def get_user(self, login: str = None, nickname: str = None, uid: str = None) -> _model.AbstractUser:
        pass

    @_abstractmethod
    def get_users(self, flt: dict = None, sort_field: str = None, sort_order: int = 1, limit: int = None,
                  skip: int = 0) -> _Iterable[_model.AbstractUser]:
        pass

    @_abstractmethod
    def count_users(self, flt: dict = None) -> int:
        pass

    @_abstractmethod
    def count_roles(self, flt: dict = None) -> int:
        pass
