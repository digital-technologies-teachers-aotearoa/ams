# Forum

Discourse is used as the forum platform, due to it's mature ecosystem, flexible features, and that it's open source.
The Discourse forum can either be self or cloud hosted.

The following documentation will set up the AMS service as the authentication provider for Discourse.
This allows access to the forum to require an active membership.

## Deployment

If you plan to self host Discourse, please read the [documentation on GitHub](https://github.com/discourse/discourse/blob/main/docs/INSTALL-cloud.md).

## Forum setup

There are several key settings that need to be set to ensure the forum works as expected with the AMS system.
These need to be set by the administrator account for Discourse, and can be set on the site settings page.

```yaml
# The following settings set up single sign on
enable_discourse_connect: 'true'
discourse_connect_url: <website domain>/forum/sso
discourse_connect_secret: changeme
logout_redirect: <website domain>

# The following settings complement using single sign on
invite_only: 'false'
login_required: 'true'
allow_new_registrations: 'false'
enable_signup_cta: 'false'
auth_skip_create_confirm: 'true'
auth_overrides_email: 'true'
auth_overrides_username: 'true'
auth_overrides_name: 'true'
auth_overrides_avatar: 'true'
email_editable: 'false'
discourse_connect_overrides_bio: 'true'
discourse_connect_overrides_avatar: 'true'
discourse_connect_overrides_profile_background: 'true'
discourse_connect_overrides_location: 'true'
discourse_connect_overrides_website: 'true'
discourse_connect_overrides_card_background: 'true'
gravatar_enabled: 'false',
automatically_download_gravatars: 'false',

# Prevent bootstrap mode
# See: https://meta.discourse.org/t/-/322876
bootstrap_mode_min_users: '0'
```
