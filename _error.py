"""PytSite Auth Plugin Errors
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import events as _events, lang as _lang


class Error(Exception):
    pass


class AuthenticationError(Error):
    def __init__(self, msg: str = None, **kwargs):
        self._msg = msg

        _events.fire('auth@sign_in_error', exception=self, user=kwargs.get('user'))

    def __str__(self) -> str:
        return self._msg or _lang.t('auth@authentication_error')


class SignUpError(Error):
    def __init__(self, msg: str = None, **kwargs):
        self._msg = msg

        _events.fire('auth@sign_up_error', exception=self, data=kwargs.get('data'))

    def __str__(self) -> str:
        return self._msg or _lang.t('auth@sign_up_error')


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
    def __str__(self) -> str:
        return _lang.t('auth@user_not_found')


class UserNotActive(Error):
    def __str__(self) -> str:
        return _lang.t('auth@user_not_active')


class UserExists(Error):
    def __str__(self) -> str:
        return _lang.t('auth@user_exists')


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


class SignupDisabled(Error):
    def __str__(self) -> str:
        return _lang.t('auth@signup_is_disabled')
