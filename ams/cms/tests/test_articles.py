import datetime
from http import HTTPStatus

import pytest
from django.test import Client
from django.test import RequestFactory
from django.utils import timezone
from wagtail.fields import StreamField
from wagtail.models import Page

from ams.cms.models import ArticlePage
from ams.cms.models import ArticlesIndexPage
from ams.cms.models import HomePage


@pytest.mark.django_db
class TestArticlesIndexPage:
    """Tests for ArticlesIndexPage model."""

    def setup_method(self):
        """Set up test data."""
        self.homepage = HomePage.objects.first()
        if not self.homepage:
            root = Page.get_first_root_node()
            self.homepage = HomePage(title="Home", slug="home")
            root.add_child(instance=self.homepage)
            self.homepage.save()

        self.client = Client()

    def create_articles_index_page(self):
        """Create an ArticlesIndexPage."""
        page = ArticlesIndexPage(
            title="Articles",
            slug="articles",
            intro="<p>Welcome to our articles</p>",
        )
        self.homepage.add_child(instance=page)
        page.save_revision().publish()
        return page

    def create_article(
        self,
        index_page,
        title,
        publication_date,
        summary="Test summary",
    ):
        """Create an ArticlePage under the given index page."""
        article = ArticlePage(
            title=title,
            slug=title.lower().replace(" ", "-"),
            publication_date=publication_date,
            summary=summary,
            author="Test Author",
            body=[],
        )
        index_page.add_child(instance=article)
        article.save_revision().publish()
        return article

    def test_articles_index_page_creation(self):
        """Test that ArticlesIndexPage can be created."""
        index_page = self.create_articles_index_page()
        assert index_page.title == "Articles"
        assert index_page.intro == "<p>Welcome to our articles</p>"

    def test_articles_index_page_only_allows_article_children(self):
        """Test that ArticlesIndexPage only allows ArticlePage as children."""
        index_page = self.create_articles_index_page()
        assert index_page.subpage_types == ["cms.ArticlePage"]

    def test_articles_index_page_only_under_homepage(self):
        """Test that ArticlesIndexPage can only be created under HomePage."""
        index_page = ArticlesIndexPage(
            title="Test Articles Index",
            slug="test-articles",
        )
        assert "cms.HomePage" in index_page.parent_page_types

    def test_get_context_returns_articles(self):
        """Test that get_context returns articles ordered by publication date."""
        index_page = self.create_articles_index_page()

        # Create articles with different publication dates
        now = timezone.now()
        article1 = self.create_article(
            index_page,
            "Oldest Article",
            now - datetime.timedelta(days=10),
        )
        article2 = self.create_article(
            index_page,
            "Newest Article",
            now,
        )
        article3 = self.create_article(
            index_page,
            "Middle Article",
            now - datetime.timedelta(days=5),
        )

        # Get context
        request = RequestFactory().get(index_page.url)
        context = index_page.get_context(request)

        # Check articles are in context and ordered correctly
        assert "articles" in context
        articles = list(context["articles"])
        expected_articles = 3
        assert len(articles) == expected_articles
        assert articles[0].id == article2.id  # Newest first
        assert articles[1].id == article3.id  # Middle
        assert articles[2].id == article1.id  # Oldest last

    def test_get_context_only_returns_live_articles(self):
        """Test that get_context only returns published articles."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create a published article
        published_article = self.create_article(
            index_page,
            "Published Article",
            now,
        )

        # Create an unpublished article (publish then unpublish)
        unpublished_article = ArticlePage(
            title="Unpublished Article",
            slug="unpublished",
            publication_date=now,
            summary="Test summary",
            author="Test Author",
            body=[],
        )
        index_page.add_child(instance=unpublished_article)
        unpublished_article.save_revision().publish()
        unpublished_article.unpublish()

        # Get context
        request = RequestFactory().get(index_page.url)
        context = index_page.get_context(request)

        # Check only published article is returned
        articles = list(context["articles"])
        assert len(articles) == 1
        assert articles[0].id == published_article.id

    def test_get_context_only_shows_past_articles(self):
        """Test that articles with future publication dates are hidden."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create article in the past (should show)
        past_article = self.create_article(
            index_page,
            "Past Article",
            now - datetime.timedelta(hours=1),
        )

        # Create article in the future (should NOT show)
        self.create_article(
            index_page,
            "Future Article",
            now + datetime.timedelta(hours=1),
        )

        # Get context
        request = RequestFactory().get(index_page.url)
        context = index_page.get_context(request)

        # Check only past article is returned
        articles = list(context["articles"])
        assert len(articles) == 1
        assert articles[0].id == past_article.id

    def test_pagination_with_12_articles(self):
        """Test that pagination works correctly with exactly 12 articles."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create exactly 12 articles
        for i in range(12):
            self.create_article(
                index_page,
                f"Article {i + 1}",
                now - datetime.timedelta(days=i),
            )

        # Get context for page 1
        request = RequestFactory().get(index_page.url)
        context = index_page.get_context(request)

        # All 12 should be on page 1
        articles = context["articles"]
        expected_articles = 12
        assert len(list(articles)) == expected_articles
        assert articles.paginator.num_pages == 1

    def test_pagination_with_25_articles(self):
        """Test that pagination works correctly with 25 articles (3 pages)."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create 25 articles
        for i in range(25):
            self.create_article(
                index_page,
                f"Article {i + 1}",
                now - datetime.timedelta(days=i),
            )

        # Test page 1
        request = RequestFactory().get(index_page.url + "?page=1")
        context = index_page.get_context(request)
        articles = context["articles"]
        expected_pages = 3
        expected_page_1_articles = 12
        assert len(list(articles)) == expected_page_1_articles
        assert articles.paginator.num_pages == expected_pages

        # Test page 2
        request = RequestFactory().get(index_page.url + "?page=2")
        context = index_page.get_context(request)
        articles = context["articles"]
        expected_page_2_articles = 12
        assert len(list(articles)) == expected_page_2_articles

        # Test page 3 (last page with only 1 article)
        request = RequestFactory().get(index_page.url + "?page=3")
        context = index_page.get_context(request)
        articles = context["articles"]
        expected_page_3_articles = 1
        assert len(list(articles)) == expected_page_3_articles

    def test_pagination_invalid_page_defaults_to_page_1(self):
        """Test that invalid page numbers default to page 1."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create 13 articles (2 pages)
        for i in range(13):
            self.create_article(
                index_page,
                f"Article {i + 1}",
                now - datetime.timedelta(days=i),
            )

        # Test with invalid page number
        request = RequestFactory().get(index_page.url + "?page=invalid")
        context = index_page.get_context(request)
        articles = context["articles"]
        assert articles.number == 1

    def test_pagination_out_of_range_returns_last_page(self):
        """Test that out of range page numbers return the last page."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create 13 articles (2 pages)
        for i in range(13):
            self.create_article(
                index_page,
                f"Article {i + 1}",
                now - datetime.timedelta(days=i),
            )

        # Test with page number beyond range
        request = RequestFactory().get(index_page.url + "?page=999")
        context = index_page.get_context(request)
        articles = context["articles"]
        expected_page = 2  # Last page
        assert articles.number == expected_page

    def test_articles_index_page_renders(self):
        """Test that the ArticlesIndexPage renders correctly."""
        index_page = self.create_articles_index_page()
        now = timezone.now()

        # Create a couple of articles
        self.create_article(index_page, "Test Article 1", now)
        self.create_article(
            index_page,
            "Test Article 2",
            now - datetime.timedelta(days=1),
        )

        response = self.client.get(index_page.url)
        assert response.status_code == HTTPStatus.OK
        assert b"Test Article 1" in response.content
        assert b"Test Article 2" in response.content


@pytest.mark.django_db
class TestArticlePage:
    """Tests for ArticlePage model."""

    def setup_method(self):
        """Set up test data."""
        self.homepage = HomePage.objects.first()
        if not self.homepage:
            root = Page.get_first_root_node()
            self.homepage = HomePage(title="Home", slug="home")
            root.add_child(instance=self.homepage)
            self.homepage.save()

        # Create ArticlesIndexPage
        self.articles_index = ArticlesIndexPage(
            title="Articles",
            slug="articles",
        )
        self.homepage.add_child(instance=self.articles_index)
        self.articles_index.save_revision().publish()

        self.client = Client()

    def create_article(self, **kwargs):
        """Create an ArticlePage with default values."""
        defaults = {
            "title": "Test Article",
            "slug": "test-article",
            "publication_date": timezone.now(),
            "summary": "This is a test article summary",
            "author": "Test Author",
            "body": [],
        }
        defaults.update(kwargs)

        article = ArticlePage(**defaults)
        self.articles_index.add_child(instance=article)
        article.save_revision().publish()
        return article

    def test_article_page_creation(self):
        """Test that ArticlePage can be created with required fields."""
        article = self.create_article()
        assert article.title == "Test Article"
        assert article.summary == "This is a test article summary"
        assert article.author == "Test Author"
        assert isinstance(article.publication_date, datetime.datetime)

    def test_article_page_only_under_articles_index(self):
        """Test that ArticlePage can only be created under ArticlesIndexPage."""
        article = ArticlePage(
            title="Test Article",
            slug="test",
            publication_date=timezone.now(),
            summary="Test",
            body=[],
        )
        assert article.parent_page_types == ["cms.ArticlesIndexPage"]

    def test_article_page_no_children_allowed(self):
        """Test that ArticlePage cannot have child pages."""
        article = self.create_article()
        assert article.subpage_types == []

    def test_meta_ordering_defined(self):
        """Test that ArticlePage has Meta.ordering defined for publication_date."""
        # Check that the model has the expected Meta.ordering
        assert hasattr(ArticlePage, "_meta")
        assert hasattr(ArticlePage._meta, "ordering")  # noqa: SLF001
        assert ArticlePage._meta.ordering == ["-publication_date"]  # noqa: SLF001

    def test_article_page_author_optional(self):
        """Test that author field is optional."""
        article = self.create_article(author="")
        assert article.author == ""

    def test_article_page_renders(self):
        """Test that ArticlePage renders correctly."""
        article = self.create_article()
        response = self.client.get(article.url)
        assert response.status_code == HTTPStatus.OK
        assert b"Test Article" in response.content
        assert b"Test Author" in response.content

    def test_article_page_renders_without_summary(self):
        """Test that ArticlePage renders without the summary.

        This is used for card links only.
        """
        article = self.create_article()
        response = self.client.get(article.url)
        assert response.status_code == HTTPStatus.OK
        assert b"This is a test article summary" not in response.content

    def test_article_page_uses_content_stream_blocks(self):
        """Test that ArticlePage uses ContentStreamBlocks for body."""
        article = self.create_article()
        # Check that the body field exists and uses StreamField
        assert hasattr(article, "body")
        assert isinstance(article._meta.get_field("body"), StreamField)  # noqa: SLF001
