from django.http import Http404
from django.http import HttpResponseRedirect
from django.views import generic

from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.utils.mixins import RedirectToCosmeticURLMixin


class ResourceHomeView(generic.TemplateView):
    template_name = "resources/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resources"] = Resource.objects.filter(published=True).prefetch_related(
            "components",
            "author_users",
            "author_entities",
        )[:10]
        context["resource_count"] = Resource.objects.filter(published=True).count()
        context["component_count"] = ResourceComponent.objects.filter(
            resource__published=True,
        ).count()
        return context


class ResourceDetailView(RedirectToCosmeticURLMixin, generic.DetailView):
    model = Resource
    context_object_name = "resource"
    template_name = "resources/resource_detail.html"

    def get_queryset(self):
        return Resource.objects.filter(published=True).prefetch_related(
            "components",
            "components__component_resource",
            "author_users",
            "author_entities",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components_of"] = self.object.component_of.filter(
            resource__published=True,
        ).select_related("resource")
        return context


class ResourceComponentDownloadView(generic.View):
    def get(self, request, pk):
        component = (
            ResourceComponent.objects.select_related("resource").filter(pk=pk).first()
        )
        if component is None:
            raise Http404
        if not component.resource.published:
            raise Http404
        if not component.component_file:
            raise Http404
        return HttpResponseRedirect(component.component_file.url)
