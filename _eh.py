"""PytSite Auth Plugin Events Handlers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang, console as _console
from . import _api, _error, _driver


def register_storage_driver(driver: _driver.Storage):
    # Create/update minimum set of built-in roles
    for name in ('anonymous', 'user', 'admin', 'dev'):
        try:
            # Check for role and its valid description
            role = _api.get_storage_driver().get_role(name)
            valid_desc = 'auth@{}_role_description'.format(name)
            if role.description != valid_desc:
                _api.switch_user_to_system()
                role.description = valid_desc
                role.save()
                _api.restore_user()

        except _error.RoleNotFound:
            # Create role
            _api.switch_user_to_system()
            _api.get_storage_driver().create_role(name, 'auth@{}_role_description'.format(name)).save()
            _console.print_info(_lang.t('auth@role_created', {'name': name}))
            _api.restore_user()
