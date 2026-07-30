from collections import defaultdict
from datetime import timedelta

from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import get_language
from django.views import generic

from ams.resources.forms import ResourceSearchForm
from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag
from ams.resources.models import record_component_view
from ams.resources.models import record_resource_view
from ams.utils.mixins import RedirectToCosmeticURLMixin
from ams.utils.permissions import user_has_active_membership


def _user_can_view(user, resource):
    if resource.visibility == Resource.Visibility.MEMBERS_ONLY:
        return user_has_active_membership(user)
    return True


def _user_can_access(user, resource):
    if resource.visibility == Resource.Visibility.PUBLIC:
        return True
    if resource.visibility == Resource.Visibility.ACCESS_ACCOUNT_REQUIRED:
        return user.is_authenticated
    return user_has_active_membership(user)


_RESOURCE_LIST_PREFETCHES = (
    "components",
    "author_users",
    "author_entities",
    "tags__category__tags",
)

LATEST_LIMIT = 5
MOST_VIEWED_LIMIT = 5
MOST_VIEWED_WINDOW_DAYS = 30

# Maps the active language to its per-language search vector column and the
# Postgres text-search config used to build it. Defaults to English for any
# unrecognised or missing language.
_SEARCH_BY_LANGUAGE = {
    "en": ("search_vector_en", "english"),
    "mi": ("search_vector_mi", "simple"),
}


class ResourceHomeView(generic.TemplateView):
    template_name = "resources/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ResourceSearchForm(inline=True)
        qs = Resource.objects.filter(published=True)
        if not user_has_active_membership(self.request.user):
            qs = qs.exclude(visibility=Resource.Visibility.MEMBERS_ONLY)
        context["resources"] = qs.order_by("-datetime_added").prefetch_related(
            *_RESOURCE_LIST_PREFETCHES,
        )[:LATEST_LIMIT]
        context["resource_count"] = qs.count()
        context["component_count"] = ResourceComponent.objects.filter(
            resource__in=qs,
        ).count()

        recent_cutoff = timezone.now() - timedelta(days=MOST_VIEWED_WINDOW_DAYS)
        context["most_viewed_month"] = (
            qs.annotate(
                recent_views=Count(
                    "views",
                    filter=Q(views__datetime_viewed__gte=recent_cutoff),
                ),
            )
            .filter(recent_views__gt=0)
            .order_by("-recent_views")
            .prefetch_related(*_RESOURCE_LIST_PREFETCHES)[:MOST_VIEWED_LIMIT]
        )
        context["most_viewed_all_time"] = (
            qs.filter(view_count__gt=0)
            .order_by("-view_count")
            .prefetch_related(*_RESOURCE_LIST_PREFETCHES)[:MOST_VIEWED_LIMIT]
        )
        return context


class ResourceDetailView(RedirectToCosmeticURLMixin, generic.DetailView):
    model = Resource
    context_object_name = "resource"
    template_name = "resources/resource_detail.html"

    def get_queryset(self):
        return Resource.objects.filter(published=True).prefetch_related(
            *_RESOURCE_LIST_PREFETCHES,
            "components__component_resource",
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_view(self.request.user, obj):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components_of"] = self.object.component_of.filter(
            resource__published=True,
        ).select_related("resource")
        context["can_access"] = _user_can_access(self.request.user, self.object)
        record_resource_view(self.object)
        return context


class ResourceComponentAccessView(generic.View):
    def get(self, request, pk):
        component = (
            ResourceComponent.objects.select_related(
                "resource",
                "component_resource",
            )
            .filter(pk=pk)
            .first()
        )
        if component is None:
            raise Http404
        if not component.resource.published:
            raise Http404
        if not _user_can_access(request.user, component.resource):
            raise PermissionDenied

        if component.component_file:
            target = component.component_file.url
        elif component.component_url:
            target = component.component_url
        elif component.component_resource:
            target = component.component_resource.get_absolute_url()
        else:
            raise Http404

        record_component_view(component)
        return HttpResponseRedirect(target)


class ResourceSearchView(generic.TemplateView):
    template_name = "resources/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        tag_pks = []
        for raw_pk in self.request.GET.getlist("tag"):
            try:
                tag_pks.append(int(raw_pk))
            except ValueError:
                continue

        context["q"] = q
        context["form"] = ResourceSearchForm(initial={"q": q})
        context["selected_tag_pks"] = set(tag_pks)

        if not q and not tag_pks:
            context["results"] = Resource.objects.none()
            return context

        qs = Resource.objects.filter(published=True)
        if not user_has_active_membership(self.request.user):
            qs = qs.exclude(visibility=Resource.Visibility.MEMBERS_ONLY)

        if q:
            column, config = _SEARCH_BY_LANGUAGE.get(
                get_language(),
                _SEARCH_BY_LANGUAGE["en"],
            )
            query = SearchQuery(q, config=config, search_type="websearch")
            qs = (
                qs.filter(**{column: query})
                .annotate(rank=SearchRank(F(column), query))
                .order_by("-rank")
            )

        if tag_pks:
            selected_tags = ResourceTag.objects.filter(
                pk__in=tag_pks,
            ).select_related("category")
            if not selected_tags:
                context["results"] = Resource.objects.none()
                return context
            tags_by_category = defaultdict(list)
            for tag in selected_tags:
                tags_by_category[tag.category_id].append(tag.pk)
            # OR within a category, AND across categories
            for category_tag_pks in tags_by_category.values():
                qs = qs.filter(tags__pk__in=category_tag_pks)
            qs = qs.distinct()

        context["results"] = qs.prefetch_related(*_RESOURCE_LIST_PREFETCHES)
        return context
