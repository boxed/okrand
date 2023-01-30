from django.db.models import (
    Field,
    Model,
)
from django.utils.translation import gettext_lazy

from okrand import monkey_patch_django


class Before(Model):
    field = Field()


class BeforeWithMeta(Model):
    field = Field()

    class Meta:
        pass


monkey_patch_django()


class After(Model):
    field = Field()


class After2(Model):
    field = Field(verbose_name=gettext_lazy('field manual'))

    class Meta:
        verbose_name = gettext_lazy('manual')


class After3(Model):
    field = Field()

    # No class Meta!
