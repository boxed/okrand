Okrand
-----

Okrand is an internationalization/translation tool for Django.

It is a pure Python program so doesn't rely on ``gettext``.

Okrand will respect your ``.gitignore``.

Installation
============

Add `okrand` to `INSTALLED_APP`.


Configuration
=============

In ``setup.cfg`` you set:

 - languages used
 - additional ignore rules beyond ``.gitignore``. These are regexes for the full path.
 - sorting: none (default), alphabetical

.. code-block::

    [tool:okrand]
    languages=
        sv
        fr
        de
    ignore=
        .*some_annoying_path.*
    sort=alphabetical


What does "Okrand" mean?
~~~~~~~~~~~~~~~~~~~~~~~~

`Marc Okrand <https://en.wikipedia.org/wiki/Marc_Okrand>`_ is a linguist who is best known for his work on Star Trek where he created the Klingon language.
