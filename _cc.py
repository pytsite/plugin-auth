"""PytSite Auth Plugin Console Commands
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from getpass import getpass as _getpass
from pytsite import console as _console, lang as _lang
from . import _api, _error


class UserAdd(_console.Command):
    """auth:useradd Console Command
    """

    def __init__(self):
        super().__init__()

        self.define_option(_console.option.Str('roles'))

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
            user = _api.create_user(login)

            roles = self.opt('roles')
            if roles:
                # Remove any existing roles
                for role in user.roles:
                    user.remove_role(role)

                # Add specified roles
                for role_name in roles.split(',') if roles else []:
                    try:
                        user.add_role(_api.get_role(role_name)).save()

                    except _error.RoleNotFound as e:
                        user.delete()
                        raise e

            _console.print_success(_lang.t('auth@user_created', {'login': login}))

        except _error.Error as e:
            raise _console.error.CommandExecutionError(e)

        # Set password of the user
        try:
            _console.run_command('auth:passwd', arguments=[login])
        except _console.error.Error as e:
            user.delete()
            raise e


class UserMod(_console.Command):
    """auth:usermod Console Command
    """

    def __init__(self):
        super().__init__()

        self.define_option(_console.option.Str('roles'))

    @property
    def name(self) -> str:
        """Get command's name
        """
        return 'auth:usermod'

    @property
    def description(self) -> str:
        """Get command's description
        """
        return 'auth@usermod_console_command_description'

    def exec(self):
        """Execute the command
        """
        login = self.arg(0)
        if not login:
            raise _console.error.MissingArgument('auth@login_required', 0)

        try:
            user = _api.get_user(login)

            roles = self.opt('roles')
            if roles:
                # Remove all attached roles
                for role in user.roles:
                    user.remove_role(role)

                # Add new roles
                for role_name in roles.split(',') if roles else []:
                    try:
                        user.add_role(_api.get_role(role_name)).save()
                    except _error.RoleNotFound as e:
                        _console.print_warning(e)

            else:
                raise _console.error.MissingOption(list(self._opts.keys()))

            _console.print_success(_lang.t('auth@user_modified', {'login': login}))

        except _error.Error as e:
            raise _console.error.CommandExecutionError(e)


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
        except _error.UserNotFound as e:
            raise _console.error.CommandExecutionError(e)

        while True:
            pass_1 = _getpass(_lang.t('auth@enter_new_password', {'login': user.login}) + ': ')
            if not pass_1:
                raise _console.error.CommandExecutionError(_lang.t('auth@password_cannot_be_empty'))

            pass_2 = _getpass(_lang.t('auth@retype_password') + ': ')

            if pass_1 != pass_2:
                _console.print_error(_lang.t('auth@passwords_dont_match'))
            else:
                break

        try:
            user.password = pass_2
            user.save()
            _console.print_success(_lang.t('auth@password_successfully_changed', {'login': user.login}))

        except Exception as e:
            raise _console.error.CommandExecutionError(e)
