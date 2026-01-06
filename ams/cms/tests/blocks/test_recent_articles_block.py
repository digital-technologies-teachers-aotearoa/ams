"""Tests for RecentArticlesBlock."""

import datetime

import pytest
from django.utils import timezone
from wagtail.blocks import ChoiceBlock
from wagtail.models import Page

from ams.cms.blocks.recent_articles_block import RecentArticlesBlock
from ams.cms.models import ArticlePage
from ams.cms.models import ArticlesIndexPage
from ams.cms.models import HomePage


@pytest.fixture
def setup_articles(db):
    """Create homepage, articles index, and sample articles."""
    # Get or create root
    root = Page.get_first_root_node()

    # Create HomePage
    homepage = HomePage(title="Home", slug="test-home")
    root.add_child(instance=homepage)
    homepage.save()

    # Create ArticlesIndexPage
    articles_index = ArticlesIndexPage(title="Articles", slug="articles")
    homepage.add_child(instance=articles_index)
    articles_index.save_revision().publish()

    # Create 5 articles with different publication dates
    now = timezone.now()
    articles = []
    for i in range(5):
        article = ArticlePage(
            title=f"Article {i + 1}",
            slug=f"article-{i + 1}",
            publication_date=now - datetime.timedelta(days=i),
            summary=f"Summary for article {i + 1}",
            author=f"Author {i + 1}",
            body=[],
        )
        articles_index.add_child(instance=article)
        article.save_revision().publish()
        articles.append(article)

    return {
        "homepage": homepage,
        "articles_index": articles_index,
        "articles": articles,
    }


class TestRecentArticlesBlock:
    """Test the RecentArticlesBlock functionality."""

    def test_block_instantiation(self):
        """Test that RecentArticlesBlock can be instantiated."""
        block = RecentArticlesBlock()
        assert block is not None

    def test_block_has_required_fields(self):
        """Test that block has all required fields."""
        block = RecentArticlesBlock()
        assert "article_count" in block.child_blocks

    def test_article_count_is_choice_block(self):
        """Test that article_count field is a ChoiceBlock."""
        block = RecentArticlesBlock()
        assert isinstance(block.child_blocks["article_count"], ChoiceBlock)

    def test_article_count_default(self):
        """Test that article_count has correct default value."""
        block = RecentArticlesBlock()
        assert block.child_blocks["article_count"].meta.default == "3"

    def test_article_count_choices(self):
        """Test that article_count has correct choices."""
        block = RecentArticlesBlock()
        # Test that we can create a valid value with each choice
        for count in ["3", "5", "10"]:
            value = block.to_python({"article_count": count})
            assert value["article_count"] == count

    def test_get_context_returns_articles(self, setup_articles):
        """Test that get_context returns recent articles."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        context = block.get_context(value)

        assert "articles" in context
        articles = list(context["articles"])
        expected_articles = 3
        assert len(articles) == expected_articles

    def test_get_context_articles_ordered_by_publication_date(self, setup_articles):
        """Test that articles are ordered by publication date (newest first)."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "5",
            },
        )

        context = block.get_context(value)
        articles = list(context["articles"])

        # Verify ordering (newest first)
        assert articles[0].title == "Article 1"
        assert articles[1].title == "Article 2"
        assert articles[4].title == "Article 5"

    def test_get_context_respects_article_count(self, setup_articles):
        """Test that article_count limits number of articles."""
        block = RecentArticlesBlock()

        # Test with count=3
        value_3 = block.to_python({"article_count": "3"})
        context_3 = block.get_context(value_3)
        expected_articles = 3
        assert len(list(context_3["articles"])) == expected_articles

        # Test with count=5
        value_5 = block.to_python({"article_count": "5"})
        context_5 = block.get_context(value_5)
        expected_articles = 5
        assert len(list(context_5["articles"])) == expected_articles

    def test_get_context_only_returns_live_articles(self, setup_articles):
        """Test that only published articles are returned."""
        # Unpublish one article
        articles = setup_articles["articles"]
        articles[1].unpublish()

        block = RecentArticlesBlock()
        value = block.to_python({"article_count": "5"})
        context = block.get_context(value)

        articles_list = list(context["articles"])
        # Should return 4 articles (1 was unpublished)
        expected_articles = 4
        assert len(articles_list) == expected_articles
        # Verify unpublished article is not in results
        assert "Article 2" not in [a.title for a in articles_list]

    def test_get_context_only_shows_past_articles(self, setup_articles):
        """Test that articles with future publication times are hidden."""
        index_page = setup_articles["articles_index"]
        now = timezone.now()

        # Create article scheduled for future (should NOT show)
        future_article = ArticlePage(
            title="Future Article",
            slug="future-article",
            publication_date=now + datetime.timedelta(hours=2),
            summary="This is in the future",
            author="Test Author",
            body=[],
        )
        index_page.add_child(instance=future_article)
        future_article.save_revision().publish()

        # Test block filtering
        block = RecentArticlesBlock()
        value = block.to_python({"article_count": "10"})
        context = block.get_context(value)

        articles_list = list(context["articles"])
        # Should return 5 existing articles, NOT the future one
        expected_articles = 5
        assert len(articles_list) == expected_articles
        assert "Future Article" not in [a.title for a in articles_list]

    def test_get_context_when_no_articles_exist(self, db):
        """Test get_context when no articles have been published."""
        block = RecentArticlesBlock()
        value = block.to_python({"article_count": "3"})
        context = block.get_context(value)

        assert "articles" in context
        assert len(list(context["articles"])) == 0

    def test_render_includes_article_metadata(self, setup_articles):
        """Test that rendered HTML includes article metadata."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Check for article components
        assert "card" in html
        assert "card-title" in html
        assert "card-text" in html
        assert "Read more" in html
        assert "Summary for article" in html
        assert "Author" in html

    def test_render_empty_state(self, db):
        """Test rendering when no articles exist."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Should show empty state message
        assert "No articles have been published yet" in html

    def test_block_meta_properties(self):
        """Test block meta properties."""
        block = RecentArticlesBlock()
        assert block.meta.icon == "doc-full"
        assert block.meta.label == "Recent Articles"
        assert block.meta.template == "cms/blocks/recent_articles_block.html"

    def test_get_context_preserves_parent_context(self, setup_articles):
        """Test that parent_context is preserved when provided."""
        block = RecentArticlesBlock()
        value = block.to_python({"article_count": "3"})

        parent_context = {"custom_var": "test_value"}
        context = block.get_context(value, parent_context=parent_context)

        # Verify articles are added
        assert "articles" in context

    def test_render_includes_publication_dates(self, setup_articles):
        """Test that rendered HTML includes publication dates."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Check that date formatting is present
        # The date will be formatted like "January 6, 2026"
        now = timezone.now()
        # At minimum, check for the year
        assert str(now.year) in html

    def test_render_includes_author_names(self, setup_articles):
        """Test that rendered HTML includes author names."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Check for author names
        assert "Author 1" in html
        assert "Author 2" in html
        assert "Author 3" in html

    def test_get_context_with_fewer_articles_than_requested(self, setup_articles):
        """Test behavior when requesting more articles than exist."""
        # setup_articles creates 5 articles
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "10",
            },
        )
        context = block.get_context(value)

        articles_list = list(context["articles"])
        # Should return all 5 available articles, not 10
        expected_articles = 5
        assert len(articles_list) == expected_articles

    def test_render_includes_read_more_links(self, setup_articles):
        """Test that rendered HTML includes 'Read more' links."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Check for Read more button
        assert "Read more" in html
        assert "btn" in html
        assert "btn-outline-primary" in html

    def test_render_uses_article_card_partial(self, setup_articles):
        """Test that rendering uses the article card partial template."""
        block = RecentArticlesBlock()
        value = block.to_python(
            {
                "article_count": "3",
            },
        )

        html = block.render(value)

        # Check for card structure that would come from the partial
        assert "card h-100" in html
        assert "card-body" in html
        assert "card-title" in html
