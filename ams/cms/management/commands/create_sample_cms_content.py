"""Management command to create sample CMS content for the English site."""

from pathlib import Path

from django.conf import settings
from django.core import management
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.images import get_image_model
from wagtail.models import Locale
from wagtail.models import Site
from wagtailmenus.models import FlatMenu
from wagtailmenus.models import FlatMenuItem
from wagtailmenus.models import MainMenu
from wagtailmenus.models import MainMenuItem

from ams.cms.models import ArticlePage
from ams.cms.models import ArticlesIndexPage
from ams.cms.models import ContentPage
from ams.cms.models import HomePage
from ams.utils.management.commands._constants import LOG_HEADER

FIXTURES_DIR = Path(__file__).parent / ".." / "fixtures"


class Command(management.base.BaseCommand):
    help = "Create sample CMS content for the English site"

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("🌐 Creating sample CMS content"))

        self.stdout.write("🖼️  Creating placeholder images...")
        images = self._create_images()

        for lang_code, lang_name in settings.LANGUAGES:
            self.stdout.write(f"\n🌐 Processing {lang_name} site...")
            prefix = "" if lang_code == "en" else f"[{lang_code.upper()}] "

            try:
                locale = Locale.objects.get(language_code=lang_code)
                home = HomePage.objects.get(locale=locale)
                site = Site.objects.get(sitesettings__language=lang_code)
            except (Locale.DoesNotExist, HomePage.DoesNotExist, Site.DoesNotExist):
                self.stdout.write(f"  ⚠️  Site for {lang_name} not ready, skipping.")
                continue

            self.stdout.write("📄 Creating pages...")
            pages = self._create_pages(home, images, prefix=prefix)

            self.stdout.write("🏠 Building homepage body...")
            self._build_homepage_body(home, images, pages, prefix=prefix)

            self.stdout.write("🗺️  Creating navigation menus...")
            self._create_menus(site, pages, prefix=prefix)

        self.stdout.write("\n✅ Sample CMS content created.")

    # -------------------------------------------------------------------------
    # Images
    # -------------------------------------------------------------------------

    def _get_or_create_image(self, title, fixture_filename):
        image_model = get_image_model()
        try:
            return image_model.objects.get(title=title)
        except image_model.DoesNotExist:
            pass

        fixture_path = FIXTURES_DIR / fixture_filename
        with fixture_path.open("rb") as f:
            content = f.read()

        # SimpleUploadedFile lets Wagtail read image dimensions from memory
        # before the file is transferred to remote storage.
        file_obj = SimpleUploadedFile(
            fixture_filename,
            content,
            content_type="image/png",
        )
        image = image_model(title=title, file=file_obj)
        image.save()
        self.stdout.write(f"  ✅ Created image: {title}")
        return image

    def _create_images(self):
        return {
            "hero": self._get_or_create_image(
                "Sample Hero Image",
                "placeholder_hero.png",
            ),
            "content": self._get_or_create_image(
                "Sample Content Image",
                "placeholder_landscape.png",
            ),
            "grid": self._get_or_create_image(
                "Sample Grid Image",
                "placeholder_grid.png",
            ),
            "square": self._get_or_create_image(
                "Sample Square Image",
                "placeholder_square.png",
            ),
        }

    # -------------------------------------------------------------------------
    # Pages
    # -------------------------------------------------------------------------

    def _get_or_create_child_page(self, parent, page_class, slug, **kwargs):
        existing = parent.get_children().filter(slug=slug).first()
        if existing:
            self.stdout.write(f"  ⏭️  Page already exists: {slug}")
            return existing.specific
        page = page_class(slug=slug, **kwargs)
        parent.add_child(instance=page)
        self.stdout.write(f"  ✅ Created page: {slug}")
        return page

    def _create_pages(self, home, images, prefix=""):
        about = self._get_or_create_child_page(
            home,
            ContentPage,
            "about",
            title=f"{prefix}About",
            body=[],
        )

        team = self._get_or_create_child_page(
            about,
            ContentPage,
            "team",
            title=f"{prefix}About — Team",
            body=[],
        )

        members = self._get_or_create_child_page(
            home,
            ContentPage,
            "members-only",
            title=f"{prefix}Members Only",
            visibility=ContentPage.VISIBILITY_MEMBERS,
            body=[],
        )

        articles_index = self._get_or_create_child_page(
            home,
            ArticlesIndexPage,
            "articles",
            title=f"{prefix}Articles",
            intro=f"<p>{prefix}Read our latest articles and updates.</p>",
        )

        article_body = [
            (
                "paragraph_block",
                f"<p>{prefix}This is a sample article created for "
                "demonstration purposes.</p>",
            ),
        ]

        article1 = self._get_or_create_child_page(
            articles_index,
            ArticlePage,
            "sample-article-welcome",
            title=f"{prefix}Welcome to AMS",
            summary=f"{prefix}An introduction to our association management system.",
            author=f"{prefix}The AMS Team",
            body=article_body,
            cover_image=images["content"],
        )

        article2 = self._get_or_create_child_page(
            articles_index,
            ArticlePage,
            "sample-article-community-update",
            title=f"{prefix}Community Update",
            summary=f"{prefix}The latest news and updates from our community.",
            author=f"{prefix}The AMS Team",
            body=article_body,
            cover_image=images["content"],
        )

        article3 = self._get_or_create_child_page(
            articles_index,
            ArticlePage,
            "sample-article-upcoming-events",
            title=f"{prefix}Upcoming Events",
            summary=f"{prefix}What's on the horizon for our association.",
            author=f"{prefix}The AMS Team",
            body=article_body,
            cover_image=images["content"],
        )

        return {
            "about": about,
            "team": team,
            "members": members,
            "articles_index": articles_index,
            "articles": [article1, article2, article3],
        }

    # -------------------------------------------------------------------------
    # Homepage body
    # -------------------------------------------------------------------------

    def _build_homepage_body(self, home, images, pages, prefix=""):
        hero = images["hero"]
        content_img = images["content"]
        grid_img = images["grid"]
        square_img = images["square"]

        body = [
            # ------------------------------------------------------------------
            # 1. Intro
            # ------------------------------------------------------------------
            (
                "paragraph_block",
                (
                    f"<p><strong>{prefix}This is a sample/test website</strong> "
                    "demonstrating AMS features. Use it to explore "
                    "available blocks and page types.</p>"
                    f"<p>{prefix}Key pages: "
                    f'<a href="/en/about/">{prefix}About</a> &bull; '
                    f'<a href="/events/">{prefix}Events</a> &bull; '
                    f'<a href="/resources/">{prefix}Resources</a> &bull; '
                    f'<a href="/en/members-only/">{prefix}Members Only</a> &bull; '
                    f'<a href="#content-examples">{prefix}Content Examples &darr;</a>'
                    "</p>"
                ),
            ),
            # ------------------------------------------------------------------
            # 2-3. TitleBlock (HomePage-only)
            # ------------------------------------------------------------------
            (
                "title_block",
                {
                    "title": {
                        "text": f"{prefix}Welcome to AMS",
                        "size": "3",
                        "colour": "#222222",
                        "font_weight": "bold",
                    },
                    "subtitle": {
                        "text": "",
                        "size": "5",
                        "colour": "#555555",
                        "font_weight": "normal",
                        "position": "after",
                    },
                    "alignment": "center",
                },
            ),
            (
                "title_block",
                {
                    "title": {
                        "text": f"{prefix}TitleBlock with Subtitle",
                        "size": "3",
                        "colour": "#222222",
                        "font_weight": "bold",
                    },
                    "subtitle": {
                        "text": f"{prefix}This subtitle appears below the main title",
                        "size": "5",
                        "colour": "#555555",
                        "font_weight": "normal",
                        "position": "after",
                    },
                    "alignment": "center",
                },
            ),
            # ------------------------------------------------------------------
            # 4-5. ColumnsBlock (HomePage-only variants)
            # ------------------------------------------------------------------
            (
                "columns_block",
                {
                    "layout": "2-equal",
                    "columns": [
                        [
                            (
                                "paragraph_block",
                                f"<p><strong>{prefix}Left column</strong> — "
                                "2-equal layout. Both columns share "
                                "the width equally.</p>",
                            ),
                        ],
                        [
                            (
                                "paragraph_block",
                                f"<p><strong>{prefix}Right column</strong> — "
                                "2-equal layout. This is the second "
                                "equal-width column.</p>",
                            ),
                        ],
                    ],
                },
            ),
            (
                "columns_block",
                {
                    "layout": "2-thirds-1-third",
                    "columns": [
                        [
                            (
                                "paragraph_block",
                                f"<p><strong>{prefix}Wide column (2/3)</strong> — "
                                "2-thirds-1-third layout. This column "
                                "takes two thirds of the width, ideal "
                                "for main content.</p>",
                            ),
                        ],
                        [
                            (
                                "paragraph_block",
                                f"<p><strong>{prefix}Narrow column (1/3)</strong> — "
                                "Sidebar width. Use for supplementary "
                                "content.</p>",
                            ),
                        ],
                    ],
                },
            ),
            # ------------------------------------------------------------------
            # 6. FullWidthSectionBlock with background image (HomePage-only)
            # ------------------------------------------------------------------
            (
                "full_width_section_block",
                {
                    "heading": f"{prefix}Key Features",
                    "text": f"<p>{prefix}Explore what AMS has to offer.</p>",
                    "background_image": hero,
                    "background_image_opacity": "25",
                    "colour_mode": "dark",
                    "item_shape": "default",
                    "items": [
                        {
                            "text": f"{prefix}About Us",
                            "link_page": pages["about"],
                            "link_url": "",
                            "background_image": None,
                            "background_image_opacity": "15",
                            "background_colour": "#1a6b8a",
                            "colour_mode": "dark",
                        },
                        {
                            "text": f"{prefix}Events",
                            "link_page": None,
                            "link_url": "/events/",
                            "background_image": None,
                            "background_image_opacity": "15",
                            "background_colour": "#2d5a27",
                            "colour_mode": "dark",
                        },
                        {
                            "text": f"{prefix}Members Only",
                            "link_page": pages["members"],
                            "link_url": "",
                            "background_image": None,
                            "background_image_opacity": "15",
                            "background_colour": "#6b3a8a",
                            "colour_mode": "dark",
                        },
                    ],
                },
            ),
            # ------------------------------------------------------------------
            # 7. RecentArticlesBlock (HomePage-only)
            # ------------------------------------------------------------------
            (
                "recent_articles_block",
                {"article_count": "3"},
            ),
            # ------------------------------------------------------------------
            # 8-12. HeadingBlock (Content Examples section)
            # ------------------------------------------------------------------
            (
                "heading_block",
                {
                    "heading_text": f"{prefix}Content Examples",
                    "size": "h2",
                    "alignment": "left",
                },
            ),
            (
                "heading_block",
                {
                    "heading_text": f"{prefix}H3 Heading — Left Aligned",
                    "size": "h3",
                    "alignment": "left",
                },
            ),
            (
                "heading_block",
                {
                    "heading_text": f"{prefix}H4 Heading — Left Aligned",
                    "size": "h4",
                    "alignment": "left",
                },
            ),
            (
                "heading_block",
                {
                    "heading_text": f"{prefix}H2 Heading — Centre Aligned",
                    "size": "h2",
                    "alignment": "center",
                },
            ),
            (
                "heading_block",
                {
                    "heading_text": f"{prefix}H3 Heading — Centre Aligned",
                    "size": "h3",
                    "alignment": "center",
                },
            ),
            # ------------------------------------------------------------------
            # 13. paragraph_block
            # ------------------------------------------------------------------
            (
                "paragraph_block",
                (
                    f"<p>{prefix}This is a <strong>paragraph block</strong> "
                    "demonstrating rich text. It supports "
                    "<em>italic</em>, <strong>bold</strong>, "
                    "<a href='/en/about/'>internal links</a>, "
                    "ordered and unordered lists, and text "
                    "alignment options.</p>"
                    f"<ul><li>{prefix}List item one</li><li>{prefix}List item two</li>"
                    f"<li>{prefix}List item three</li></ul>"
                ),
            ),
            # ------------------------------------------------------------------
            # 14. lead_paragraph_block
            # ------------------------------------------------------------------
            (
                "lead_paragraph_block",
                {
                    "text": (
                        f"<p>{prefix}This is a <strong>lead paragraph block</strong>. "
                        "It renders in a larger, more prominent style — ideal for "
                        "page introductions or key callouts.</p>"
                    ),
                },
            ),
            # ------------------------------------------------------------------
            # 15-17. CaptionedImageBlock (3 variants)
            # ------------------------------------------------------------------
            (
                "image_block",
                {
                    "image": content_img,
                    "image_scaling": "fit",
                    "caption": f"{prefix}CaptionedImageBlock — Fit scaling, no border",
                    "attribution": "placehold.co",
                    "border_style": "none",
                },
            ),
            (
                "image_block",
                {
                    "image": content_img,
                    "image_scaling": "fill",
                    "caption": (
                        f"{prefix}CaptionedImageBlock — Fill scaling, rounded border"
                    ),
                    "attribution": "placehold.co",
                    "border_style": "rounded",
                },
            ),
            (
                "image_block",
                {
                    "image": square_img,
                    "image_scaling": "fit",
                    "caption": (
                        f"{prefix}CaptionedImageBlock — Fit scaling, circle border"
                    ),
                    "attribution": "placehold.co",
                    "border_style": "circle",
                },
            ),
            # ------------------------------------------------------------------
            # 18-19. ImageGridBlock (2 variants)
            # ------------------------------------------------------------------
            (
                "image_grid_block",
                {
                    "columns": "2",
                    "border_style": "none",
                    "image_alignment": "center",
                    "image_vertical_alignment": "center",
                    "text_alignment": "center",
                    "items": [
                        {
                            "image": grid_img,
                            "image_scaling": "fit",
                            "title": f"{prefix}Grid Item One",
                            "subtitle": f"{prefix}2-column grid",
                            "description": "",
                            "link_page": None,
                            "link_url": "",
                        },
                        {
                            "image": grid_img,
                            "image_scaling": "fit",
                            "title": f"{prefix}Grid Item Two",
                            "subtitle": f"{prefix}2-column grid",
                            "description": "",
                            "link_page": None,
                            "link_url": "",
                        },
                    ],
                },
            ),
            (
                "image_grid_block",
                {
                    "columns": "4",
                    "border_style": "rounded",
                    "image_alignment": "center",
                    "image_vertical_alignment": "center",
                    "text_alignment": "center",
                    "items": [
                        {
                            "image": grid_img,
                            "image_scaling": "fill",
                            "title": f"{prefix}Item {i}",
                            "subtitle": f"{prefix}4-column grid",
                            "description": "",
                            "link_page": None,
                            "link_url": "",
                        }
                        for i in range(1, 5)
                    ],
                },
            ),
            # ------------------------------------------------------------------
            # 20-21. ImageCarouselBlock (2 transition variants)
            # ------------------------------------------------------------------
            (
                "image_carousel_block",
                {
                    "slides": [
                        {
                            "image": content_img,
                            "caption": f"{prefix}Slide {i} — slide transition",
                            "attribution": "placehold.co",
                        }
                        for i in range(1, 4)
                    ],
                    "show_indicators": True,
                    "show_controls": True,
                    "transition_type": "slide",
                    "auto_advance": True,
                    "interval": 5000,
                    "border_style": "none",
                },
            ),
            (
                "image_carousel_block",
                {
                    "slides": [
                        {
                            "image": content_img,
                            "caption": f"{prefix}Slide {i} — fade transition",
                            "attribution": "placehold.co",
                        }
                        for i in range(1, 3)
                    ],
                    "show_indicators": True,
                    "show_controls": True,
                    "transition_type": "fade",
                    "auto_advance": True,
                    "interval": 4000,
                    "border_style": "rounded",
                },
            ),
            # ------------------------------------------------------------------
            # 22. HorizontalRuleBlock
            # ------------------------------------------------------------------
            ("horizontal_rule_block", {}),
            # ------------------------------------------------------------------
            # 23. embed_block
            # ------------------------------------------------------------------
            ("embed_block", "https://www.youtube.com/watch?v=ScMzIvxBSi4"),
            # ------------------------------------------------------------------
            # 24-25. ColumnsBlock (Content Examples variants)
            # ------------------------------------------------------------------
            (
                "columns_block",
                {
                    "layout": "2-equal",
                    "columns": [
                        [
                            (
                                "heading_block",
                                {
                                    "heading_text": f"{prefix}Column One",
                                    "size": "h3",
                                    "alignment": "left",
                                },
                            ),
                            (
                                "paragraph_block",
                                f"<p>{prefix}Content for the first "
                                "equal-width column inside a "
                                "ColumnsBlock.</p>",
                            ),
                        ],
                        [
                            (
                                "heading_block",
                                {
                                    "heading_text": f"{prefix}Column Two",
                                    "size": "h3",
                                    "alignment": "left",
                                },
                            ),
                            (
                                "paragraph_block",
                                f"<p>{prefix}Content for the second "
                                "equal-width column inside a "
                                "ColumnsBlock.</p>",
                            ),
                        ],
                    ],
                },
            ),
            (
                "columns_block",
                {
                    "layout": "2-thirds-1-third",
                    "columns": [
                        [
                            (
                                "heading_block",
                                {
                                    "heading_text": f"{prefix}Main Content (2/3)",
                                    "size": "h3",
                                    "alignment": "left",
                                },
                            ),
                            (
                                "paragraph_block",
                                f"<p>{prefix}This wide column demonstrates "
                                "the 2/3 portion of a 2-thirds-1-third "
                                "layout.</p>",
                            ),
                        ],
                        [
                            (
                                "heading_block",
                                {
                                    "heading_text": f"{prefix}Sidebar (1/3)",
                                    "size": "h3",
                                    "alignment": "left",
                                },
                            ),
                            (
                                "paragraph_block",
                                f"<p>{prefix}Narrower sidebar column (1/3 width).</p>",
                            ),
                        ],
                    ],
                },
            ),
            # ------------------------------------------------------------------
            # 26. FullWidthSectionBlock (Content Examples variant, no background)
            # ------------------------------------------------------------------
            (
                "full_width_section_block",
                {
                    "heading": f"{prefix}FullWidthSectionBlock",
                    "text": (
                        f"<p>{prefix}This section has no background "
                        "image — items use solid background colours.</p>"
                    ),
                    "background_image": None,
                    "background_image_opacity": "15",
                    "colour_mode": "dark",
                    "item_shape": "circle",
                    "items": [
                        {
                            "text": f"{prefix}Feature One",
                            "link_page": None,
                            "link_url": "",
                            "background_image": None,
                            "background_image_opacity": "15",
                            "background_colour": "#1a6b8a",
                            "colour_mode": "dark",
                        },
                        {
                            "text": f"{prefix}Feature Two",
                            "link_page": None,
                            "link_url": "",
                            "background_image": None,
                            "background_image_opacity": "15",
                            "background_colour": "#8a3a1a",
                            "colour_mode": "dark",
                        },
                    ],
                },
            ),
        ]

        home.body = body
        home.save()
        self.stdout.write("  ✅ Homepage body set.")

    # -------------------------------------------------------------------------
    # Menus
    # -------------------------------------------------------------------------

    def _create_menus(self, site, pages, prefix=""):
        # Main menu
        main_menu, _ = MainMenu.objects.get_or_create(site=site)
        MainMenuItem.objects.filter(menu=main_menu).delete()
        MainMenuItem.objects.create(
            menu=main_menu,
            link_page=pages["about"],
            sort_order=0,
        )
        MainMenuItem.objects.create(
            menu=main_menu,
            link_url="/events/",
            link_text=f"{prefix}Events",
            sort_order=1,
        )
        MainMenuItem.objects.create(
            menu=main_menu,
            link_url="/resources/",
            link_text=f"{prefix}Resources",
            sort_order=2,
        )
        MainMenuItem.objects.create(
            menu=main_menu,
            link_page=pages["members"],
            sort_order=3,
        )
        MainMenuItem.objects.create(
            menu=main_menu,
            link_page=pages["articles_index"],
            sort_order=4,
        )
        self.stdout.write("  ✅ Main menu created.")

        # Footer menu
        flat_menu, _ = FlatMenu.objects.get_or_create(
            site=site,
            handle="footer-1",
            defaults={"title": "Footer Navigation", "heading": ""},
        )
        FlatMenuItem.objects.filter(menu=flat_menu).delete()
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_page=pages["about"],
            sort_order=0,
        )
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_page=pages["team"],
            sort_order=1,
        )
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_page=pages["members"],
            sort_order=2,
        )
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_page=pages["articles_index"],
            sort_order=3,
        )
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_url="/events/",
            link_text=f"{prefix}Events",
            sort_order=4,
        )
        FlatMenuItem.objects.create(
            menu=flat_menu,
            link_url="/resources/",
            link_text=f"{prefix}Resources",
            sort_order=5,
        )
        self.stdout.write("  ✅ Footer menu created.")
