import pytest
from django.http import Http404
from iommi import render_if_needed
from iommi.admin import Admin

from tests.helpers import (
    req,
    staff_req,
)
from okrand.views import (
    i18n,
    strip_prefix,
)


def test_i18n_view(settings):
    with pytest.raises(Http404):
        render_if_needed(request=req('get'), response=i18n(request=req('get'))).content.decode()

    with pytest.raises(Http404):
        render_if_needed(request=staff_req('get'), response=i18n(request=staff_req('get'))).content.decode()

    settings.DEBUG = True
    request = staff_req('post', **{'-submit': ''})
    render_if_needed(request=request, response=i18n(request=request))


def test_admin(settings):
    settings.DEBUG = True
    all_models = Admin().all_models().as_view()
    content = all_models(staff_req('get')).content.decode()
    assert '>i18n</a>' in content


def test_strip_prefix():
    assert strip_prefix('foobar', prefix='foo') == 'bar'
    assert strip_prefix('foobar', prefix='baz') == 'foobar'
    with pytest.raises(AssertionError):
        assert strip_prefix('foobar', prefix='baz', strict=True) == 'foobar'
