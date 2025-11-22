from wagtail.blocks import StaticBlock


class HorizontalRuleBlock(StaticBlock):
    class Meta:
        label = "Horizontal rule"
        icon = "minus"
        template = "cms/blocks/horizontal_rule_block.html"
        help_text = "Inserts a horizontal divider line."
