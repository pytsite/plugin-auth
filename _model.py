"""PytSite Auth Plugin Data Models
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Union as _Union, Tuple as _Tuple, List as _List, Any as _Any
from datetime import datetime as _datetime
from pytz import timezone as _timezone
from pytsite import router as _router, util as _util
from plugins import permissions as _permissions, geo_ip as _geo_ip, file as _file

ANONYMOUS_USER_LOGIN = 'anonymous@anonymous.anonymous'
SYSTEM_USER_LOGIN = 'system@system.system'


class AuthEntity(_ABC):
    """Abstract Auth Entity Model
    """

    @property
    @_abstractmethod
    def uid(self) -> str:
        """Get UID of the entity.
        """
        raise NotImplementedError()

    @property
    @_abstractmethod
    def is_modified(self) -> str:
        raise NotImplementedError()

    @_abstractmethod
    def save(self):
        pass

    @_abstractmethod
    def delete(self):
        pass

    @_abstractmethod
    def has_field(self, field_name: str) -> bool:
        pass

    @_abstractmethod
    def get_field(self, field_name: str, **kwargs) -> _Any:
        pass

    @_abstractmethod
    def set_field(self, field_name: str, value):
        pass

    @_abstractmethod
    def add_to_field(self, field_name: str, value):
        pass

    @_abstractmethod
    def remove_from_field(self, field_name: str, value):
        pass


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
    def is_dev(self) -> bool:
        """Check if the user has the 'admin' role.
        """
        return self.has_role('dev')

    @property
    def is_admin(self) -> bool:
        """Check if the user has the 'admin' role.
        """
        return self.has_role('admin')

    @property
    def is_online(self) -> bool:
        return (_datetime.now() - self.last_activity).seconds < 180

    @is_online.setter
    def is_online(self, value):
        raise AttributeError("'is_online' attribute is read only.")

    @property
    def geo_ip(self) -> _geo_ip.GeoIP:
        try:
            return _geo_ip.resolve(self.last_ip)
        except _geo_ip.error.ResolveError:
            return _geo_ip.resolve('0.0.0.0')

    @geo_ip.setter
    def geo_ip(self, value):
        raise AttributeError("'geo_ip' attribute is read only.")

    @property
    def created(self) -> _datetime:
        return self.get_field('created')

    @created.setter
    def created(self, value):
        raise AttributeError("'created' attribute is read only.")

    @property
    def login(self) -> str:
        return self.get_field('login')

    @login.setter
    def login(self, value: str):
        self.set_field('login', value)

    @property
    def email(self) -> str:
        return self.get_field('email')

    @email.setter
    def email(self, value: str):
        self.set_field('email', value)

    @property
    def password(self) -> str:
        return self.get_field('password')

    @password.setter
    def password(self, value: str):
        self.set_field('password', value)

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
    def last_name(self) -> str:
        return self.get_field('last_name')

    @last_name.setter
    def last_name(self, value: str):
        self.set_field('last_name', value)

    @property
    def full_name(self) -> str:
        return self.first_name + ' ' + self.last_name

    @full_name.setter
    def full_name(self, value):
        raise AttributeError("'full_name' attribute is read only")

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

    @localtime.setter
    def localtime(self, value):
        raise AttributeError("'localtime' attribute is read only.")

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
    def urls(self) -> tuple:
        return self.get_field('urls')

    @urls.setter
    def urls(self, value: tuple):
        self.set_field('urls', value)

    @property
    def profile_is_public(self) -> bool:
        return self.get_field('profile_is_public')

    @profile_is_public.setter
    def profile_is_public(self, value: bool):
        self.set_field('profile_is_public', value)

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
    def city(self) -> str:
        return self.get_field('city')

    @city.setter
    def city(self, value: str):
        self.set_field('city', value)

    @property
    def profile_edit_url(self) -> str:
        return _router.rule_url('auth_ui@profile_edit', {'nickname': self.nickname})

    def add_role(self, role: AbstractRole):
        """
        :rtype: AbstractUser
        """
        return self.add_to_field('roles', role)

    def remove_role(self, role: AbstractRole):
        """
        :rtype: AbstractUser
        """
        return self.remove_from_field('roles', role)

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
        return self.remove_from_field('follows', self._check_user(user_to_unfollow))

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
        return self.remove_from_field('blocked_users', self._check_user(user))

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
        # System user has all permissions
        if self.is_system:
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

    def save(self):
        if self.is_anonymous:
            raise RuntimeError('Anonymous user cannot be saved')

        if self.is_system:
            raise RuntimeError('System user cannot be saved')

        return self

    def delete(self):
        for user in self.follows:
            self.remove_follows(user)

        for user in self.blocked_users:
            self.remove_blocked_user(user)

        return self

    def as_jsonable(self, **kwargs):
        from . import _api
        current_user = _api.get_current_user()

        r = {
            'uid': self.uid,
        }

        if self.profile_is_public or current_user == self or current_user.is_admin:
            r.update({
                'nickname': self.nickname,
                'picture': {
                    'url': self.picture.get_url(),
                    'width': self.picture.width,
                    'height': self.picture.height,
                    'length': self.picture.length,
                    'mime': self.picture.mime,
                },
                'first_name': self.first_name,
                'last_name': self.last_name,
                'full_name': self.full_name,
                'timezone': self.timezone,
                'birth_date': _util.w3c_datetime_str(self.birth_date),
                'gender': self.gender,
                'phone': self.phone,
                'urls': self.urls,
                'follows_count': self.follows_count,
                'followers_count': self.followers_count,
                'is_follows': self.is_follows(current_user),
                'is_followed': self.is_followed(current_user),
            })

        if current_user == self or current_user.is_admin:
            r.update({
                'created': _util.w3c_datetime_str(self.created),
                'login': self.login,
                'email': self.email,
                'last_sign_in': _util.w3c_datetime_str(self.last_sign_in),
                'last_activity': _util.w3c_datetime_str(self.last_activity),
                'sign_in_count': self.sign_in_count,
                'status': self.status,
                'profile_is_public': self.profile_is_public,
            })

        return r

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other.uid == self.uid
