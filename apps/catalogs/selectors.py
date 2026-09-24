from django.db.models import Q, QuerySet

from apps.catalogs.utils import normalize_whitespace


def catalog_list_qs(
    model,
    *,
    search: str = "",
    status: str = "",
    search_fields: tuple[str, ...],
    extra_filter=None,
) -> QuerySet:
    qs = model.objects.select_related("created_by", "updated_by").all()
    if search:
        term = normalize_whitespace(search)
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": term})
        qs = qs.filter(query)
    if status == "activo":
        qs = qs.filter(is_active=True)
    elif status == "inactivo":
        qs = qs.filter(is_active=False)
    if extra_filter:
        qs = extra_filter(qs)
    return qs.order_by("code")
