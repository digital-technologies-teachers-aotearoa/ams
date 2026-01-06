from ams.cms.blocks.recent_articles_block import RecentArticlesBlock
from ams.cms.blocks.title_block import TitleBlock

from .columns_block import ColumnsBlock
from .content_stream_blocks import ContentStreamBlocks
from .full_width_section_block import FullWidthSectionBlock


class HomePageBlocks(ContentStreamBlocks):
    """StreamBlock for home page."""

    title_block = TitleBlock()
    columns_block = ColumnsBlock()
    full_width_section_block = FullWidthSectionBlock()
    recent_articles_block = RecentArticlesBlock()


class ContentPageBlocks(ContentStreamBlocks):
    """StreamBlock for content page."""

    columns_block = ColumnsBlock()
    full_width_section_block = FullWidthSectionBlock()
