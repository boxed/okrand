from django.db.models import (
    Field,
    Model,
)
from django.utils.translation import gettext_lazy


class NoMetaNoExplicitVerboseName(Model):
    field = Field()


class WithMetaAndVerboseName(Model):
    field = Field(verbose_name=gettext_lazy('field explicit'))

    class Meta:
        verbose_name = gettext_lazy('explicit')


class WithMetaAndOnlyPluralVerboseName(Model):
    field = Field(verbose_name=gettext_lazy('field explicit'))

    class Meta:
        verbose_name_plural = gettext_lazy('explicit')


class UpgradedStringsName(Model):
    field = Field(verbose_name='upgraded field')

    class Meta:
        verbose_name = 'upgraded'
        verbose_name_plural = 'upgraded plural'
