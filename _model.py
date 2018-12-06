"""PytSite Auth Plugin Data Models
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Union as _Union, Tuple as _Tuple, List as _List, Any as _Any
from datetime import datetime as _datetime
from pytz import timezone as _timezone
from pytsite import util as _util, events as _events, errors as _errors, lang as _lang
from plugins import permissions as _permissions, geo_ip as _geo_ip, file as _file, query as _query

ANONYMOUS_USER_LOGIN = 'anonymous@anonymous.anonymous'
SYSTEM_USER_LOGIN = 'system@system.system'
LOGIN_MAX_LENGTH = 50
NICKNAME_MAX_LENGTH = 50
FIRST_NAME_MAX_LENGTH = 50
MIDDLE_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50
USER_POSITION_MAX_LENGTH = 50
COUNTRY_MAX_LENGTH = 50
POSTAL_CODE_MAX_LENGTH = 10
REGION_MAX_LENGTH = 50
CITY_MAX_LENGTH = 50
STREET_MAX_LENGTH = 100
HOUSE_NUMBER_MAX_LENGTH = 10
APT_NUMBER_MAX_LENGTH = 10
PHONE_MAX_LENGTH = 20
USER_DESCRIPTION_MAX_LENGTH = 4096


class AuthEntity(_ABC):
    """Abstract Auth Entity Model
    """

    @property
    def uid(self) -> str:
        """Get UID of the entity
        """
        return self.get_field('uid')

    @property
    @_abstractmethod
    def is_new(self) -> bool:
        raise NotImplementedError()

    @property
    @_abstractmethod
    def is_modified(self) -> str:
        raise NotImplementedError()

    @property
    @_abstractmethod
    def created(self) -> _datetime:
        raise NotImplementedError()

    @_abstractmethod
    def save(self):
        raise NotImplementedError()

    @_abstractmethod
    def delete(self):
        raise NotImplementedError()

    @_abstractmethod
    def has_field(self, field_name: str) -> bool:
        raise NotImplementedError()

    @_abstractmethod
    def get_field(self, field_name: str, **kwargs) -> _Any:
        raise NotImplementedError()

    @_abstractmethod
    def set_field(self, field_name: str, value):
        raise NotImplementedError()

    @_abstractmethod
    def add_to_field(self, field_name: str, value):
        raise NotImplementedError()

    @_abstractmethod
    def sub_from_field(self, field_name: str, value):
        raise NotImplementedError()

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other.uid == self.uid

    def __hash__(self) -> int:
        return hash(self.uid)

    def __str__(self) -> str:
        return self.uid


class AbstractRole(AuthEntity):
    """Abstract Role Model
    """

    @property
    def auth_entity_type(self) -> str:
        return 'role'

    @property
    def name(self) -> str:
        return self.get_field('name')

    @name.setter
    def name(self, value: str):
        self.set_field('name', value)

    @property
    def description(self) -> str:
        return self.get_field('description')

    @description.setter
    def description(self, value: str):
        self.set_field('description', value)

    @property
    def permissions(self) -> _Tuple:
        return self.get_field('permissions')

    @permissions.setter
    def permissions(self, value: _Union[_List, _Tuple]):
        self.set_field('permissions', value)

    def add_permission(self, perm: str):
        if perm not in self.permissions:
            self.permissions = list(self.permissions) + [_permissions.get_permission(perm)[0]]

    def remove_permission(self, perm: str):
        self.permissions = [p[0] for p in self.permissions if p[0] != perm]

    @_abstractmethod
    def do_save(self):
        """Does actual saving of the user
        """
        raise NotImplementedError()

    def save(self):
        _events.fire('auth@role_pre_save', role=self)
        self.do_save()
        _events.fire('auth@role_save', role=self)

        return self

    @_abstractmethod
    def do_delete(self):
        """Does actual deletion of the user
        """
        raise NotImplementedError()

    def delete(self):
        from . import _api

        # Check if the role is used by users
        user = _api.find_user(_query.Query(_query.Eq('roles', self)))
        if user:
            raise _errors.ForbidDeletion(_lang.t('role_used_by_user', {'role': self, 'user': user.login}))

        _events.fire('auth@role_pre_delete', user=self)
        self.do_delete()
        _events.fire('auth@role_delete', user=self)

        return self

    def __str__(self) -> str:
        return self.name


class AbstractUser(AuthEntity):
    """Abstract User Model
    """

    def _check_user(self, value):
        if isinstance(value, (list, tuple)):
            for u in value:
                self._check_user(u)

            return value

        if not isinstance(value, AbstractUser):
            raise ValueError('User expected, got {}'.format(type(value)))

        if value.is_anonymous:
            raise ValueError('Anonymous user is not allowed')

        if value.is_system:
            raise ValueError('System user is not allowed')

        if value.uid == self.uid:
            raise ValueError('Self user is not allowed')

        return value

    @property
    def auth_entity_type(self) -> str:
        return 'user'

    @property
    def is_anonymous(self) -> bool:
        """Check if the user is anonymous.
        """
        return self.login == ANONYMOUS_USER_LOGIN

    @property
    def is_system(self) -> bool:
        """Check if the user is anonymous.
        """
        return self.login == SYSTEM_USER_LOGIN

    @property
    def is_admin(self) -> bool:
        """Check if the user has the 'admin' role.
        """
        return self.has_role(['admin', 'dev'])

    @property
    def is_dev(self) -> bool:
        """Check if the user has the 'dev' role.
        """
        return self.has_role('dev')

    @property
    def is_online(self) -> bool:
        return (_datetime.now() - self.last_activity).seconds < 180

    @property
    def geo_ip(self) -> _geo_ip.GeoIP:
        try:
            return _geo_ip.resolve(self.last_ip)
        except _geo_ip.error.ResolveError:
            return _geo_ip.resolve('0.0.0.0')

    @property
    def login(self) -> str:
        return self.get_field('login')

    @login.setter
    def login(self, value: str):
        self.set_field('login', value)

    @property
    def password(self) -> str:
        return self.get_field('password')

    @password.setter
    def password(self, value: str):
        self.set_field('password', value)

    @property
    def confirmation_hash(self) -> str:
        return self.get_field('confirmation_hash')

    @confirmation_hash.setter
    def confirmation_hash(self, value: str):
        self.set_field('confirmation_hash', value)

    @property
    def is_confirmed(self) -> bool:
        return self.get_field('is_confirmed')

    @is_confirmed.setter
    def is_confirmed(self, value: bool):
        self.set_field('is_confirmed', value)

    @property
    def nickname(self) -> str:
        return self.get_field('nickname')

    @nickname.setter
    def nickname(self, value: str):
        self.set_field('nickname', value)

    @property
    def first_name(self) -> str:
        return self.get_field('first_name')

    @first_name.setter
    def first_name(self, value: str):
        self.set_field('first_name', value)

    @property
    def middle_name(self) -> str:
        return self.get_field('middle_name')

    @middle_name.setter
    def middle_name(self, value: str):
        self.set_field('middle_name', value)

    @property
    def last_name(self) -> str:
        return self.get_field('last_name')

    @last_name.setter
    def last_name(self, value: str):
        self.set_field('last_name', value)

    @property
    def full_name(self) -> str:
        return '{} {} {}'.format(self.first_name, self.middle_name, self.last_name).replace('  ', ' ')

    @property
    def first_last_name(self) -> str:
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def position(self) -> str:
        return self.get_field('position')

    @position.setter
    def position(self, value: str):
        self.set_field('position', value)

    @property
    def description(self) -> str:
        return self.get_field('description')

    @description.setter
    def description(self, value: str):
        self.set_field('description', value)

    @property
    def timezone(self) -> str:
        return self.get_field('timezone')

    @timezone.setter
    def timezone(self, value: str):
        self.set_field('timezone', value)

    @property
    def localtime(self):
        return _datetime.now(_timezone(self.timezone) if self.timezone else 'UTC')

    @property
    def birth_date(self) -> _datetime:
        return self.get_field('birth_date')

    @birth_date.setter
    def birth_date(self, value: _datetime):
        self.set_field('birth_date', value)

    @property
    def last_sign_in(self) -> _datetime:
        return self.get_field('last_sign_in')

    @last_sign_in.setter
    def last_sign_in(self, value: _datetime):
        self.set_field('last_sign_in', value)

    @property
    def last_activity(self) -> _datetime:
        return self.get_field('last_activity')

    @last_activity.setter
    def last_activity(self, value: _datetime):
        self.set_field('last_activity', value)

    @property
    def sign_in_count(self) -> int:
        return self.get_field('sign_in_count')

    @sign_in_count.setter
    def sign_in_count(self, value: int):
        self.set_field('sign_in_count', value)

    @property
    def status(self) -> str:
        return self.get_field('status')

    @status.setter
    def status(self, value: str):
        self.set_field('status', value)

    @property
    def is_active(self) -> bool:
        return self.status == 'active'

    @property
    def roles(self) -> _Tuple[AbstractRole]:
        if self.is_anonymous:
            from . import _api
            return _api.get_role('anonymous'),

        return self.get_field('roles')

    @roles.setter
    def roles(self, value: _Tuple[AbstractRole]):
        self.set_field('roles', value)

    @property
    def gender(self) -> str:
        return self.get_field('gender')

    @gender.setter
    def gender(self, value: str):
        self.set_field('gender', value)

    @property
    def phone(self) -> int:
        return self.get_field('phone')

    @phone.setter
    def phone(self, value: int):
        self.set_field('phone', value)

    @property
    def options(self) -> dict:
        return self.get_field('options')

    @options.setter
    def options(self, value: dict):
        self.set_field('options', value)

    def set_option(self, key: str, value):
        opts = dict(self.get_field('options'))
        opts[key] = value
        self.set_field('options', opts)

    def get_option(self, key: str, default=None):
        return self.options.get(key, default)

    @property
    def picture(self) -> _file.model.AbstractImage:
        return self.get_field('picture')

    @picture.setter
    def picture(self, value: _file.model.AbstractImage):
        self.set_field('picture', value)

    @property
    def cover_picture(self) -> _file.model.AbstractImage:
        return self.get_field('cover_picture')

    @cover_picture.setter
    def cover_picture(self, value: _file.model.AbstractImage):
        self.set_field('cover_picture', value)

    @property
    def urls(self) -> tuple:
        return self.get_field('urls')

    @urls.setter
    def urls(self, value: tuple):
        self.set_field('urls', value)

    @property
    def is_public(self) -> bool:
        return self.get_field('is_public')

    @is_public.setter
    def is_public(self, value: bool):
        self.set_field('is_public', value)

    @property
    def follows(self):
        """
        :return: _Iterable[AbstractUser]
        """
        return self.get_field('follows', skip=0, count=0)

    @property
    def follows_count(self) -> int:
        return self.get_field('follows_count')

    @property
    def followers(self):
        """
        :return: _Iterable[AbstractUser]
        """
        return self.get_field('followers', skip=0, count=0)

    @property
    def followers_count(self) -> int:
        return self.get_field('followers_count')

    @property
    def blocked_users(self):
        """
        :rtype: _Iterable[AbstractUser]
        """
        return self.get_field('blocked_users', skip=0, count=0)

    @property
    def blocked_users_count(self) -> int:
        return self.get_field('blocked_users_count')

    @property
    def last_ip(self) -> str:
        return self.get_field('last_ip')

    @last_ip.setter
    def last_ip(self, value: str):
        self.set_field('last_ip', value)

    @property
    def country(self) -> str:
        return self.get_field('country')

    @country.setter
    def country(self, value: str):
        self.set_field('country', value)

    @property
    def postal_code(self) -> str:
        return self.get_field('postal_code')

    @postal_code.setter
    def postal_code(self, value: str):
        self.set_field('postal_code', value)

    @property
    def region(self) -> str:
        return self.get_field('region')

    @region.setter
    def region(self, value: str):
        self.set_field('region', value)

    @property
    def city(self) -> str:
        return self.get_field('city')

    @city.setter
    def city(self, value: str):
        self.set_field('city', value)

    @property
    def street(self) -> str:
        return self.get_field('street')

    @street.setter
    def street(self, value: str):
        self.set_field('street', value)

    @property
    def house_number(self) -> str:
        return self.get_field('house_number')

    @house_number.setter
    def house_number(self, value: str):
        self.set_field('house_number', value)

    @property
    def apt_number(self) -> str:
        return self.get_field('apt_number')

    @apt_number.setter
    def apt_number(self, value: str):
        self.set_field('apt_number', value)

    def set_field(self, field_name: str, value):
        if field_name == 'status' and value != self.status and not self.is_new:
            _events.fire('auth@user_status_change', user=self, status=value)

        return self

    def add_role(self, role: AbstractRole):
        """
        :rtype: AbstractUser
        """
        return self.add_to_field('roles', role)

    def remove_role(self, role: AbstractRole):
        """
        :rtype: AbstractUser
        """
        return self.sub_from_field('roles', role)

    def is_follows(self, user_to_check) -> bool:
        """
        :type user_to_check: AbstractUser
        """
        return user_to_check in self.follows

    def is_followed(self, user_to_check) -> bool:
        """
        :type user_to_check: AbstractUser
        """
        return user_to_check in self.followers

    def add_follows(self, user_to_follow):
        """
        :type user_to_follow: AbstractUser
        :rtype: AbstractUser
        """
        return self.add_to_field('follows', self._check_user(user_to_follow))

    def remove_follows(self, user_to_unfollow):
        """
        :type user_to_unfollow: AbstractUser
        :rtype: AbstractUser
        """
        return self.sub_from_field('follows', self._check_user(user_to_unfollow))

    def add_blocked_user(self, user):
        """
        :type user: AbstractUser
        :rtype: AbstractUser
        """
        return self.add_to_field('blocked_users', self._check_user(user))

    def remove_blocked_user(self, user):
        """
        :type user: AbstractUser
        :rtype: AbstractUser
        """
        return self.sub_from_field('blocked_users', self._check_user(user))

    def has_role(self, name: _Union[str, list, tuple]) -> bool:
        """Checks if the user has a role
        """
        # System user has all roles
        if self.is_system:
            return True

        # Process list of roles
        if isinstance(name, (list, tuple)):
            for r in name:
                if self.has_role(r):
                    return True

            return False

        return name in [role.name for role in self.roles]

    def has_permission(self, name: _Union[str, list, tuple]) -> bool:
        """Checks if the user has a permission or one of the permissions
        """
        # Admins have unrestricted permissions
        if self.is_admin:
            return True

        # Process list of permissions
        if isinstance(name, (list, tuple)):
            for p in name:
                if self.has_permission(p):
                    return True

            return False

        # Checking for permission existence
        _permissions.get_permission(name)

        # Search for permission through user's roles
        for role in self.roles:
            if name in role.permissions:
                return True

        return False

    @_abstractmethod
    def do_save(self):
        """Does actual saving of the user
        """
        raise NotImplementedError()

    def save(self):
        if self.is_anonymous:
            raise RuntimeError('Anonymous user cannot be saved')

        if self.is_system:
            raise RuntimeError('System user cannot be saved')

        _events.fire('auth@user_pre_save', user=self)
        self.do_save()
        _events.fire('auth@user_save', user=self)

        return self

    @_abstractmethod
    def do_delete(self):
        """Does actual deletion of the user
        """
        raise NotImplementedError()

    def delete(self):
        _events.fire('auth@user_pre_delete', user=self)

        for user in self.follows:
            self.remove_follows(user)

        for user in self.blocked_users:
            self.remove_blocked_user(user)

        self.do_delete()

        _events.fire('auth@user_delete', user=self)

        return self

    def as_jsonable(self, **kwargs):
        from . import _api
        current_user = _api.get_current_user()

        r = {
            'uid': self.uid,
        }

        if self.is_public or current_user == self or current_user.is_admin:
            r.update({
                'nickname': self.nickname,
                'picture': {
                    'url': self.picture.get_url(
                        width=kwargs.get('picture_width', 300),
                        height=kwargs.get('picture_height', 300),
                    ),
                    'width': self.picture.width,
                    'height': self.picture.height,
                    'length': self.picture.length,
                    'mime': self.picture.mime,
                },
                'first_name': self.first_name,
                'middle_name': self.middle_name,
                'last_name': self.last_name,
                'first_last_name': self.first_last_name,
                'full_name': self.full_name,
                'timezone': self.timezone,
                'gender': self.gender,
                'urls': self.urls,
                'follows_count': self.follows_count,
                'followers_count': self.followers_count,
                'is_follows': self.is_follows(current_user),
                'is_followed': self.is_followed(current_user),
            })

            if self.cover_picture:
                r.update({
                    'cover_picture': {
                        'url': self.cover_picture.get_url(),
                        'width': self.cover_picture.width,
                        'height': self.cover_picture.height,
                        'length': self.cover_picture.length,
                        'mime': self.cover_picture.mime,
                    },
                })

        if current_user == self or current_user.is_admin:
            r.update({
                'created': _util.w3c_datetime_str(self.created),
                'login': self.login,
                'last_sign_in': _util.w3c_datetime_str(self.last_sign_in),
                'last_activity': _util.w3c_datetime_str(self.last_activity),
                'sign_in_count': self.sign_in_count,
                'status': self.status,
                'is_public': self.is_public,
                'phone': self.phone,
                'birth_date': _util.w3c_datetime_str(self.birth_date),
            })

        _events.fire('auth@user_as_jsonable', user=self, data=r)

        return r

    def __str__(self) -> str:
        return self.login
