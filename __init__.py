"""PytSite Authentication and Authorization Plugin
"""
# Public API
from . import _error as error, _model as model, _driver as driver
from ._api import get_current_user, get_user_statuses, get_user, create_user, get_role, register_auth_driver, \
    user_nickname_rule, sign_in, get_auth_driver, create_role, verify_password, hash_password, sign_out, \
    get_access_token_info, switch_user, get_anonymous_user, get_system_user, get_users, get_storage_driver, \
    count_users, count_roles, get_first_admin_user, get_roles, switch_user_to_system, switch_user_to_anonymous, \
    restore_user, generate_access_token, prolong_access_token, register_storage_driver, get_auth_drivers, \
    revoke_access_token, is_sign_up_enabled

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


def plugin_load():
    """Init wrapper
    """
    from pytsite import lang, console
    from plugins import permissions
    from . import _eh, _console_commands

    # Resources
    lang.register_package(__name__)

    # Module permission group
    permissions.define_group('security', 'auth@security')

    # Console commands
    console.register_command(_console_commands.UserAdd())
    console.register_command(_console_commands.Passwd())


def plugin_install():
    from pytsite import reg, lang, validation, console, util

    if reg.get('env.type') == 'console':
        # Search for an administrator
        if count_users({'roles': [get_role('admin')]}):
            return

        # Create administrator
        email = input(lang.t('auth@enter_admin_email') + ': ')
        try:
            validation.rule.NonEmpty(email, 'auth@email_cannot_be_empty').validate()
            validation.rule.Email(email).validate()
        except validation.error.RuleError as e:
            raise console.error.Error(e)

        switch_user_to_system()
        admin_user = create_user(email)
        admin_user.first_name = lang.t('auth@administrator')
        admin_user.nickname = util.transform_str_2(admin_user.full_name)
        admin_user.roles = [get_role('admin')]
        admin_user.save()
        restore_user()
        console.print_success(lang.t('auth@user_has_been_created', {'login': admin_user.login}))

        # Set password for created admin
        console.run_command('auth:passwd', arguments=[admin_user.login])
