from pathlib import Path

import pytest
from django.apps import apps
from django.utils.functional import Promise
from django.utils.text import format_lazy
from django.utils.translation import (
    gettext,
    gettext_lazy,
    trans_real,
)
from okrand._vendored.polib import (
    POEntry,
    POFile,
)

from okrand import (
    _update_language,
    ignore_filename,
    normalize_func,
    parse_django_template,
    parse_js,
    parse_python,
    read_config,
    String,
    translations_for_all_models,
    translations_for_model,
    UnknownSortException,
    update_language,
    update_po_files,
    UpdateResult,
)
from okrand.apps import (
    upgrade_plural,
    upgrade_verbose_name,
)
from tests.models import (
    NoMetaNoExplicitVerboseName,
    UpgradedStringsName,
    WithMetaAndOnlyPluralVerboseName,
    WithMetaAndVerboseName,
)


def collect(x):
    singular = set()
    plural = set()
    for entry in x:
        singular.add(entry.msgid)
        if entry.msgid_plural:
            plural.add(entry.msgid_plural)
    return singular, plural


def test_normalize_func():
    assert normalize_func('_') == 'gettext'
    assert normalize_func('gettext_lazy') == 'gettext'


def test_django_html():
    singular, plural = collect(parse_django_template(
'''
{% load i18n %}
{% blocktranslate count counter=list|length with foo=foo bar=3 %}singular {{ x }}{% plural %}plural {{ y }}{% endblocktranslate %}
{% blocktranslate %}singular 2{% endblocktranslate %}
{% trans "foo" %}
'''))

    assert singular == {'singular %(x)s', 'foo', 'singular 2'}
    assert plural == {'plural %(y)s'}


def test_python():
    singular, plural = collect(parse_python('''
class Foo:
    def foo(self):
        something = gettext('foo') + 'asd'
        gettext_lazy("bar")
        ngettext("singular", "plural")
        pgettext("context", "baz")
        npgettext("context", "singular2", ' plural2 ')
'''))

    assert singular == {'singular', 'foo', 'bar', 'baz', 'singular2'}
    assert plural == {'plural', ' plural2 '}


def test_python_nested_class():
    singular, plural = collect(
        parse_python(
            '''
class DealStage(NamedModel):

    class Stages(TextChoices):
        initial = 'initial', gettext_lazy('initial')
        meeting_booked = 'meeting_booked', gettext_lazy('meeting booked')
        waiting_for_customer = 'waiting_for_customer', gettext_lazy('waiting for customer')
    '''
            )
        )

    assert singular == {'initial', 'meeting booked', 'waiting for customer'}
    assert plural == set()


def test_js():
    singular, plural = collect(parse_js(
        '''
        function foo() {
            something = gettext('foo') + 'asd'
            ngettext("singular", "plural")
            pgettext("context", "baz")
            npgettext ( "context"   , "singular2", ' plural2 '  )
            asd_foo("don't catch this please")
            asd_pgettext("and not", "this either")
        }
        '''))

    assert singular == {'singular', 'foo', 'baz', 'singular2'}
    assert plural == {'plural', ' plural2 '}


def test_ignore_filename():
    assert ignore_filename('foo/bar/baz.py', ignore_list=['.*foo.*'])
    assert not ignore_filename('foo/bar/baz.py', ignore_list=['.*foobar.*'])


def test__update_language():
    po_file = POFile()
    strings = [
        String(
            msgid='foo',
            translation_function='gettext',
            domain='django',
        ),
        String(
            msgid='bar',
            translation_function='gettext',
            domain='django',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult(new_strings=['foo', 'bar'])
    assert list(po_file) == [
        POEntry(
            msgid='foo',
        ),
        POEntry(
            msgid='bar',
        )
    ]

    #  updates
    strings.append(
        String(
            msgid='baz',
            translation_function='gettext',
            domain='django',
        )
    )
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult(new_strings=['baz'])
    assert list(po_file) == [
        POEntry(
            msgid='foo',
        ),
        POEntry(
            msgid='bar',
        ),
        POEntry(
            msgid='baz',
        )
    ]

    # deletion
    strings = strings[:-1]
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult(newly_obsolete_strings=['baz'])
    assert list(po_file) == [
        POEntry(
            msgid='foo',
        ),
        POEntry(
            msgid='bar',
        ),
        POEntry(
            msgid='baz',
            obsolete=True,
        )
    ]

    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult(previously_obsolete_strings=['baz'])


def test__update_language_plural_changed():
    po_file = POFile()
    strings = [
        String(
            msgid='foo',
            msgid_plural='foos',
            translation_function='gettext',
            domain='django',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult(new_strings=['foo'])
    assert list(po_file) == [
        POEntry(
            msgid='foo',
            msgid_plural='foos',
            msgstr_plural={
                0: '',
                1: '',
            }
        ),
    ]
    # update
    strings = [
        String(
            msgid='foo',
            msgid_plural='foos updated',
            translation_function='gettext',
            domain='django',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult()
    assert list(po_file) == [
        POEntry(
            msgid='foo',
            msgid_plural='foos updated',
            msgstr_plural={
                0: '',
                1: '',
            }
        ),
    ]

    assert 'fuzzy' in po_file[0].flags


def test__update_language_singular_changed():
    # setup
    po_file = POFile()
    po_file.extend([
        POEntry(msgid='old'),
        POEntry(msgid='old 2'),
    ])

    # update returns two lists
    strings = [
        String(
            msgid='new',
            translation_function='gettext',
            domain='django',
        ),
        String(
            msgid='new 2',
            translation_function='gettext',
            domain='django',
        ),
    ]
    result = _update_language(po_file=po_file, strings=strings, domain='django')
    assert len(result.newly_obsolete_strings) == 2 and len(result.new_strings) == 2

    # assert that the data is unchanged!
    assert list(po_file) == [
        POEntry(msgid='old'),
        POEntry(msgid='old 2'),
    ]

    # Now mark a couple as the same
    assert _update_language(
        po_file=po_file,
        strings=strings,
        old_msgid_by_new_msgid={
            'new': 'old',  # "new" is same as "old"
            'new 2': None,  # "new 2" is truly new, not a renamed string
        },
        domain='django',
    ) == UpdateResult(
        new_strings=['new 2'],
        previously_obsolete_strings=['old 2'],
    )
    assert list(po_file) == [
        POEntry(
            msgid='new',
        ),
        POEntry(
            msgid='old 2',
            obsolete=True,
        ),
    ]


def test__update_language_unmark_obsolete_when_found_again():
    # setup
    po_file = POFile()
    po_file.append(
        POEntry(
            msgid='foo',
            obsolete=True,
        ),
    )

    strings = [
        String(
            msgid='foo',
            translation_function='gettext',
            domain='django',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings, domain='django') == UpdateResult()
    assert list(po_file) == [
        POEntry(
            msgid='foo',
        ),
    ]


def test_normalization():
    s = String(
        msgid='foo\r\n',
        msgid_plural='bar\r\n',
        translation_function='gettext',
        domain='django',
    )
    assert s.msgid == 'foo\n'
    assert s.msgid_plural == 'bar\n'


def test_create_implicit_verbose_name_for_models():
    # all models will have all their fields as promises now
    for model in apps.get_app_config('tests').models.values():
        assert isinstance(model._meta.verbose_name, Promise)
        assert isinstance(model._meta.verbose_name_plural, Promise)
        for field in model._meta.get_fields():
            assert isinstance(field.verbose_name, Promise)


pk_string = String(
    msgid='ID',
    translation_function='gettext',
    domain='django',
)


@pytest.mark.parametrize(
    ['model', 'expected'],
    [
        (
            NoMetaNoExplicitVerboseName, [
                String(
                    msgid='no meta no explicit verbose name',
                    translation_function='gettext',
                    domain='django',
                ),
                String(
                    msgid='no meta no explicit verbose names',
                    translation_function='gettext',
                    domain='django',
                ),
                pk_string,
                String(
                    msgid='field',
                    translation_function='gettext',
                    domain='django',
                ),
            ]
        ),
        (
            WithMetaAndVerboseName, [
                String(
                    msgid='explicit',
                    translation_function='gettext',
                    domain='django',
                ),
                String(
                    msgid='explicits',
                    translation_function='gettext',
                    domain='django',
                ),
                pk_string,
                String(
                    msgid='field explicit',
                    translation_function='gettext',
                    domain='django',
                ),
            ]
        ),
        (
            WithMetaAndOnlyPluralVerboseName, [
                String(
                    msgid='with meta and only plural verbose name',
                    translation_function='gettext',
                    domain='django',
                ),
                String(
                    msgid='explicit',
                    translation_function='gettext',
                    domain='django',
                ),
                pk_string,
                String(
                    msgid='field explicit',
                    translation_function='gettext',
                    domain='django',
                ),
            ]
        ),
        (
            UpgradedStringsName, [
                String(
                    msgid='upgraded',
                    translation_function='gettext',
                    domain='django',
                ),
                String(
                    msgid='upgraded plural',
                    translation_function='gettext',
                    domain='django',
                ),
                pk_string,
                String(
                    msgid='upgraded field',
                    translation_function='gettext',
                    domain='django',
                ),
            ]
        ),
    ]
)
def test_collect_django_models(capsys, model, expected):
    actual = list(translations_for_model(model))
    assert actual == expected


class FakeTranslationCatalog:
    # noinspection PyMethodMayBeStatic
    def gettext(self, s):
        return f'<translation of {s}>'


def test_switched_language():
    assert not hasattr(trans_real._active, 'value')
    trans_real._active.value = FakeTranslationCatalog()
    try:
        assert gettext('foo') == '<translation of foo>'
        assert gettext_lazy('foo') == '<translation of foo>'

        # We should get the translated strings here
        for model in apps.get_app_config('tests').models.values():
            assert '<translation of' in str(model._meta.verbose_name)
            assert '<translation of' in str(model._meta.verbose_name_plural)
            for field in model._meta.get_fields():
                assert '<translation of' in str(field.verbose_name)

        # The collection shouldn't collect the translated strings!
        for s in translations_for_all_models():
            assert '<translation of' not in s.msgid
            assert s.msgid_plural is None or '<translation of' not in s.msgid_plural

    finally:
        del trans_real._active.value


def test_warning_non_constant_argument(capsys):
    assert list(parse_python('''
def foo(bar):
    return gettext(bar)
    ''')) == []

    captured = capsys.readouterr()
    assert captured.out == 'Warning: found non-constant first argument: bar\n'


def test_raw_string_upgrade():
    assert isinstance(UpgradedStringsName._meta.verbose_name, Promise)
    assert isinstance(UpgradedStringsName._meta.verbose_name_plural, Promise)
    assert isinstance(UpgradedStringsName._meta.get_field('field').verbose_name, Promise)


def test_upgrade_verbose_name():
    string = 'string'

    class Foo:
        def __init__(self):
            self.verbose_name = string

    f = Foo()
    upgrade_verbose_name(f)
    assert f.verbose_name == 'string'
    assert isinstance(f.verbose_name, Promise) and f.verbose_name._okrand_original_string is string


def test_upgrade_plural():
    string = 'strings'

    class Foo:
        def __init__(self):
            self.verbose_name_plural = string

    f = Foo()
    upgrade_plural(f)
    assert f.verbose_name_plural == 'strings'
    assert isinstance(f.verbose_name_plural, Promise) and f.verbose_name_plural._okrand_original_string is string


def test_upgrade_plural_2():
    string = 'string'
    generated_plural_string = format_lazy('{}s', string)

    class Foo:
        def __init__(self):
            self.verbose_name_plural = generated_plural_string

    f = Foo()
    upgrade_plural(f)
    assert f.verbose_name_plural == 'strings'
    assert isinstance(f.verbose_name_plural, Promise)
    assert f.verbose_name_plural._okrand_original_string == generated_plural_string
    assert isinstance(f.verbose_name_plural._okrand_original_string, str)


def test_upgrade_plural_3():
    string = 'string'
    generated_plural_string = format_lazy('{}s', gettext_lazy(string))

    class Foo:
        def __init__(self):
            self.verbose_name_plural = generated_plural_string

    f = Foo()
    upgrade_plural(f)
    assert f.verbose_name_plural == 'strings'
    assert isinstance(f.verbose_name_plural, Promise)
    assert f.verbose_name_plural._okrand_original_string == generated_plural_string
    assert isinstance(f.verbose_name_plural._okrand_original_string, str)


def test_read_config():
    assert read_config('definitely_does_not_exist.cfg') == {}
    assert read_config(Path('tests') / 'test_read_config_no_section.cfg') == {}


def test_update_po_files_invalid_sort():
    with pytest.raises(UnknownSortException):
        update_po_files(sort='klingon lexicographical')


def test_update_language(monkeypatch):
    for result in update_language(language_code='tlh', strings=[], sort='alphabetical'):
        if result.domain != 'django':
            continue
        assert result.new_strings == []
        assert result.new_strings == []
        assert result.previously_obsolete_strings == ['success']
