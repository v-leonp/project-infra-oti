from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def catalog_url(stem, action, pk=None):
    name = f"catalogs:{stem}_{action}"
    try:
        if pk is not None:
            return reverse(name, kwargs={"pk": pk})
        return reverse(name)
    except NoReverseMatch:
        return "#"
