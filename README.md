# PytSite Authentication and Authorization Plugin


## Changelog


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
