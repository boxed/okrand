Changelog
=========

1.7.1 (2026-03-04)
~~~~~~~~~~~~~~~~~~

* JS and ML-language family parsers now respect the `gettext_synonyms` config variable. The ML-languages parser also allows `foo.gettext` patterns.


1.7.0 (2026-01-14)
~~~~~~~~~~~~~~~~~~

* The `manage.py i18n` command now writes compiled `.mo` files, making it a usable replacement for `manage.py compilemessages`


1.6.1 (2026-01-13)
~~~~~~~~~~~~~~~~~~

* Removed dependency on msgpack


1.6.1 (2025-12-17)
~~~~~~~~~~~~~~~~~~

* Fixed i18n iommi page to not crash when using gettext synonyms :)

* New config options `pgettext_synonyms`, `ngettext_synonyms`, `npgettext_synonyms` to mirror `gettext_synonyms`.


1.6.0 (2025-12-17)
~~~~~~~~~~~~~~~~~~

* New config option `gettext_synonyms`.


1.5.1 (2025-10-14)
~~~~~~~~~~~~~~~~~~

* Avoid infinite reloads when using django-browser-reload

* Option to turn off rename support, as this can often be more in the way than help. Set `renames=0` in the conf.


1.5.0 (2025-03-25)
~~~~~~~~~~~~~~~~~~

* Support for ignoring strings for translation


1.4.0 (2025-03-19)
~~~~~~~~~~~~~~~~~~

* Support `_('foo')` syntax inside Django templates


1.3.0 (2024-11-06)
~~~~~~~~~~~~~~~~~~

* Plugin system for adding your own custom string collectors


1.2.0 (2024-11-05)
~~~~~~~~~~~~~~~~~~

* Fixed issue with handling of plural names for Django models

* Added new config option `django_model_prefixes` to filter which models you want to translate


1.1.2 (2024-09-11)
~~~~~~~~~~~~~~~~~~

* Fixed another compatibility issue with Django 5


1.1.1 (2024-09-10)
~~~~~~~~~~~~~~~~~~

* Fixed compatibility with Django 5

1.1.0 (2023-04-04)
~~~~~~~~~~~~~~~~~~

* Split JS files into separate domain (like django does by default)

* Support elm files. Should enable easy support of any ML-style language.


1.0.0 (2023-02-17)
~~~~~~~~~~~~~~~~~~

- Initial release
