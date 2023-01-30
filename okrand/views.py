def i18n(request):
    import sys
    from django.apps import apps
    from os.path import dirname
    import os

    def is_in_project(model):
        env_paths = {dirname(os.__file__), dirname(dirname(sys.executable))}
        for env_path in env_paths:
            if sys.modules[model.__module__].__file__.startswith(env_path):
                return False
        return True

    models = [
        model
        for app_name, models in apps.all_models.items()
        for model_name, model in models.items()
        if is_in_project(model)
    ]

    from django.utils.functional import Promise
    missing_verbose_name = [
        x
        for x in models
        if not isinstance(x._meta.verbose_name, Promise)
    ]

    missing_verbose_name_plural = [
        x
        for x in models
        if not isinstance(x._meta.verbose_name_plural, Promise)
    ]

    from django.db.models import ForeignObjectRel
    from django.db.models import AutoField
    fields_with_missing_verbose_name = [
        field
        for x in models
        for field in x._meta.get_fields()
        if (
                not isinstance(field, ForeignObjectRel) and
                not isinstance(field, AutoField) and
                not field._verbose_name  # _verbose_name is the original, while verbose_name can be auto generated
        )
    ]

    with open(Path(settings.BASE_DIR) / '.gitignore') as f:
        gitignore = [x for x in f.read().split('\n') if x]

    language = 'sv'
    js_catalog_output = (Path(__file__).parent / 'static' / f'{language}_i18n.js').relative_to(settings.BASE_DIR)
    ignore = gitignore + [
        str(js_catalog_output),
        'dryft/base/static/vue.global.js',
    ]

    potential_rename_fields = {}
    potential_rename_prefix = 'potential_rename-'
    if request.method == 'GET':
        # Otherwise we'll do this twice on POST
        update_po_result = update_po_files()

        if update_po_result.new_strings and update_po_result.newly_obsolete_strings:
            potential_rename_fields = {
                f'{potential_rename_prefix}{s}': Field.choice(
                    display_name=s,
                    required=False,
                    choices=update_po_result.newly_obsolete_strings,
                )
                for s in update_po_result.new_strings
            }

    def save_potential_renames(form, **_):
        # TODO: validate that two strings aren't set to the same target string
        old_msgid_by_new_msgid = {
            strip_prefix(k, prefix=potential_rename_prefix): v
            for k, v in form.get_request().POST.items()
            if k.startswith(potential_rename_prefix)
        }
        update_po_files(old_msgid_by_new_msgid=old_msgid_by_new_msgid)
        return redirect('.')


    potential_renames_form = Form(
        title='Handle renames',
        fields=potential_rename_fields,
        actions__submit=dict(
            display_name='Save',
            post_handler=save_potential_renames,
        ),
    )


    # noinspection PyPackageRequirements
    import polib
    path = Path(__file__).parent.parent.parent / 'locale' / language / 'LC_MESSAGES' / 'django.po'
    po = polib.pofile(str(path))

    def process(m):
        m.problems = []
        if not m.msgid or not m.msgstr:
            return

        if m.msgid[0].isupper() != m.msgstr[0].isupper() and m.msgstr[0].upper() != m.msgstr[0]:
            m.problems.append('Case differs on first character')

        if m.msgid.count('{}') != m.msgstr.count('{}'):
            m.problems.append('Different amount of {} in strings')

    items = sorted(po, key=lambda x: x.msgid.lower())
    for m in items:
        process(m)

    # Form conf from this point onwards
    def fields_from_items(items):
        return {
            x.msgid: Field(
                initial=x.msgstr,
                display_name=x.msgid,
                help_text='\n'.join(getattr(x, 'problems', [])),
            )
            for x in items
        }

    def save(form, **_):
        for field in form.fields.values():
            m = po.find(field._name)
            if m is None:
                continue
            if m.msgstr != field.value and field.value:
                m.msgstr = field.value
                # Remove fuzzy flag
                m.flags = [x for x in m.flags if x != 'fuzzy']
        po.save()

        from django.core import management
        management.call_command('compilemessages', ignore=ignore)

        with open(js_catalog_output, 'wb') as f:
            activate(language)
            f.write(JavaScriptCatalog().get(request, domain='django').content)

        return redirect('.')

    save_button = dict(actions__submit=dict(display_name='Save', post_handler=save))

    def code_url(row, **_):
        try:
            return src_debug_url_builder(sys.modules[row.__module__].__file__, inspect.findsource(row)[1] + 1)
        except (OSError, TypeError):
            return None

    class ClassSourceCodeReferenceTable(Table):
        name = Column(
            attr=None,
            cell__value=lambda row, **_: row.__name__,
            cell__url=code_url,
        )

        class Meta:
            header__template = None

    class FieldSourceCodeReferenceTable(Table):
        name = Column(
            attr=None,
            cell__value=lambda row, **_: row.name,
            cell__url=code_url,
        )

        class Meta:
            header__template = None

    return Page(
        title='Swedish',
        parts=dict(
            potential_renames=potential_renames_form,

            untranslated=Form(
                title='Untranslated',
                fields=fields_from_items(x for x in items if not x.msgstr.strip() and not x.obsolete),
                **save_button,
            ),

            problems=Form(
                title='Problems',
                fields=fields_from_items(x for x in items if x.problems and not x.obsolete),
                **save_button,
            ),

            fuzzy=Form(
                title='Fuzzy',
                fields=fields_from_items(x for x in items if x.fuzzy and not x.obsolete),
                **save_button,
            ),

            missing_verbose_name=ClassSourceCodeReferenceTable(
                title='Models with missing verbose_name',
                rows=missing_verbose_name,
            ),

            missing_verbose_name_plural=ClassSourceCodeReferenceTable(
                title='Models with missing verbose_name_plural',
                rows=missing_verbose_name_plural,
            ),

            fields_with_missing_verbose_name=FieldSourceCodeReferenceTable(
                title='Fields with missing verbose_name',
                rows=fields_with_missing_verbose_name,
            ),

            # all=Form(
            #     title='All',
            #     fields=fields_from_items(x for x in items),
            #     **save_button,
            # ),
        ),
    )