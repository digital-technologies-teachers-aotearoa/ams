from .columns_block import ColumnsBlock
from .content_stream_blocks import ContentStreamBlocks


class ContentAndLayoutStreamBlocks(ContentStreamBlocks):
    """StreamBlock for content pages that includes layout blocks like columns."""

    columns_block = ColumnsBlock()
