# PytSite Authentication and Authorization Plugin


## Changelog


### 2.5 (2018-04-09)

New exception added: `error.UserNotActive`.


### 2.4 (2018-04-08)

New API function: `on_user_create()`.


### 2.3 (2018-04-08)

- New properties and methods added to `AbstractRole`: `do_save()`,
  `do_delete()`.
- New API functions added: `find_role()`, `find_user()`,
  `on_role_pre_save()`, `on_role_save()`, `on_role_pre_delete()`,
  `on_role_delete()`.


### 2.2 (2018-04-08)

- New properties and methods added to `AbstractUser`: `is_new`,
  `do_save()`, `do_delete()`.
- User-related events added.
- New API functions added: `on_user_pre_save()`, `on_user_save()`,
  `on_user_pre_delete()`, `on_user_delete()`.


### 2.1.1 (2018-04-07)

Signatures of `count_users()` and `count_roles` fixed.


### 2.1 (2018-04-07)

- New API functions: `get_admin_users()`,
  `is_sign_up_admins_notification_enabled()`.
- New property: `AbstractUser.is_confirmed`.


### 2.0 (2018-04-06)

- New API functions added: `get_new_user_status()`,
  `is_sign_up_confirmation_required()`.
- `get_first_admin_user()` renamed to `get_admin_user()` and got
  modified constructor's signature.
- `get_users()` renamed to `find_users()` and got modified constructor's
  signature.
- `get_roles()` renamed to `find_roles()` and got modified constructor's
  signature.
- Fixed a couple of minor issues.


### 1.11.2 (2018-03-28)

Unnecessary property `AbstractUser.profile_edit_url` removed.


### 1.11.1 (2018-03-24)

Location of `__eq__` moved up in model's hierarchy.


### 1.11 (2018-03-24)

`model.AuthEntity.remove_from_field()` renamed to
`model.AuthEntity.sub_from_field()`


### 1.10 (2018-02-20)

New property `AbstractUser.is_admin_or_dev` added.


### 1.9.2 (2018-02-13)

Build-in roles' description checking fixed.


### 1.9.1 (2018-02-11)

Build-in roles' description checking added.


### 1.9 (2018-02-08)

New console command added: `auth:usermod`.


### 1.8.1 (2018-02-07)

Support for PytSite-7.7.


### 1.8 (2018-01-26)

New built-in role `dev` added.


### 1.7 (2018-01-19)

- New function `sign_up()` added.
- Function `create_user()` refactored.
- Exception `SignUpError`.
- Exception `UserAlreadyExists` renamed to `UserExists`.


### 1.6 (2017-12-23)

New properties in `AbstractUser`: `timezone`, `localtime`.


### 1.5.1 (2017-12-13)

Events names fixed.


### 1.5 (2017-12-13)

Support for PytSite-7.0.


### 1.4.2 (2017-12-07)

Fixed init code.


### 1.4.1 (2017-12-07)

Fixed init code.


### 1.4 (2017-12-03)

- Added option 'roles' to the `auth:useradd` console command.
- Two exceptions renamed.


### 1.3 (2017-12-02)

Added support for last `geo_ip` plugin update.


### 1.2 (2017-12-02)

- Added new console command `auth:useradd`.
- Fixed plugin setup hook.
- Removed unnecessary dependency.


### 1.1 (2017-12-02)

- Added new API function: `is_signup_enabled()`.
- Part of the authentication driver moved to the `auth_ui` plugin.
- Fixed `AuthenticationError`'s constructor.
- Removed `url` and `profile_url` properties from `model.AbstractUser`.


### 1.0 (2017-11-24)

First release.
