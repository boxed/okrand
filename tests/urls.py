from django.urls import (
    include,
    path,
)
from iommi.admin import Admin

from okrand.views import i18n


urlpatterns = [
    path('admin/', include(Admin().urls())),
    path('i18n/', i18n),
]
