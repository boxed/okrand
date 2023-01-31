import pytest
from django.http import Http404
from iommi import render_if_needed

from tests.helpers import (
    req,
    staff_req,
)
from okrand.views import i18n


def test_i18n_view(settings):
    with pytest.raises(Http404):
        render_if_needed(request=req('get'), response=i18n(request=req('get'))).content.decode()

    with pytest.raises(Http404):
        render_if_needed(request=staff_req('get'), response=i18n(request=staff_req('get'))).content.decode()

    settings.DEBUG = True
    request = staff_req('post', **{'-submit': ''})
    response = render_if_needed(request=request, response=i18n(request=request))
