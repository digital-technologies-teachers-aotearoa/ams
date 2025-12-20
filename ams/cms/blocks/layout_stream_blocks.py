from .columns_block import ColumnsBlock
from .content_stream_blocks import ContentStreamBlocks
from .full_width_section_block import FullWidthSectionBlock


class ContentAndLayoutStreamBlocks(ContentStreamBlocks):
    """StreamBlock for content pages that includes layout blocks like columns."""

    columns_block = ColumnsBlock()
    full_width_section_block = FullWidthSectionBlock()
