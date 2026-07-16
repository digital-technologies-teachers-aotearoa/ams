from collections import defaultdict

from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils.translation import get_language
from django.views import generic

from ams.resources.forms import ResourceSearchForm
from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag
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


_RESOURCE_LIST_PREFETCHES = ("components", "author_users", "author_entities", "tags")

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
        context["resources"] = qs.prefetch_related(*_RESOURCE_LIST_PREFETCHES)[:10]
        context["resource_count"] = qs.count()
        context["component_count"] = ResourceComponent.objects.filter(
            resource__in=qs,
        ).count()
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
        return context


class ResourceComponentDownloadView(generic.View):
    def get(self, request, pk):
        # Validates component exists, belongs to a published resource, and has a file.
        component = (
            ResourceComponent.objects.select_related("resource").filter(pk=pk).first()
        )
        if component is None:
            raise Http404
        if not component.resource.published:
            raise Http404
        if not component.component_file:
            raise Http404
        if not _user_can_access(request.user, component.resource):
            raise PermissionDenied
        return HttpResponseRedirect(component.component_file.url)


class ResourceSearchView(generic.TemplateView):
    template_name = "resources/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        tag_slugs = self.request.GET.getlist("tag")

        context["q"] = q
        context["form"] = ResourceSearchForm(initial={"q": q})
        context["selected_tag_slugs"] = set(tag_slugs)

        if not q and not tag_slugs:
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

        if tag_slugs:
            selected_tags = ResourceTag.objects.filter(
                slug__in=tag_slugs,
            ).select_related("category")
            if not selected_tags:
                context["results"] = Resource.objects.none()
                return context
            tags_by_category = defaultdict(list)
            for tag in selected_tags:
                tags_by_category[tag.category_id].append(tag.slug)
            # OR within a category, AND across categories
            for category_tag_slugs in tags_by_category.values():
                qs = qs.filter(tags__slug__in=category_tag_slugs)
            qs = qs.distinct()

        context["results"] = qs.prefetch_related(
            *_RESOURCE_LIST_PREFETCHES,
            "tags__category",
        )
        return context
