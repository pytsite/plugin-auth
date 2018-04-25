"""PytSite Auth Plugin Validation Rules
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import validation as _validation
from plugins import query as _query
from . import _api, _error


class UserFieldUnique(_validation.Rule):
    def __init__(self, value=None, msg_id: str = None, msg_args: dict = None, **kwargs):
        super().__init__(value, msg_id, msg_args)

        self._field_name = kwargs.get('field_name')
        if not self._field_name:
            raise RuntimeError("'field_name' argument is required")

        self._q = _query.Query()

        self._exclude_uids = kwargs.get('exclude_uids', ())
        if self._exclude_uids:
            if not isinstance(self._exclude_uids, (list, tuple)):
                self._exclude_uids = (self._exclude_uids,)
            self._q.add(_query.Nin('uid', self._exclude_uids))

    def _do_validate(self):
        self._q.add(_query.Eq(self._field_name, self.value))
        if _api.find_user(self._q):
            raise _validation.RuleError('auth@{}_already_taken'.format(self._field_name), {'value': self.value})
