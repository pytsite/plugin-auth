"""PytSite Auth Plugin
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _error as error, _model as model, _driver as driver
from ._api import get_current_user, get_user_statuses, get_user, create_user, get_role, register_auth_driver, \
    user_nickname_rule, sign_in, get_auth_driver, create_role, verify_password, hash_password, sign_out, \
    get_access_token_info, switch_user, get_anonymous_user, get_system_user, find_users, find_user, \
    get_storage_driver, count_users, count_roles, get_admin_user, find_roles, find_role, switch_user_to_system, \
    switch_user_to_anonymous, restore_user, generate_access_token, prolong_access_token, register_storage_driver, \
    get_auth_drivers, revoke_access_token, is_sign_up_enabled, sign_up, on_register_storage_driver, \
    is_sign_up_confirmation_required, get_new_user_status, is_sign_up_admins_notification_enabled, get_admin_users, \
    on_role_pre_save, on_role_save, on_role_pre_delete, on_role_delete, on_user_pre_save, on_user_save, \
    on_user_create, on_user_pre_delete, on_user_delete
from ._model import AuthEntity, AbstractRole, AbstractUser


def plugin_load():
    """Init wrapper
    """
    from pytsite import lang
    from plugins import permissions
    from . import _eh

    # Resources
    lang.register_package(__name__)

    # Module permission group
    permissions.define_group('security', 'auth@security')

    # Events handlers
    on_register_storage_driver(_eh.register_storage_driver)


def plugin_load_console():
    from pytsite import console
    from . import _cc

    # Console commands
    console.register_command(_cc.UserAdd())
    console.register_command(_cc.UserMod())
    console.register_command(_cc.Passwd())
