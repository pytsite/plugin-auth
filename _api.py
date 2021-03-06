"""PytSite Auth Plugin API Functions
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Dict, Iterator, List, Tuple, Optional
from collections import OrderedDict
from datetime import datetime, timedelta
from pytsite import reg, lang, cache, events, util, validation, threading
from plugins import query
from . import _error, _model, _driver

USER_STATUS_ACTIVE = 'active'
USER_STATUS_WAITING = 'waiting'
USER_STATUS_DISABLED = 'disabled'

_authentication_drivers = OrderedDict()  # type: Dict[str, _driver.Authentication]
_storage_driver = None  # type: _driver.Storage

_permission_groups = []
permissions = []
_anonymous_user = None
_system_user = None
_access_tokens = cache.create_pool('auth.access_tokens')  # token: token_info
_user_access_tokens = cache.create_pool('auth.user_access_tokens')  # user.uid: tokens
_current_user = {}  # Current users, per thread
_previous_user = {}  # Previous users, per thread
_access_token_ttl = reg.get('auth.access_token_ttl', 86400)  # 24 hours

user_login_rule = validation.rule.Regex(msg_id='auth@login_str_rules',
                                        pattern='^[A-Za-z0-9][A-Za-z0-9.\-_@]{1,64}$')
user_nickname_rule = validation.rule.Regex(msg_id='auth@nickname_str_rules',
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


def get_auth_drivers() -> Dict[str, _driver.Authentication]:
    """Get all registered authentication drivers
    """
    return _authentication_drivers


def get_auth_driver(name: str = None) -> _driver.Authentication:
    """Get driver instance
    """
    if name is None:
        if _authentication_drivers:
            name = reg.get('auth.auth_driver')
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

    events.fire('auth@register_storage_driver', driver=driver)


def on_register_storage_driver(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@register_storage_driver', handler, priority)


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
        raise _error.UserCreateError(lang.t('auth@login_str_rules'))

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
            except validation.error.RuleError as e:
                raise _error.UserCreateError(e)

    # Create user
    user = get_storage_driver().create_user(login, password)

    # Attach roles
    if login not in (_model.ANONYMOUS_USER_LOGIN, _model.SYSTEM_USER_LOGIN):
        # Set user's status
        user.status = get_new_user_status()

        # Generate confirmation hash
        if is_sign_up_confirmation_required():
            user.is_confirmed = False

        user.roles = [get_role(r) for r in get_new_user_roles()]
        user.save()

        events.fire('auth@user_create', user=user)

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


def get_admin_users(sort: List[Tuple[str, int]] = None, active_only: bool = True) -> Iterator[_model.AbstractUser]:
    """Get admin users
    """
    if sort is None:
        sort = [('created', 1)]

    q = query.Query(query.Eq('roles', get_role('admin')))
    if active_only:
        q.add(query.Eq('status', 'active'))

    return find_users(q, sort)


def get_admin_user(sort: List[Tuple[str, int]] = None, active_only: bool = True) -> _model.AbstractUser:
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


def sign_in(auth_driver_name: str = None, data: dict = None) -> _model.AbstractUser:
    """Authenticate user
    """
    # Get user from driver
    user = get_auth_driver(auth_driver_name).sign_in(data)

    if user.status != USER_STATUS_ACTIVE:
        raise _error.UserNotActive()

    if is_sign_up_confirmation_required() and not (user.is_confirmed or user.is_admin):
        raise _error.UserNotConfirmed()

    switch_user(user)

    # Update statistics
    user.sign_in_count += 1
    user.last_sign_in = datetime.now()
    user.save()

    # Login event
    events.fire('auth@sign_in', user=user)

    return user


def get_access_token_info(token: str) -> dict:
    """Get access token's metadata
    """
    try:
        return _access_tokens.get(token)

    except cache.error.KeyNotExist:
        raise _error.InvalidAccessToken('Invalid access token')


def generate_access_token(user: _model.AbstractUser) -> str:
    """Generate a new access token
    """
    while True:
        token = util.random_str(32)

        if not _access_tokens.has(token):
            now = datetime.now()
            t_info = {
                'user_uid': user.uid,
                'ttl': _access_token_ttl,
                'created': now,
                'expires': now + timedelta(seconds=_access_token_ttl),
            }

            _access_tokens.put(token, t_info, _access_token_ttl)

            try:
                user_tokens = _user_access_tokens.get(user.uid)  # type: list
                user_tokens.append(token)
                _user_access_tokens.put(user.uid, user_tokens)
            except cache.error.KeyNotExist:
                _user_access_tokens.put(user.uid, [token])

            return token


def get_user_access_tokens(user: _model.AbstractUser) -> List[str]:
    """Get user's access tokens
    """
    try:
        return _user_access_tokens.get(user.uid)
    except cache.error.KeyNotExist:
        return []


def revoke_access_token(token: str):
    """Revoke an access token
    """
    if not token or not _access_tokens.has(token):
        raise _error.InvalidAccessToken('Invalid access token')

    user_uid = get_access_token_info(token)['user_uid']
    user_tokens = _user_access_tokens.get(user_uid)  # type: List[str]
    user_tokens.remove(token)
    _user_access_tokens.put(user_uid, user_tokens)

    _access_tokens.rm(token)


def revoke_user_access_tokens(user: _model.AbstractUser):
    """Revoke all user access tokens
    """
    # Revoke user access tokens
    for token in _user_access_tokens.rm(user.uid):
        revoke_access_token(token)


def prolong_access_token(token: str):
    """Prolong an access token
    """
    token_info = get_access_token_info(token)
    token_info['expires'] = datetime.now() + timedelta(seconds=_access_token_ttl),
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
        events.fire('auth@sign_out', user=user)

    finally:
        # Set anonymous user as current
        switch_user_to_anonymous()


def get_current_user() -> _model.AbstractUser:
    """Get current user
    """
    user = _current_user.get(threading.get_id()) or _current_user.get(threading.get_parent_id())
    if not user:
        user = switch_user_to_anonymous()

    return user


def get_previous_user() -> _model.AbstractUser:
    """Get previous user
    """
    tid = threading.get_id()
    p_tid = threading.get_parent_id()

    user = _previous_user.get(tid) or _current_user.get(p_tid) or _previous_user.get(p_tid)
    if not user:
        user = get_anonymous_user()
        _previous_user[threading.get_id()] = user

    return user


def switch_user(user: _model.AbstractUser):
    """Switch current user
    """
    tid = threading.get_id()
    p_tid = threading.get_parent_id()

    _previous_user[tid] = _current_user.get(tid) or _current_user.get(p_tid) or get_anonymous_user()
    _current_user[tid] = user

    return user


def restore_user() -> _model.AbstractUser:
    """Switch back to the previous user
    """
    return switch_user(get_previous_user())


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
        ('active', lang.t('auth@status_active')),
        ('waiting', lang.t('auth@status_waiting')),
        ('disabled', lang.t('auth@status_disabled')),
    )


def get_new_user_status() -> str:
    """Get status of newly created user
    """
    return reg.get('auth.new_user_status', 'waiting')


def get_new_user_roles() -> list:
    """Get default roles of newly created user
    """
    return reg.get('auth.new_user_roles', ['user'])


def find_users(query: query.Query = None, sort: List[Tuple[str, int]] = None, limit: int = 0,
               skip: int = 0) -> Iterator[_model.AbstractUser]:
    """Find users
    """
    return get_storage_driver().find_users(query, sort, limit, skip)


def find_user(query: query.Query = None, sort: List[Tuple[str, int]] = None, limit: int = 0,
              skip: int = 0) -> Optional[_model.AbstractUser]:
    try:
        return next(find_users(query, sort, limit, skip))
    except StopIteration:
        return None


def find_roles(query: query.Query = None, sort: List[Tuple[str, int]] = None, limit: int = 0,
               skip: int = 0) -> Iterator[_model.AbstractRole]:
    """Get roles iterable
    """
    return get_storage_driver().find_roles(query, sort, limit, skip)


def find_role(query: query.Query = None, sort: List[Tuple[str, int]] = None, limit: int = 0,
              skip: int = 0) -> Optional[_model.AbstractRole]:
    try:
        return next(find_roles(query, sort, limit, skip))
    except StopIteration:
        return None


def count_users(query: query.Query = None) -> int:
    """Count users
    """
    return get_storage_driver().count_users(query)


def count_roles(query: query.Query = None) -> int:
    """Count roles
    """
    return get_storage_driver().count_roles(query)


def is_sign_up_enabled() -> bool:
    """Check if the registration of new users is allowed
    """
    return reg.get('auth.signup_enabled', False)


def is_sign_up_confirmation_required() -> bool:
    """Check if the confirmation of the registration of new users is required
    """
    return reg.get('auth.signup_confirmation_required', True)


def is_sign_up_admins_notification_enabled() -> bool:
    """Check if the notification of admins about new users registration is enabled
    """
    return reg.get('auth.signup_admins_notification_enabled', True)


def is_user_status_change_notification_enabled() -> bool:
    """Check if the notification of the user status change si enabled
    """
    return reg.get('auth.user_status_change_notification_enabled', True)


def sign_up(auth_driver_name: str = None, data: dict = None) -> _model.AbstractUser:
    """Register a new user
    """
    if not is_sign_up_enabled():
        raise _error.SignupDisabled()

    user = get_auth_driver(auth_driver_name).sign_up(data)

    events.fire('auth@sign_up', user=user)

    return user


def on_sign_up(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@sign_up', handler, priority)


def on_sign_in(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@sign_in', handler, priority)


def on_sign_out(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@sign_out', handler, priority)


def on_role_pre_save(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@role_pre_save', handler, priority)


def on_role_save(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@role_save', handler, priority)


def on_role_pre_delete(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@role_pre_delete', handler, priority)


def on_role_delete(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@role_delete', handler, priority)


def on_user_create(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_create', handler, priority)


def on_user_status_change(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_status_change', handler, priority)


def on_user_pre_save(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_pre_save', handler, priority)


def on_user_save(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_save', handler, priority)


def on_user_pre_delete(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_pre_delete', handler, priority)


def on_user_delete(handler, priority: int = 0):
    """Shortcut
    """
    events.listen('auth@user_delete', handler, priority)


def on_user_as_jsonable(handler, priority: int = 0):
    events.listen('auth@user_as_jsonable', handler, priority)
