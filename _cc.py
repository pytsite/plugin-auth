"""PytSite Auth Plugin Console Commands
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from getpass import getpass
from pytsite import console, lang
from . import _api, _error


class UserAdd(console.Command):
    """auth:useradd Console Command
    """

    def __init__(self):
        super().__init__()

        self.define_option(console.option.Str('roles'))
        self.define_option(console.option.Str('status'))

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
            raise console.error.MissingArgument('auth@login_required')

        user = None
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

            status = self.opt('status')
            if status:
                user.status = status
                user.save()

            # Prompt for a password
            console.run_command('auth:passwd', arguments=[login])

            console.print_success(lang.t('auth@user_created', {'login': login}))

        except Exception as e:
            # Delete not completely created user
            if user:
                user.delete()

            raise console.error.CommandExecutionError(e)


class UserMod(console.Command):
    """auth:usermod Console Command
    """

    def __init__(self):
        super().__init__()

        self.define_option(console.option.Str('roles'))
        self.define_option(console.option.Str('status'))

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
            raise console.error.MissingArgument('auth@login_required')

        try:
            user = _api.get_user(login)

            roles = self.opt('roles')
            status = self.opt('status')

            # Set roles
            if roles:
                # Remove all attached roles
                for role in user.roles:
                    user.remove_role(role)

                # Add new roles
                for role_name in roles.split(',') if roles else []:
                    try:
                        user.add_role(_api.get_role(role_name))
                    except _error.RoleNotFound as e:
                        console.print_warning(e)

            # Set status
            if status:
                user.status = status

            if user.is_modified:
                user.save()
                console.print_success(lang.t('auth@user_modified', {'login': login}))

        except _error.Error as e:
            raise console.error.CommandExecutionError(e)


class Passwd(console.Command):
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
            raise console.error.MissingArgument('auth@login_required')

        try:
            user = _api.get_user(login)
        except _error.UserNotFound as e:
            raise console.error.CommandExecutionError(e)

        while True:
            pass_1 = getpass(lang.t('auth@enter_new_password', {'login': user.login}) + ': ')
            if not pass_1:
                raise console.error.CommandExecutionError(lang.t('auth@password_cannot_be_empty'))

            pass_2 = getpass(lang.t('auth@retype_password') + ': ')

            if pass_1 != pass_2:
                console.print_error(lang.t('auth@passwords_dont_match'))
            else:
                break

        try:
            user.password = pass_2
            user.save()
            console.print_success(lang.t('auth@password_successfully_changed', {'login': user.login}))

        except Exception as e:
            raise console.error.CommandExecutionError(e)


class UserDel(console.Command):
    """auth:userdel Console Command
    """

    @property
    def name(self) -> str:
        """Get command's name
        """
        return 'auth:userdel'

    @property
    def description(self) -> str:
        """Get command's description
        """
        return 'auth@userdel_console_command_description'

    def exec(self):
        """Execute the command
        """
        login = self.arg(0)
        if not login:
            raise console.error.MissingArgument('auth@login_required')

        try:
            _api.get_user(login).delete()

            console.print_success(lang.t('auth@user_deleted', {'login': login}))

        except _error.Error as e:
            raise console.error.CommandExecutionError(e)
