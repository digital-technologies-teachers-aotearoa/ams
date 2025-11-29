from django.views.generic import TemplateView


class PageNotFoundView(TemplateView):
    template_name = "404.html"
