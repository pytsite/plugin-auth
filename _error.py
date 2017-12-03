"""PytSite Authentication and Authorization Plugin Errors
"""
from pytsite import events as _events, lang as _lang

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Error(Exception):
    pass


class AuthenticationError(Error):
    def __init__(self, msg: str = None, **kwargs):
        self._msg = msg

        _events.fire('auth.sign_in_error', exception=self, user=kwargs.get('user'))

    def __str__(self) -> str:
        return self._msg or _lang.t('auth@authentication_error')


class NoDriverRegistered(Error):
    pass


class DriverNotRegistered(Error):
    pass


class DriverRegistered(Error):
    pass


class RoleNotFound(Error):
    def __init__(self, role_name: str):
        self._role_name = role_name

    def __str__(self) -> str:
        return "Role '{}' is not found".format(self._role_name)


class RoleAlreadyExists(Error):
    def __init__(self, role_name: str):
        self._role_name = role_name

    def __str__(self) -> str:
        return "Role '{}' is already exist".format(self._role_name)


class UserNotFound(Error):
    pass


class UserAlreadyExists(Error):
    def __init__(self, login: str):
        self._login = login

    def __str__(self) -> str:
        return "User with login '{}' is already exist".format(self._login)


class UserCreateError(Error):
    pass


class InvalidAccessToken(Error):
    pass


class UserModifyForbidden(Error):
    pass


class UserDeleteForbidden(Error):
    pass


class RoleModifyForbidden(Error):
    pass


class RoleDeleteForbidden(Error):
    pass


class NoAdminUser(Error):
    pass
