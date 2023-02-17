Okrand
------

Okrand is an internationalization/translation tool for Django.

It is a pure Python program so doesn't rely on ``gettext``.

Okrand will respect your ``.gitignore``.


Django models
=============

Okrand can upgrade Django models so translation is much easier. You don't need to write ``verbose_name`` anymore! And if you do write them Okrand will upgrade raw strings to `gettext_lazy`.

Turn this feature on in your ``setup.cfg``:

.. code-block::

    [tool:okrand]
    django_model_upgrade=1

So concretely this model:

.. code-block:: python

    from django.utils.translation import gettext_lazy as _


    class Book(Model):
        name = CharField(verbose_name=_('name'))
        isbn = CharField(verbose_name=_('ISBN'))

        class Meta:
            verbose_name = _('author')
            verbose_name = _('authors')

Can now be changed to the more natural:

.. code-block:: python

    class Book(Model):
        name = CharField()
        isbn = CharField(verbose_name='ISBN')

Note that I don't need to wrap the ``verbose_name`` in a `gettext_lazy` call anymore.


Installation
============

Add `okrand` to `INSTALLED_APP`.

Add `OKRAND_STATIC_PATH` to settings, pointing to where Okrand should write the JavaScript catalog files. Typically something like:

.. code-block:: python

    OKRAND_STATIC_PATH = Path(BASE_DIR) / 'yourproject' / 'base' / 'static'

If you have a ``base`` app to put common stuff.


Configuration
=============

In ``setup.cfg`` you set:

 - additional ignore rules beyond ``.gitignore``. These are regexes for the full path.
 - sorting: none (default), alphabetical
 - if the django model upgrade is enabled


.. code-block::

    [tool:okrand]
    ignore=
        .*some_annoying_path.*
    sort=alphabetical
    django_model_upgrade=1


What does "Okrand" mean?
~~~~~~~~~~~~~~~~~~~~~~~~

`Marc Okrand <https://en.wikipedia.org/wiki/Marc_Okrand>`_ is a linguist who is best known for his work on Star Trek where he created the Klingon language.
