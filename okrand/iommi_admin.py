from django.conf import settings
from django.urls import (
    NoReverseMatch,
    reverse,
)
from iommi import MenuItem

from okrand.views import i18n


def include_i81n_menu(request, **_):
    include = request.user.is_superuser and settings.DEBUG
    if include:
        try:
            reverse(i18n)
        except NoReverseMatch:
            print('Please add the i18n view to your url patterns to enable the link in the admin')
            return False
    return include


class Meta:
    parts__menu__sub_menu__i18n = MenuItem(
        after=1,
        display_name='i18n',
        url=lambda **_: reverse(i18n),
        include=include_i81n_menu,
    )
