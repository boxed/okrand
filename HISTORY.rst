Changelog
=========

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
