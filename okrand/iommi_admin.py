from django.conf import settings
from django.urls import reverse
from iommi import MenuItem

from okrand.views import i18n


class Meta:
    parts__menu__sub_menu__i18n = MenuItem(
        after=1,
        display_name='i18n',
        url=lambda **_: reverse(i18n),
        include=lambda request, **_: request.user.is_superuser and settings.DEBUG,
    )
