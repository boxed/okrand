from django.apps import (
    AppConfig,
    apps,
)
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy
from iommi import MenuItem

from okrand.views import i18n


class OkrandConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'okrand'

    def ready(self):
        for model in apps.get_models():
            # if the field has explicit verbose_name
            verbose_name = model._meta.original_attrs.get('verbose_name')
            verbose_name_plural = model._meta.original_attrs.get('verbose_name_plural')

            if verbose_name is None:
                model._meta.verbose_name = gettext_lazy(model._meta.verbose_name)

            if verbose_name_plural is None:
                model._meta.verbose_name_plural = gettext_lazy(model._meta.verbose_name_plural)

            for field in model._meta._get_fields(reverse=False):
                if not isinstance(field.verbose_name, Promise):
                    field.verbose_name = gettext_lazy(field.verbose_name)
