"""PytSite Auth Plugin
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _error as error, _model as model, _driver as driver, _validation as validation
from ._api import get_current_user, get_user_statuses, get_user, create_user, get_role, register_auth_driver, \
    user_nickname_rule, sign_in, get_auth_driver, create_role, verify_password, hash_password, sign_out, \
    get_access_token_info, switch_user, get_anonymous_user, get_system_user, find_users, find_user, \
    get_storage_driver, count_users, count_roles, get_admin_user, find_roles, find_role, switch_user_to_system, \
    switch_user_to_anonymous, restore_user, generate_access_token, prolong_access_token, register_storage_driver, \
    get_auth_drivers, revoke_access_token, is_sign_up_enabled, sign_up, on_register_storage_driver, \
    is_sign_up_confirmation_required, get_new_user_status, is_sign_up_admins_notification_enabled, \
    is_user_status_change_notification_enabled, get_admin_users, on_role_pre_save, on_role_save, on_role_pre_delete, \
    on_role_delete, on_user_pre_save, on_user_save, on_user_create, on_user_pre_delete, on_user_delete, \
    on_user_status_change, get_new_user_roles, get_user_access_tokens, on_sign_in, on_sign_out, on_sign_up, \
    on_user_as_jsonable
from ._model import AuthEntity, AbstractRole, AbstractUser
from ._api import USER_STATUS_ACTIVE, USER_STATUS_WAITING, USER_STATUS_DISABLED
from ._model import SYSTEM_USER_LOGIN, ANONYMOUS_USER_LOGIN, LOGIN_MAX_LENGTH, NICKNAME_MAX_LENGTH, \
    FIRST_NAME_MAX_LENGTH, MIDDLE_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH, COUNTRY_MAX_LENGTH, POSTAL_CODE_MAX_LENGTH, \
    PROVINCE_MAX_LENGTH, CITY_MAX_LENGTH, DISTRICT_MAX_LENGTH, STREET_MAX_LENGTH, BUILDING_MAX_LENGTH, \
    APT_NUMBER_MAX_LENGTH, PHONE_MAX_LENGTH, USER_DESCRIPTION_MAX_LENGTH, USER_POSITION_MAX_LENGTH


def plugin_load():
    """Init wrapper
    """
    from pytsite import cron
    from plugins import permissions
    from . import _eh

    # Module permission group
    permissions.define_group('security', 'auth@security')

    # Events handlers
    on_register_storage_driver(_eh.on_register_storage_driver)
    cron.on_start(switch_user_to_system)
    cron.on_stop(restore_user)


def plugin_load_console():
    from pytsite import console
    from . import _cc

    # Console commands
    console.register_command(_cc.UserAdd())
    console.register_command(_cc.UserMod())
    console.register_command(_cc.Passwd())
    console.register_command(_cc.UserDel())
