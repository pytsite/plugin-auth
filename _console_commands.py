"""PytSite Authentication and Authorization Plugin Console Commands
"""
from getpass import getpass as _getpass
from pytsite import console as _console, lang as _lang
from . import _api, _error

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class UserAdd(_console.Command):
    """auth:useradd Console Command
    """

    @property
    def name(self) -> str:
        """Get command's name
        """
        return 'auth:useradd'

    @property
    def description(self) -> str:
        """Get command's description
        """
        return 'auth@useradd_console_command_description'

    def exec(self):
        """Execute the command
        """
        login = self.arg(0)
        if not login:
            raise _console.error.MissingArgument('auth@login_required', 0)

        try:
            _api.switch_user_to_system()
            user = _api.create_user(login)
            _api.restore_user()
            _console.print_success(_lang.t('auth@user_has_been_created', {'login': login}))

        except (_error.UserCreateError, _error.UserAlreadyExists) as e:
            raise _console.error.Error(e)

        try:
            _console.run_command('auth:passwd', arguments=[login])

        except _console.error.Error as e:
            _api.switch_user_to_system()
            user.delete()
            _api.restore_user()

            raise e


class Passwd(_console.Command):
    """auth:passwd Console Command
    """

    @property
    def name(self) -> str:
        """Get command's name
        """
        return 'auth:passwd'

    @property
    def description(self) -> str:
        """Get command's description
        """
        return 'auth@passwd_console_command_description'

    def exec(self):
        """Execute the command
        """
        login = self.arg(0)
        if not login:
            raise _console.error.MissingArgument('auth@login_required', 0)

        try:
            user = _api.get_user(login)
        except _error.UserNotFound:
            raise _console.error.Error(_lang.t('auth@user_is_not_exist', {'login': login}))

        while True:
            pass_1 = _getpass(_lang.t('auth@enter_new_password', {'login': user.login}) + ': ')
            if not pass_1:
                raise _console.error.Error(_lang.t('auth@password_cannot_be_empty'))

            pass_2 = _getpass(_lang.t('auth@retype_password') + ': ')

            if pass_1 != pass_2:
                _console.print_error(_lang.t('auth@passwords_dont_match'))
            else:
                break

        try:
            _api.switch_user_to_system()
            user.password = pass_2
            user.save()
            _console.print_success(_lang.t('auth@password_successfully_changed', {'login': user.login}))

        except Exception as e:
            raise _console.error.Error(str(e))
