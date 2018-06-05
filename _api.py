"""PytSite Auth Plugin API Functions
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Dict as _Dict, Iterator as _Iterator, List as _List, Tuple as _Tuple, Optional as _Optional
from collections import OrderedDict as _OrderedDict
from datetime import datetime as _datetime, timedelta as _timedelta
from pytsite import reg as _reg, lang as _lang, router as _router, cache as _cache, events as _events, util as _util, \
    validation as _validation, threading as _threading
from plugins import query as _query
from . import _error, _model, _driver

USER_STATUS_ACTIVE = 'active'
USER_STATUS_WAITING = 'waiting'
USER_STATUS_DISABLED = 'disabled'

_authentication_drivers = _OrderedDict()  # type: _Dict[str, _driver.Authentication]
_storage_driver = None  # type: _driver.Storage

_permission_groups = []
_permissions = []
_anonymous_user = None
_system_user = None
_access_tokens = _cache.create_pool('auth.token_user')  # user.uid: token
_current_user = {}  # Current users, per thread
_previous_user = {}  # Previous users, per thread
_access_token_ttl = _reg.get('auth.access_token_ttl', 86400)  # 24 hours

user_login_rule = _validation.rule.Regex(msg_id='auth@login_str_rules',
                                         pattern='^[A-Za-z0-9][A-Za-z0-9.\-_@]{1,64}$')
user_nickname_rule = _validation.rule.Regex(msg_id='auth@nickname_str_rules',
                                            pattern='^[A-Za-z0-9][A-Za-z0-9.\-_]{0,31}$')


def hash_password(secret: str) -> str:
    """Hash a password
    """
    from werkzeug.security import generate_password_hash
    return generate_password_hash(str(secret))


def verify_password(clear_text: str, hashed: str) -> bool:
    """Verify hashed password
    """
    from werkzeug.security import check_password_hash
    return check_password_hash(str(hashed), str(clear_text))


def register_auth_driver(driver: _driver.Authentication):
    """Register authentication driver
    """
    if not isinstance(driver, _driver.Authentication):
        raise TypeError('Instance of auth.driver.Authentication expected.')

    name = driver.get_name()
    if name in _authentication_drivers:
        raise RuntimeError("Authentication driver '{}' is already registered.".format(name))

    _authentication_drivers[name] = driver


def get_auth_drivers() -> _Dict[str, _driver.Authentication]:
    """Get all registered authentication drivers
    """
    return _authentication_drivers


def get_auth_driver(name: str = None) -> _driver.Authentication:
    """Get driver instance
    """
    if name is None:
        if _authentication_drivers:
            name = _reg.get('auth.auth_driver')
            if not name or name not in _authentication_drivers:
                name = list(_authentication_drivers)[-1]
        else:
            raise _error.NoDriverRegistered('No authentication driver registered')

    if name not in _authentication_drivers:
        raise _error.DriverNotRegistered("Authentication driver '{}' is not registered.".format(name))

    return _authentication_drivers[name]


def register_storage_driver(driver: _driver.Storage):
    """Register storage driver
    """
    global _storage_driver

    if _storage_driver:
        raise _error.DriverRegistered('Storage driver is already registered')

    if not isinstance(driver, _driver.Storage):
        raise TypeError('Instance of {} expected'.format(type(_driver.Storage)))

    _storage_driver = driver

    _events.fire('auth@register_storage_driver', driver=driver)


def on_register_storage_driver(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@register_storage_driver', handler, priority)


def get_storage_driver() -> _driver.Storage:
    """Get driver instance
    """
    # Load storage driver if it is not loaded yet
    if not _storage_driver:
        raise _error.NoDriverRegistered('No storage driver registered')

    return _storage_driver


def create_user(login: str, password: str = None) -> _model.AbstractUser:
    """Create a new user
    """
    if not login:
        raise _error.UserCreateError(_lang.t('auth@login_str_rules'))

    # Various checks
    if login not in (_model.ANONYMOUS_USER_LOGIN, _model.SYSTEM_USER_LOGIN):
        try:
            # Check user existence
            get_user(login)
            raise _error.UserExists()

        except _error.UserNotFound:
            # Check user login
            try:
                user_login_rule.validate(login)
            except _validation.error.RuleError as e:
                raise _error.UserCreateError(e)

    # Create user
    user = get_storage_driver().create_user(login, password)

    # Attach roles
    if login not in (_model.ANONYMOUS_USER_LOGIN, _model.SYSTEM_USER_LOGIN):
        # Set user's status
        user.status = get_new_user_status()

        # Generate confirmation hash
        if is_sign_up_confirmation_required():
            user.confirmation_hash = _util.random_str(64)

        user.roles = [get_role(r) for r in get_new_user_roles()]
        user.save()

        _events.fire('auth@user_create', user=user)

    else:
        user.status = USER_STATUS_ACTIVE
        user.roles = [get_role('anonymous')]

    return user


def get_user(login: str = None, nickname: str = None, uid: str = None, access_token: str = None) -> _model.AbstractUser:
    """Get user
    """
    # Convert access token to user UID
    if access_token:
        return get_user(uid=get_access_token_info(access_token)['user_uid'])

    # Retrieve user from storage driver
    user = get_storage_driver().get_user(login, nickname, uid)
    if not user:
        raise _error.UserNotFound()

    # Sign out non-active users
    if user == get_current_user() and user.status != USER_STATUS_ACTIVE:
        sign_out(user)

    return user


def get_admin_users(sort: _List[_Tuple[str, int]] = None, active_only: bool = True) -> _Iterator[_model.AbstractUser]:
    """Get admin users
    """
    if sort is None:
        sort = [('created', 1)]

    q = _query.Query(_query.Eq('roles', get_role('admin')))
    if active_only:
        q.add(_query.Eq('status', 'active'))

    return find_users(q, sort)


def get_admin_user(sort: _List[_Tuple[str, int]] = None, active_only: bool = True) -> _model.AbstractUser:
    """Get first admin user
    """
    try:
        return next(get_admin_users(sort, active_only))
    except StopIteration:
        raise _error.UserNotFound()


def get_anonymous_user() -> _model.AbstractUser:
    """Get anonymous user
    """
    global _anonymous_user
    if not _anonymous_user:
        _anonymous_user = create_user(_model.ANONYMOUS_USER_LOGIN)

    return _anonymous_user


def get_system_user() -> _model.AbstractUser:
    """Get system user
    """
    global _system_user
    if not _system_user:
        _system_user = create_user(_model.SYSTEM_USER_LOGIN)

    return _system_user


def create_role(name: str, description: str = ''):
    """Create a new role
    """
    try:
        get_role(name)
        raise _error.RoleAlreadyExists(name)

    except _error.RoleNotFound:
        return get_storage_driver().create_role(name, description)


def get_role(name: str = None, uid: str = None) -> _model.AbstractRole:
    """Get a role
    """
    return get_storage_driver().get_role(name, uid)


def sign_in(auth_driver_name: str, data: dict) -> _model.AbstractUser:
    """Authenticate user
    """
    # Get user from driver
    user = get_auth_driver(auth_driver_name).sign_in(data)

    if user.status != USER_STATUS_ACTIVE:
        raise _error.UserNotActive()

    switch_user(user)

    # Update statistics
    user.sign_in_count += 1
    user.last_sign_in = _datetime.now()
    user.save()

    if _router.request():
        # Set session marker
        _router.session()['auth.login'] = user.login

        # Update IP address and geo data
        user.last_ip = _router.request().remote_addr
        geo_ip = user.geo_ip
        if not user.timezone:
            user.timezone = geo_ip.timezone
        if not user.country:
            user.country = geo_ip.country
        if not user.city:
            user.city = geo_ip.city

        user.save()

    # Login event
    _events.fire('auth@sign_in', user=user)

    return user


def get_access_token_info(token: str) -> dict:
    """Get access token's metadata
    """
    try:
        return _access_tokens.get(token)

    except _cache.error.KeyNotExist:
        raise _error.InvalidAccessToken('Invalid access token')


def generate_access_token(user: _model.AbstractUser) -> str:
    """Generate a new access token
    """
    while True:
        token = _util.random_str(32)

        if not _access_tokens.has(token):
            now = _datetime.now()
            t_info = {
                'user_uid': user.uid,
                'ttl': _access_token_ttl,
                'created': now,
                'expires': now + _timedelta(seconds=_access_token_ttl),
            }
            _access_tokens.put(token, t_info, _access_token_ttl)

            return token


def revoke_access_token(token: str):
    """Revoke an access token
    """
    if not token or not _access_tokens.has(token):
        raise _error.InvalidAccessToken('Invalid access token')

    _access_tokens.rm(token)


def prolong_access_token(token: str):
    """Prolong an access token
    """
    token_info = get_access_token_info(token)
    _access_tokens.put(token, token_info, _access_token_ttl)


def sign_out(user: _model.AbstractUser):
    """Sign out a user
    """
    # Anonymous user cannot be signed out
    if user.is_anonymous:
        return

    try:
        # All operation on current user perform on behalf of system user
        switch_user_to_system()

        # Ask drivers to perform necessary operations
        for driver in _authentication_drivers.values():
            driver.sign_out(user)

        # Notify listeners
        _events.fire('auth@sign_out', user=user)

    finally:
        # Set anonymous user as current
        switch_user_to_anonymous()


def get_current_user() -> _model.AbstractUser:
    """Get currently signed in user
    """
    user = _current_user.get(_threading.get_id())
    if user:
        return user

    return switch_user_to_anonymous()


def switch_user(user: _model.AbstractUser):
    """Switch current user
    """
    tid = _threading.get_id()
    _previous_user[tid] = _current_user[tid] if tid in _current_user else get_anonymous_user()
    _current_user[tid] = user

    return user


def restore_user() -> _model.AbstractUser:
    """Switch back to the previous user
    """
    tid = _threading.get_id()
    _current_user[tid] = _previous_user[tid] if tid in _previous_user else get_anonymous_user()

    return _current_user[tid]


def switch_user_to_system() -> _model.AbstractUser:
    """Shortcut
    """
    return switch_user(get_system_user())


def switch_user_to_anonymous() -> _model.AbstractUser:
    """Shortcut
    """
    return switch_user(get_anonymous_user())


def get_user_statuses() -> tuple:
    """Get valid user statuses
    """
    return (
        ('active', _lang.t('auth@status_active')),
        ('waiting', _lang.t('auth@status_waiting')),
        ('disabled', _lang.t('auth@status_disabled')),
    )


def get_new_user_status() -> str:
    """Get status of newly created user
    """
    return _reg.get('auth.new_user_status', 'waiting')


def get_new_user_roles() -> list:
    """Get default roles of newly created user
    """
    return _reg.get('auth.new_user_roles', ['user'])


def find_users(query: _query.Query = None, sort: _List[_Tuple[str, int]] = None, limit: int = 0,
               skip: int = 0) -> _Iterator[_model.AbstractUser]:
    """Find users
    """
    return get_storage_driver().find_users(query, sort, limit, skip)


def find_user(query: _query.Query = None, sort: _List[_Tuple[str, int]] = None, limit: int = 0,
              skip: int = 0) -> _Optional[_model.AbstractUser]:
    try:
        return next(find_users(query, sort, limit, skip))
    except StopIteration:
        return None


def find_roles(query: _query.Query = None, sort: _List[_Tuple[str, int]] = None, limit: int = 0,
               skip: int = 0) -> _Iterator[_model.AbstractRole]:
    """Get roles iterable
    """
    return get_storage_driver().find_roles(query, sort, limit, skip)


def find_role(query: _query.Query = None, sort: _List[_Tuple[str, int]] = None, limit: int = 0,
              skip: int = 0) -> _Optional[_model.AbstractRole]:
    try:
        return next(find_roles(query, sort, limit, skip))
    except StopIteration:
        return None


def count_users(query: _query.Query = None) -> int:
    """Count users
    """
    return get_storage_driver().count_users(query)


def count_roles(query: _query.Query = None) -> int:
    """Count roles
    """
    return get_storage_driver().count_roles(query)


def is_sign_up_enabled() -> bool:
    """Check if the registration of new users is allowed
    """
    return _reg.get('auth.signup_enabled', False)


def is_sign_up_confirmation_required() -> bool:
    """Check if the confirmation of the registration of new users is required
    """
    return _reg.get('auth.signup_confirmation_required', True)


def is_sign_up_admins_notification_enabled() -> bool:
    """Check if the notification of admins about new users registration is enabled
    """
    return _reg.get('auth.signup_admins_notification_enabled', True)


def is_user_status_change_notification_enabled() -> bool:
    """Check if the notification of the user status change si enabled
    """
    return _reg.get('auth.user_status_change_notification_enabled', True)


def sign_up(auth_driver_name: str, data: dict) -> _model.AbstractUser:
    """Register a new user
    """
    if not is_sign_up_enabled():
        raise _error.SignupDisabled()

    user = get_auth_driver(auth_driver_name).sign_up(data)

    return user


def on_role_pre_save(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@role_pre_save', handler, priority)


def on_role_save(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@role_save', handler, priority)


def on_role_pre_delete(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@role_pre_delete', handler, priority)


def on_role_delete(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@role_delete', handler, priority)


def on_user_create(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_create', handler, priority)


def on_user_status_change(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_status_change', handler, priority)


def on_user_pre_save(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_pre_save', handler, priority)


def on_user_save(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_save', handler, priority)


def on_user_pre_delete(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_pre_delete', handler, priority)


def on_user_delete(handler, priority: int = 0):
    """Shortcut
    """
    _events.listen('auth@user_delete', handler, priority)
