from http import HTTPStatus
from unittest.mock import patch

import pytest

from ams.entities.tests.factories import EntityFactory
from ams.resources.models import Resource
from ams.resources.tests.factories import ResourceCategoryFactory
from ams.resources.tests.factories import ResourceComponentFactory
from ams.resources.tests.factories import ResourceFactory
from ams.resources.tests.factories import ResourceTagFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestResourceHomeView:
    def test_get(self, client):
        response = client.get("/en/resources/")
        assert response.status_code == HTTPStatus.OK

    def test_shows_only_published(self, client):
        published = ResourceFactory(published=True)
        unpublished = ResourceFactory(published=False)
        response = client.get("/en/resources/")
        resources = list(response.context["resources"])
        assert published in resources
        assert unpublished not in resources

    def test_resource_count_in_context(self, client):
        ResourceFactory.create_batch(3, published=True)
        ResourceFactory(published=False)
        response = client.get("/en/resources/")
        expected_component_count = 3
        assert response.context["resource_count"] == expected_component_count

    def test_component_count_in_context(self, client):
        resource = ResourceFactory(published=True)
        ResourceComponentFactory(
            resource=resource,
            component_url="https://a.example.com/",
        )
        ResourceComponentFactory(
            resource=resource,
            component_url="https://b.example.com/",
        )
        # Component on unpublished resource should not be counted
        unpublished = ResourceFactory(published=False)
        ResourceComponentFactory(
            resource=unpublished,
            component_url="https://c.example.com/",
        )
        response = client.get("/en/resources/")
        expected_component_count = 2
        assert response.context["component_count"] == expected_component_count

    def test_caps_at_10_resources(self, client):
        ResourceFactory.create_batch(15, published=True)
        response = client.get("/en/resources/")
        expected_component_count = 10
        assert len(response.context["resources"]) == expected_component_count


class TestResourceDetailView:
    def test_get_with_slug(self, client):
        resource = ResourceFactory(published=True)
        response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_redirect_without_slug(self, client):
        resource = ResourceFactory(published=True)
        response = client.get(f"/en/resources/resource/{resource.pk}/")
        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert resource.get_absolute_url() in response.url

    def test_unpublished_returns_404(self, client):
        resource = ResourceFactory(published=False)
        response = client.get(resource.get_absolute_url(), follow=True)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_components_of_in_context(self, client):
        parent = ResourceFactory(published=True)
        child = ResourceFactory(published=True)
        ResourceComponentFactory(resource=parent, component_resource=child)
        response = client.get(child.get_absolute_url())
        components_of = list(response.context["components_of"])
        assert len(components_of) == 1
        assert components_of[0].resource == parent

    def test_components_of_excludes_unpublished_parent(self, client):
        unpublished_parent = ResourceFactory(published=False)
        child = ResourceFactory(published=True)
        ResourceComponentFactory(resource=unpublished_parent, component_resource=child)
        response = client.get(child.get_absolute_url())
        assert list(response.context["components_of"]) == []


class TestResourceComponentDownloadView:
    def test_nonexistent_component_returns_404(self, client):
        response = client.get("/en/resources/component/99999/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_unpublished_resource_returns_404(self, client):
        resource = ResourceFactory(published=False)
        component = ResourceComponentFactory(
            resource=resource,
            component_url="https://example.com/",
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_url_component_returns_404(self, client):
        resource = ResourceFactory(published=True)
        component = ResourceComponentFactory(
            resource=resource,
            component_url="https://example.com/",
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_post_returns_405(self, client):
        response = client.post("/en/resources/component/1/download/")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_recursive_component_returns_404(self, client):
        parent = ResourceFactory(published=True)
        child = ResourceFactory(published=True)
        component = ResourceComponentFactory(resource=parent, component_resource=child)
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_file_component_redirects_to_file_url(self, client, file_storage):
        resource = ResourceFactory(published=True)
        component = ResourceComponentFactory(resource=resource, with_file=True)
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FOUND
        assert "test.pdf" in response.url


class TestResourceSearchView:
    def test_get_without_query_returns_200(self, client):
        response = client.get("/en/resources/search/")
        assert response.status_code == HTTPStatus.OK

    def test_get_without_query_returns_empty_results(self, client):
        ResourceFactory(published=True)
        response = client.get("/en/resources/search/")
        assert list(response.context["results"]) == []

    def test_q_in_context(self, client):
        response = client.get("/en/resources/search/?q=python")
        assert response.context["q"] == "python"

    def test_finds_resource_by_name(self, client):
        resource = ResourceFactory(name="Python tutorial", published=True)
        response = client.get("/en/resources/search/?q=python")
        assert resource in list(response.context["results"])

    def test_finds_resource_by_description(self, client):
        resource = ResourceFactory(
            name="Unrelated title",
            description="This covers Django web framework concepts.",
            published=True,
        )
        response = client.get("/en/resources/search/?q=django")
        assert resource in list(response.context["results"])

    def test_excludes_unpublished_resources(self, client):
        ResourceFactory(name="Hidden resource", published=False)
        response = client.get("/en/resources/search/?q=hidden")
        assert list(response.context["results"]) == []

    def test_name_match_ranks_higher_than_description_match(self, client):
        name_match = ResourceFactory(
            name="Python guide",
            description="A general resource.",
            published=True,
        )
        desc_match = ResourceFactory(
            name="General guide",
            description="Covers Python programming.",
            published=True,
        )
        response = client.get("/en/resources/search/?q=python")
        results = list(response.context["results"])
        assert results.index(name_match) < results.index(desc_match)

    def test_websearch_quoted_phrase(self, client):
        resource = ResourceFactory(
            name="Machine learning fundamentals",
            published=True,
        )
        other = ResourceFactory(name="Learning machines separately", published=True)
        response = client.get('/en/resources/search/?q="machine learning"')
        results = list(response.context["results"])
        assert resource in results
        assert other not in results

    def test_websearch_excluded_term(self, client):
        included = ResourceFactory(name="Python tutorial", published=True)
        excluded = ResourceFactory(name="Python Django tutorial", published=True)
        response = client.get("/en/resources/search/?q=python -django")
        results = list(response.context["results"])
        assert included in results
        assert excluded not in results

    def test_finds_resource_by_component_name(self, client):
        resource = ResourceFactory(name="Unrelated title", published=True)
        ResourceComponentFactory(
            resource=resource,
            name="Kubernetes deployment guide",
            component_url="https://example.com/",
        )
        response = client.get("/en/resources/search/?q=kubernetes")
        assert resource in list(response.context["results"])

    def test_finds_resource_by_author_user_name(self, client):
        resource = ResourceFactory(name="Unrelated title", published=True)
        user = UserFactory(first_name="Hildegard", last_name="Peplau")
        resource.author_users.add(user)
        response = client.get("/en/resources/search/?q=hildegard")
        assert resource in list(response.context["results"])

    def test_finds_resource_by_author_entity_name(self, client):
        resource = ResourceFactory(name="Unrelated title", published=True)
        entity = EntityFactory(name="Oceanic Research Institute")
        resource.author_entities.add(entity)
        response = client.get("/en/resources/search/?q=oceanic")
        assert resource in list(response.context["results"])

    def test_empty_query_returns_no_results(self, client):
        ResourceFactory.create_batch(3, published=True)
        response = client.get("/en/resources/search/?q=")
        assert list(response.context["results"]) == []

    def test_whitespace_only_query_treated_as_empty(self, client):
        ResourceFactory(name="Python tutorial", published=True)
        response = client.get("/en/resources/search/?q=++++")
        assert list(response.context["results"]) == []
        assert response.context["q"] == ""

    def test_no_match_query_returns_empty_results(self, client):
        ResourceFactory(name="Python tutorial", published=True)
        response = client.get("/en/resources/search/?q=xyznonexistentterm")
        assert list(response.context["results"]) == []

    def test_resource_matching_both_search_vector_and_tag_name_appears_once(
        self,
        client,
    ):
        category = ResourceCategoryFactory()
        tag = ResourceTagFactory(category=category, name="Kubernetes")
        resource = ResourceFactory(name="Kubernetes tutorial", published=True)
        resource.tags.add(tag)
        response = client.get("/en/resources/search/?q=kubernetes")
        results = list(response.context["results"])
        assert results.count(resource) == 1

    def test_form_initial_q_matches_query(self, client):
        response = client.get("/en/resources/search/?q=python")
        assert response.context["form"].initial["q"] == "python"

    def test_selected_tag_slugs_empty_when_no_tags(self, client):
        response = client.get("/en/resources/search/?q=python")
        assert response.context["selected_tag_slugs"] == set()


class TestResourceSearchTagFiltering:
    def test_single_tag_filters_results(self, client):
        category = ResourceCategoryFactory()
        tag = ResourceTagFactory(category=category, name="Year 9")
        other_tag = ResourceTagFactory(category=category, name="Year 10")
        tagged = ResourceFactory(published=True)
        tagged.tags.add(tag)
        other = ResourceFactory(published=True)
        other.tags.add(other_tag)
        response = client.get(f"/en/resources/search/?tag={tag.slug}")
        results = list(response.context["results"])
        assert tagged in results
        assert other not in results

    def test_or_within_category(self, client):
        category = ResourceCategoryFactory()
        tag_a = ResourceTagFactory(category=category, name="Year 9")
        tag_b = ResourceTagFactory(category=category, name="Year 10")
        r_a = ResourceFactory(published=True)
        r_a.tags.add(tag_a)
        r_b = ResourceFactory(published=True)
        r_b.tags.add(tag_b)
        response = client.get(
            f"/en/resources/search/?tag={tag_a.slug}&tag={tag_b.slug}",
        )
        results = list(response.context["results"])
        assert r_a in results
        assert r_b in results

    def test_and_across_categories(self, client):
        c1 = ResourceCategoryFactory()
        c2 = ResourceCategoryFactory()
        tag_c1 = ResourceTagFactory(category=c1, name="Year 9")
        tag_c2 = ResourceTagFactory(category=c2, name="English")
        both = ResourceFactory(published=True)
        both.tags.add(tag_c1, tag_c2)
        only_c1 = ResourceFactory(published=True)
        only_c1.tags.add(tag_c1)
        response = client.get(
            f"/en/resources/search/?tag={tag_c1.slug}&tag={tag_c2.slug}",
        )
        results = list(response.context["results"])
        assert both in results
        assert only_c1 not in results

    def test_unpublished_excluded_when_tag_matches(self, client):
        category = ResourceCategoryFactory()
        tag = ResourceTagFactory(category=category)
        hidden = ResourceFactory(published=False)
        hidden.tags.add(tag)
        response = client.get(f"/en/resources/search/?tag={tag.slug}")
        assert list(response.context["results"]) == []

    def test_combined_query_and_tag_filter(self, client):
        category = ResourceCategoryFactory()
        tag = ResourceTagFactory(category=category)
        match = ResourceFactory(name="Python tutorial", published=True)
        match.tags.add(tag)
        query_only = ResourceFactory(name="Python advanced", published=True)
        tag_only = ResourceFactory(name="Unrelated", published=True)
        tag_only.tags.add(tag)
        response = client.get(
            f"/en/resources/search/?q=python&tag={tag.slug}",
        )
        results = list(response.context["results"])
        assert match in results
        assert query_only not in results
        assert tag_only not in results

    def test_full_text_search_finds_resource_by_tag_name(self, client):
        category = ResourceCategoryFactory(name="Subject")
        tag = ResourceTagFactory(category=category, name="Xyzzy")
        resource = ResourceFactory(name="Unrelated title", published=True)
        resource.tags.add(tag)
        response = client.get("/en/resources/search/?q=xyzzy")
        assert resource in list(response.context["results"])

    def test_categories_in_form(self, client):
        category = ResourceCategoryFactory(name="Year Level")
        ResourceTagFactory(category=category, name="Year 9")
        response = client.get("/en/resources/search/")
        categories = list(response.context["form"].categories)
        assert category in categories

    def test_selected_tag_slugs_populated_in_context(self, client):
        category = ResourceCategoryFactory()
        tag = ResourceTagFactory(category=category)
        response = client.get(f"/en/resources/search/?tag={tag.slug}")
        assert tag.slug in response.context["selected_tag_slugs"]

    def test_nonexistent_tag_slug_returns_empty_results(self, client):
        ResourceFactory(published=True)
        response = client.get("/en/resources/search/?tag=does-not-exist")
        assert response.status_code == HTTPStatus.OK
        assert list(response.context["results"]) == []

    def test_resource_with_multiple_matching_tags_in_category_appears_once(
        self,
        client,
    ):
        category = ResourceCategoryFactory()
        tag_a = ResourceTagFactory(category=category, name="Year 9")
        tag_b = ResourceTagFactory(category=category, name="Year 10")
        resource = ResourceFactory(published=True)
        resource.tags.add(tag_a, tag_b)
        response = client.get(
            f"/en/resources/search/?tag={tag_a.slug}&tag={tag_b.slug}",
        )
        results = list(response.context["results"])
        assert results.count(resource) == 1

    def test_three_category_and_combination(self, client):
        c1, c2, c3 = (
            ResourceCategoryFactory(),
            ResourceCategoryFactory(),
            ResourceCategoryFactory(),
        )
        tag1 = ResourceTagFactory(category=c1, name="Year 9")
        tag2 = ResourceTagFactory(category=c2, name="English")
        tag3 = ResourceTagFactory(category=c3, name="Beginner")
        all_three = ResourceFactory(published=True)
        all_three.tags.add(tag1, tag2, tag3)
        missing_one = ResourceFactory(published=True)
        missing_one.tags.add(tag1, tag2)
        response = client.get(
            f"/en/resources/search/?tag={tag1.slug}&tag={tag2.slug}&tag={tag3.slug}",
        )
        results = list(response.context["results"])
        assert all_three in results
        assert missing_one not in results


_MEMBERSHIP_PATCH = "ams.resources.views.user_has_active_membership"


class TestResourceVisibilityDownload:
    """Download view gating by visibility level."""

    def _make_file_component(self, visibility):
        resource = ResourceFactory(published=True, visibility=visibility)
        return ResourceComponentFactory(resource=resource, with_file=True)

    def test_public_download_accessible_to_anonymous(self, client, file_storage):
        component = self._make_file_component(Resource.Visibility.PUBLIC)
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FOUND

    def test_download_account_required_denied_to_anonymous(self, client, file_storage):
        component = self._make_file_component(
            Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED,
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_download_account_required_allowed_to_authenticated(
        self,
        client,
        file_storage,
    ):
        user = UserFactory()
        client.force_login(user)
        component = self._make_file_component(
            Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED,
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FOUND

    def test_download_membership_required_denied_to_non_member(
        self,
        client,
        file_storage,
    ):
        user = UserFactory()
        client.force_login(user)
        component = self._make_file_component(
            Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_download_membership_required_allowed_to_member(self, client, file_storage):
        user = UserFactory()
        client.force_login(user)
        component = self._make_file_component(
            Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FOUND

    def test_members_only_download_denied_to_anonymous(self, client, file_storage):
        component = self._make_file_component(Resource.Visibility.MEMBERS_ONLY)
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_members_only_download_allowed_to_member(self, client, file_storage):
        user = UserFactory()
        client.force_login(user)
        component = self._make_file_component(Resource.Visibility.MEMBERS_ONLY)
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.FOUND


class TestResourceVisibilityDetail:
    """Detail view gating: only MEMBERS_ONLY restricts browsing."""

    def test_members_only_detail_denied_to_anonymous(self, client):
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_members_only_detail_denied_to_non_member(self, client):
        user = UserFactory()
        client.force_login(user)
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_members_only_detail_allowed_to_member(self, client):
        user = UserFactory()
        client.force_login(user)
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_download_account_required_detail_accessible_to_anonymous(self, client):
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED,
        )
        response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_download_membership_required_detail_accessible_to_anonymous(self, client):
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_can_download_context_false_for_non_member_on_membership_required(
        self,
        client,
    ):
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get(resource.get_absolute_url())
        assert response.context["can_download"] is False

    def test_can_download_context_true_for_member_on_membership_required(self, client):
        user = UserFactory()
        client.force_login(user)
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get(resource.get_absolute_url())
        assert response.context["can_download"] is True


class TestResourceVisibilityListing:
    """Home and search views exclude MEMBERS_ONLY resources from non-members."""

    def test_home_hides_members_only_from_non_members(self, client):
        visible = ResourceFactory(published=True, visibility=Resource.Visibility.PUBLIC)
        hidden = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get("/en/resources/")
        resources = list(response.context["resources"])
        assert visible in resources
        assert hidden not in resources

    def test_home_shows_members_only_to_members(self, client):
        resource = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get("/en/resources/")
        assert resource in list(response.context["resources"])

    def test_home_shows_download_restricted_resources_to_anonymous(self, client):
        r1 = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED,
        )
        r2 = ResourceFactory(
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        response = client.get("/en/resources/")
        resources = list(response.context["resources"])
        assert r1 in resources
        assert r2 in resources

    def test_search_hides_members_only_from_non_members(self, client):
        hidden = ResourceFactory(
            name="Hidden resource",
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=False):
            response = client.get("/en/resources/search/?q=hidden")
        assert hidden not in list(response.context["results"])

    def test_search_shows_members_only_to_members(self, client):
        resource = ResourceFactory(
            name="Members resource",
            published=True,
            visibility=Resource.Visibility.MEMBERS_ONLY,
        )
        with patch(_MEMBERSHIP_PATCH, return_value=True):
            response = client.get("/en/resources/search/?q=members")
        assert resource in list(response.context["results"])

    def test_search_shows_download_restricted_resources_to_anonymous(self, client):
        r1 = ResourceFactory(
            name="Account resource",
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_ACCOUNT_REQUIRED,
        )
        r2 = ResourceFactory(
            name="Membership resource",
            published=True,
            visibility=Resource.Visibility.DOWNLOAD_MEMBERSHIP_REQUIRED,
        )
        response = client.get("/en/resources/search/?q=resource")
        results = list(response.context["results"])
        assert r1 in results
        assert r2 in results
