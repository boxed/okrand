from django.apps import apps
from django.utils.functional import Promise
from django.utils.translation import (
    activate,
    gettext,
    trans_real,
)
from polib import (
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
    String,
    translations_for_all_models,
    UpdateResult,
)
from tests.models import BadVerboseNamesName


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
        ),
        String(
            msgid='bar',
            translation_function='gettext',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult(new_strings=['foo', 'bar'])
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
            translation_function='gettext'
        )
    )
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult(new_strings=['baz'])
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
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult(newly_obsolete_strings=['baz'])
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

    assert _update_language(po_file=po_file, strings=strings) == UpdateResult(previously_obsolete_strings=['baz'])


def test__update_language_plural_changed():
    po_file = POFile()
    strings = [
        String(
            msgid='foo',
            msgid_plural='foos',
            translation_function='gettext',
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult(new_strings=['foo'])
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
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult()
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
    po_file.append(
        POEntry(
            msgid='old',
        ),
    )

    # update returns two lists
    strings = [
        String(
            msgid='new',
            translation_function='gettext',
        ),
    ]
    result = _update_language(po_file=po_file, strings=strings)
    assert len(result.newly_obsolete_strings) == 1 and len(result.new_strings) == 1

    # assert that the data is unchanged!
    assert list(po_file) == [
        POEntry(
            msgid='old',
        ),
    ]

    # Now mark a couple as the same
    assert _update_language(po_file=po_file, strings=strings, old_msgid_by_new_msgid={
        result.new_strings[0]: result.newly_obsolete_strings[0],
    }) == UpdateResult()
    assert list(po_file) == [
        POEntry(
            msgid='new',
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
        ),
    ]
    assert _update_language(po_file=po_file, strings=strings) == UpdateResult()
    assert list(po_file) == [
        POEntry(
            msgid='foo',
        ),
    ]


def test_normalization():
    s = String(msgid='foo\r\n', msgid_plural='bar\r\n', translation_function='gettext')
    assert s.msgid == 'foo\n'
    assert s.msgid_plural == 'bar\n'


def test_create_implicit_verbose_name_for_models():
    for model in apps.get_app_config('tests').models.values():
        if model is BadVerboseNamesName:
            continue
        assert isinstance(model._meta.verbose_name, Promise)
        assert isinstance(model._meta.verbose_name_plural, Promise)
        for field in model._meta.get_fields():
            assert isinstance(field.verbose_name, Promise)


def test_collect_django_models(capsys):
    result = list(translations_for_all_models())

    # TODO: something more reasonable here!
    assert len(result) == 14

    captured = capsys.readouterr()
    assert captured.out.split('\n') == [
        "Warning: verbose_name on <class 'tests.models.BadVerboseNamesName'> is a string, not set to a gettext_lazy object",
        "Warning: verbose_name_plural on <class 'tests.models.BadVerboseNamesName'> is a string, not set to a gettext_lazy object",
        '',
    ]


class FakeTranslationCatalog:
    def gettext(self, s):
        return f'<translation of {s}>'


def test_switched_language():
    trans_real._active.value = FakeTranslationCatalog()
    assert gettext('foo') == '<translation of foo>'

    for model in apps.get_app_config('tests').models.values():
        if model == BadVerboseNamesName:
            continue
        assert '<translation of' in str(model._meta.verbose_name)
        assert '<translation of' in str(model._meta.verbose_name_plural)
        for field in model._meta.get_fields():
            assert '<translation of' in str(field.verbose_name)


def test_warning_non_constant_argument(capsys):
    assert list(parse_python('''
def foo(bar):
    return gettext(bar)
    ''')) == []

    captured = capsys.readouterr()
    assert captured.out == 'Warning: found non-constant first argument: bar\n'
