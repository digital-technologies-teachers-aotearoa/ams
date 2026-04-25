from collections import defaultdict

from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404
from django.http import HttpResponseRedirect
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


def _user_can_download(user, resource):
    if resource.visibility == Resource.Visibility.PUBLIC:
        return True
    if resource.visibility == Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED:
        return user.is_authenticated
    return user_has_active_membership(user)


_RESOURCE_LIST_PREFETCHES = ("components", "author_users", "author_entities", "tags")


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
        context["can_download"] = _user_can_download(self.request.user, self.object)
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
        if not _user_can_download(request.user, component.resource):
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
            query = SearchQuery(q, search_type="websearch")
            qs = (
                qs.filter(search_vector=query)
                .annotate(rank=SearchRank(F("search_vector"), query))
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
