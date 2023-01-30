__version__ = '1.0.0'

import argparse
import ast
import os
import re
from configparser import (
    ConfigParser,
    NoSectionError,
)
from dataclasses import (
    dataclass,
    field,
    fields,
)
from pathlib import Path
from typing import List

from django.template import Template
from django.template.base import TokenType
from django.template.loader_tags import IncludeNode
from django.templatetags.i18n import (
    BlockTranslateNode,
    TranslateNode,
)

from django.apps.registry import apps
from django.utils.functional import Promise
from gitignorefile import Cache
from polib import (
    pofile,
    POEntry,
)


def translations_for_all_models():
    for model in apps.get_models():
        # if the field has explicit verbose_name
        verbose_name = model._meta.original_attrs.get('verbose_name')
        verbose_name_plural = model._meta.original_attrs.get('verbose_name_plural')

        if isinstance(verbose_name, Promise):
            continue

        if isinstance(verbose_name_plural, Promise):
            continue

        yield String(
            msgid=verbose_name,
            msgid_plural=verbose_name_plural,
            translation_function='gettext',
            context='auto django model',
        )
        yield from _translations_for_model(model)


def _translations_for_model(model):
    for field in model._meta.get_fields():
        try:
            # if the field has explicit verbose_name
            if isinstance(field.verbose_name, Promise):
                continue

            yield String(
                msgid=field.verbose_name,
                translation_function='gettext',
                context='auto django field',
            )
        except AttributeError:
            pass


def walk_respecting_gitignore(path):
    ignored = Cache()
    for root, dirs, files in os.walk(path):
        dirs[:] = [x for x in dirs if not ignored(x) and not x == '.git']
        files[:] = [x for x in files if not ignored(x)]
        yield root, dirs, files


gettext_synonyms = {
    '_',
    'gettext',
    'gettext_lazy',
    'ngettext',
    'ngettext_lazy',
    'pgettext',
    'pgettext_lazy',
    'npgettext',
    'npgettext_lazy',
}


@dataclass(kw_only=True, frozen=True)
class _String:
    msgid: str
    translation_function: str
    msgid_plural: str = None
    context: str = ''


def String(*, msgid, translation_function, msgid_plural=None, context=''):
    return _String(
        msgid=normalize(msgid),
        translation_function=translation_function,
        msgid_plural=normalize(msgid_plural),
        context=context,
    )


def strip_suffix(s, *, suffix):
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def normalize_func(func):
    func = strip_suffix(func, suffix='_lazy')
    if func == '_':
        func = 'gettext'
    return func


def parse_python(content):
    t = ast.parse(content)

    def w(node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in gettext_synonyms:
            func = normalize_func(node.func.id)

            if not isinstance(node.args[0], ast.Constant):
                print('Warning: found non-constant first argument')
                return

            if func == 'gettext':
                yield String(
                    msgid=node.args[0].value,
                    translation_function=func,
                )
            elif func == 'pgettext':
                yield String(
                    msgid=node.args[1].value,
                    translation_function=func,
                    context=node.args[0].value,
                )
            elif func == 'ngettext':
                yield String(
                    msgid=node.args[0].value,
                    translation_function=func,
                    msgid_plural=node.args[1].value,
                )
            elif func == 'npgettext':
                context = node.args[0].value
                yield String(
                    msgid=node.args[1].value,
                    translation_function=func,
                    context=context,
                    msgid_plural=node.args[2].value,
                )
            else:  # pragma: no cover
                assert False, f'unknown gettext flavor {func}'

        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for x in value:
                    if isinstance(x, ast.AST):
                        # noinspection PyTypeChecker
                        yield from w(x)
                    else:
                        pass
            elif isinstance(value, ast.AST):
                # noinspection PyTypeChecker
                yield from w(value)
            else:
                pass

    # noinspection PyTypeChecker
    yield from w(t)


# language=pythonregexp
find_string_regex = r'''(?x) 
    \b     # word boundary
    (?P<func>
        gettext |
        ngettext |
        pgettext |
        npgettext |
        _ 
    )
    \s*
    \(
        \s*
        (?<!\\)
        (?P<quote>["'])  
        (?P<string>.*?)
        (?<!\\)      # not the escaped quote
        (?P=quote)   # same quote as we started with

        # these two arguments are the same regex as above, plus the handling of comma
        (?P<second_argument>
            \s*,\s*
            (?<!\\)
            (?P<quote2>["'])
            (?P<string2>.*?)
            (?<!\\)
            (?P=quote2)
        )?

        (?P<third_argument>
            \s*,\s*
            (?<!\\)
            (?P<quote3>["'])
            (?P<string3>.*?)
            (?<!\\)
            (?P=quote3)
        )?
        \s*
    \)
    '''


def parse_js(content):
    # I would like to have a proper JS parser here instead of a regex, but I couldn't find one that I could use in a reasonable way
    # An idea is to use @babel/parse to parse the file and dump the strings. But this would make node and babel a dependency. This is how far I got before I decided to stop:
    # const fs = require('fs');
    # const data = fs.readFileSync('some_js.js', 'utf8');
    # parse = require('@babel/parser').parse
    # ast = parse(data)
    for m in re.finditer(find_string_regex, content):
        s = m.groupdict()['string']
        func = normalize_func(m.groupdict()['func'])

        if func == 'gettext':
            yield String(
                msgid=s,
                translation_function=func,
            )
        elif func == 'pgettext':
            yield String(
                msgid=m.groupdict()['string2'],
                translation_function=func,
                context=m.groupdict()['string'],
            )
        elif func == 'ngettext':
            yield String(
                msgid=m.groupdict()['string'],
                translation_function=func,
                msgid_plural=m.groupdict()['string2'],
            )
        elif func == 'npgettext':
            yield String(
                msgid=m.groupdict()['string2'],
                translation_function=func,
                context=s,
                msgid_plural=m.groupdict()['string3'],
            )
        else:  # pragma: no cover
            assert False, f'unknown gettext flavor {func}'


def parse_vue(content):
    yield from parse_js(content)


# monkeypatch fixes to Django classes
IncludeNode.child_nodelists = ()
BlockTranslateNode.child_nodelists = ()


def extract_string_from_blocktrans_tokens(tokens):
    result = []
    for token in tokens:
        if token.token_type == TokenType.TEXT:
            result.append(token.contents)
        elif token.token_type == TokenType.VAR:
            result.append(f'%({token.contents})s')
        else:  # pragma: no cover
            assert False
    return ''.join(result)


def parse_django_template(content):
    t = Template(content)
    t.child_nodelists = ("nodelist",)

    def w(node):
        if isinstance(node, TranslateNode):
            yield String(
                msgid=node.filter_expression.var.literal,
                translation_function='{% trans %}',
            )
        elif isinstance(node, BlockTranslateNode):
            if node.plural:
                msgid_plural = extract_string_from_blocktrans_tokens(node.plural)
            else:
                msgid_plural = None
            yield String(
                msgid=extract_string_from_blocktrans_tokens(node.singular),
                msgid_plural=msgid_plural,
                translation_function='{% blocktrans %}',
            )

        for child_nodelist in node.child_nodelists:
            nodelist = getattr(node, child_nodelist)
            for n in nodelist:
                yield from w(n)

    # noinspection PyTypeChecker
    yield from w(t)


def ignore_filename(full_path, *, ignore_list):
    for ignore_rule in ignore_list:
        if re.fullmatch(ignore_rule, str(full_path)):
            return True
    return False


def find_source_strings(ignore_list):
    # TODO:
    # yield from translations_for_all_models()

    # TODO: Path(__file__).parent should be something more general. Try to find .git/setup.cfg/pyproject.toml/poetry.toml
    for root, dirs, files in walk_respecting_gitignore(Path(__file__).parent):
        for f in files:
            extension = Path(f).suffix
            if extension not in ['.py', '.vue', '.js', '.html']:
                continue

            full_path = Path(root) / f

            if ignore_filename(full_path, ignore_list=ignore_list):
                continue

            with open(full_path) as file:
                content = file.read()

            if extension == '.py':
                yield from parse_python(content)
            elif extension == '.js':
                yield from parse_js(content)
            elif extension == '.vue':
                yield from parse_vue(content)
            elif extension == '.html':
                assert 'templates' in full_path.parts, f'Only support parsing django templates as html for now ({root} {f})'
                yield from parse_django_template(content)
            else:
                assert False, f'unknown extension {extension}'


domain = 'django'

POEntry.__repr__ = lambda self: f'<POEntry: {self.msgid}>'


@dataclass(frozen=True, kw_only=True)
class UpdateResult:
    new_strings: List[str] = field(default_factory=list)
    newly_obsolete_strings: List[str] = field(default_factory=list)
    previously_obsolete_strings: List[str] = field(default_factory=list)


def update_po_files(*, old_msgid_by_new_msgid=None) -> UpdateResult:
    config_parser = ConfigParser()
    config_parser.read('setup.cfg')
    try:
        config = dict(config_parser.items('tool:okrand'))
    except NoSectionError:
        config = {}

    def get_conf_list(name):
        return [x for x in config.get(name, []).split('\n') if x]

    ignore_list = get_conf_list('ignore')
    ignore_list += [
        __file__,
        __file__.replace('.py', '__tests.py')
    ]
    languages = get_conf_list('languages')
    sort = config.get('sort', 'none').strip()

    if sort not in ('none', 'alphabetical'):
        print(f'Unknown sort configuration "{sort}"')
        exit(1)

    strings = list(find_source_strings(ignore_list=ignore_list))

    result_fields = fields(UpdateResult)

    # dicts as a poor man's ordered set
    result_totals = {
        f.name: {}
        for f in result_fields
    }

    for language_code in languages:
        r = update_language(language_code=language_code, strings=strings, sort=sort, old_msgid_by_new_msgid=old_msgid_by_new_msgid)
        for f in result_fields:
            result_totals[f.name].update({x: None for x in getattr(r, f.name)})

    return UpdateResult(
        **{
            k: list(v)
            for k, v in result_totals.items()
        }
    )


def update_language(*, language_code, strings, sort='none', old_msgid_by_new_msgid=None) -> UpdateResult:
    # TODO: settings.BASE_DIR?
    po_file = pofile(Path('locale') / language_code / 'LC_MESSAGES' / f'{domain}.po')

    result = _update_language(po_file=po_file, strings=strings, old_msgid_by_new_msgid=old_msgid_by_new_msgid)

    if sort == 'alphabetical':
        po_file.sort(key=lambda x: x.msgid)

    po_file.save()

    return result


def normalize(msgid):
    if msgid:
        return msgid.replace('\r\n', '\n')
    else:
        return msgid


def _update_language(*, po_file, strings, old_msgid_by_new_msgid=None) -> UpdateResult:
    old_msgid_by_new_msgid = {
        normalize(k): normalize(v)
        for k, v in (old_msgid_by_new_msgid or {}).items()
    }

    for po_entry in po_file:
        if po_entry.msgid:
            po_entry.msgid = normalize(po_entry.msgid)
        if po_entry.msgid_plural:
            po_entry.msgid_plural = normalize(po_entry.msgid_plural)

    # Singular
    string_by_msgid = {
        s.msgid: s
        for s in strings
    }

    po_entry_by_msgid = {
        x.msgid: x
        for x in po_file
    }

    for new_msgid, old_msgid in old_msgid_by_new_msgid.items():
        assert new_msgid in string_by_msgid
        if not old_msgid:
            po_entry_by_msgid[new_msgid] = POEntry(
                msgid=new_msgid,
                comment=string_by_msgid[new_msgid].context,
            )
        else:
            assert old_msgid in po_entry_by_msgid
            po_entry = po_entry_by_msgid.pop(old_msgid)
            po_entry.flags.append('fuzzy')
            po_entry.msgid = new_msgid
            po_entry_by_msgid[new_msgid] = po_entry

    new_strings = [
        s
        for msgid, s in string_by_msgid.items()
        if msgid not in po_entry_by_msgid
    ]

    obsolete_po_entries = [
        po_entry
        for msgid, po_entry in po_entry_by_msgid.items()
        if msgid not in string_by_msgid
    ]

    for msgid, po_entry in po_entry_by_msgid.items():
        if po_entry.obsolete and msgid in string_by_msgid:
            # Marked as obsolete, but we found it now
            po_entry.obsolete = False

    newly_obsolete_po_entries = [
        po_entry
        for po_entry in obsolete_po_entries
        if not po_entry.obsolete
    ]

    unchanged_po_entries = [
        po_entry
        for msgid, po_entry in po_entry_by_msgid.items()
        if msgid in string_by_msgid
    ]

    if not new_strings:
        for po_entry in newly_obsolete_po_entries:
            po_entry.obsolete = True

    if not newly_obsolete_po_entries:
        for s in new_strings:
            data = dict(
                msgid=s.msgid,
                comment=s.context,
            )
            if s.msgid_plural is None:
                data.update(dict(msgstr=''))
            else:
                data.update(
                    dict(
                        msgid_plural=s.msgid_plural,
                        msgstr_plural={
                            0: '',
                            1: '',
                        },
                    )
                )

            po_file.append(
                POEntry(
                    **data
                )
            )

    # Plural: write changed plural, and mark as fuzzy
    for po_entry in unchanged_po_entries:
        s = string_by_msgid[po_entry.msgid]
        if s.msgid_plural != (po_entry.msgid_plural or None):  # the "or None" is because polib stores empty string when no plural exists
            po_entry.msgid_plural = s.msgid_plural
            if 'fuzzy' not in po_entry.flags:
                po_entry.flags.append('fuzzy')

    # TODO: update the i18n view to handle plural
    newly_obsolete_strings = [x.msgid for x in newly_obsolete_po_entries]
    newly_obsolete_strings_set = set(newly_obsolete_strings)
    return UpdateResult(
        new_strings=[x.msgid for x in new_strings],
        newly_obsolete_strings=newly_obsolete_strings,
        previously_obsolete_strings=[x.msgid for x in obsolete_po_entries if x.msgid not in newly_obsolete_strings_set],
    )


def monkey_patch_django():
    from django.db.models import Field
    from django.utils.translation import gettext_lazy
    from django.db.models.options import Options
    from django.utils.text import camel_case_to_spaces

    def okrand_set_attributes_from_name(self, name):
        self.name = self.name or name
        self.attname, self.column = self.get_attname_column()
        self.concrete = self.column is not None
        if self.verbose_name is None and self.name:
            self.verbose_name = gettext_lazy(self.name.replace("_", " "))

    Field.set_attributes_from_name = okrand_set_attributes_from_name

    orig_contribute_to_class = Options.contribute_to_class

    def okrand_contribute_to_class(self, cls, name):
        if not cls.__module__.startswith('django.'):
            print(self)
            if not self.meta or 'verbose_name' not in self.meta.__dict__:
                class OkrandMeta(self.meta):
                    verbose_name = gettext_lazy(camel_case_to_spaces(cls.__name__))

                self.meta = OkrandMeta

        orig_contribute_to_class(self, cls, name)

    Options.contribute_to_class = okrand_contribute_to_class
