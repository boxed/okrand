from django.apps import AppConfig
from django.urls import reverse
from iommi import MenuItem

from okrand.views import i18n


class OkrandConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'okrand'

    parts__menu__sub_menu__i18n = MenuItem(
        after=1,
        display_name='i18n',
        url=lambda **_: reverse(i18n),
        include=lambda request, **_: request.user.is_superuser,
    )
