"""PytSite Auth Plugin Validation Rules
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import validation
from plugins import query
from . import _api


class AuthEntityFieldUnique(validation.Rule):
    def __init__(self, value=None, msg_id: str = None, msg_args: dict = None, **kwargs):
        super().__init__(value, msg_id, msg_args)

        self._e_type = kwargs.get('e_type')
        if not self._e_type:
            raise RuntimeError("'e_type' argument is required")

        self._field_name = kwargs.get('field_name')
        if not self._field_name:
            raise RuntimeError("'field_name' argument is required")

        self._q = query.Query()

        self._exclude_uids = kwargs.get('exclude_uids', ())
        if self._exclude_uids:
            if not isinstance(self._exclude_uids, (list, tuple)):
                self._exclude_uids = (self._exclude_uids,)
            self._q.add(query.Nin('uid', self._exclude_uids))

    def _do_validate(self):
        self._q.add(query.Eq(self._field_name, self.value))

        if self._e_type == 'role':
            if _api.find_role(self._q):
                raise validation.RuleError('auth@{}_{}_already_taken'.
                                           format(self._e_type, self._field_name), {'value': self.value})
        elif self._e_type == 'user':
            if _api.find_user(self._q):
                raise validation.RuleError('auth@{}_{}_already_taken'.
                                           format(self._e_type, self._field_name), {'value': self.value})
