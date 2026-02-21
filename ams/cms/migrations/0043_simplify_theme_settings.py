"""Simplify ThemeSettings: remove dark mode and auto-derivable variant fields.

Renames *_light fields to drop the suffix, removes all dark mode fields and
theme color variant fields (bg_subtle, border_subtle, text_emphasis) which
are now auto-derived from base colors.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0042_alter_articlepage_body_alter_contentpage_body_and_more"),
    ]

    operations = [
        # ==== RENAMES (do first, before removals) ====
        migrations.RenameField(
            model_name="themesettings",
            old_name="body_color_light",
            new_name="body_color",
        ),
        migrations.RenameField(
            model_name="themesettings",
            old_name="body_bg_light",
            new_name="body_bg",
        ),
        migrations.RenameField(
            model_name="themesettings",
            old_name="link_color_light",
            new_name="link_color",
        ),
        migrations.RenameField(
            model_name="themesettings",
            old_name="link_hover_color_light",
            new_name="link_hover_color",
        ),
        # ==== REMOVALS: Dark mode body/secondary/tertiary/emphasis/border/link ====
        migrations.RemoveField(model_name="themesettings", name="body_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="body_bg_dark"),
        migrations.RemoveField(model_name="themesettings", name="secondary_color_light"),
        migrations.RemoveField(model_name="themesettings", name="secondary_bg_light"),
        migrations.RemoveField(model_name="themesettings", name="secondary_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="secondary_bg_dark"),
        migrations.RemoveField(model_name="themesettings", name="tertiary_color_light"),
        migrations.RemoveField(model_name="themesettings", name="tertiary_bg_light"),
        migrations.RemoveField(model_name="themesettings", name="tertiary_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="tertiary_bg_dark"),
        migrations.RemoveField(model_name="themesettings", name="emphasis_color_light"),
        migrations.RemoveField(model_name="themesettings", name="emphasis_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="border_color_light"),
        migrations.RemoveField(model_name="themesettings", name="border_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="link_color_dark"),
        migrations.RemoveField(model_name="themesettings", name="link_hover_color_dark"),
        # ==== REMOVALS: Primary variants ====
        migrations.RemoveField(model_name="themesettings", name="primary_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="primary_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="primary_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="primary_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="primary_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="primary_text_emphasis_dark"),
        # ==== REMOVALS: Success variants ====
        migrations.RemoveField(model_name="themesettings", name="success_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="success_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="success_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="success_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="success_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="success_text_emphasis_dark"),
        # ==== REMOVALS: Danger variants ====
        migrations.RemoveField(model_name="themesettings", name="danger_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="danger_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="danger_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="danger_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="danger_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="danger_text_emphasis_dark"),
        # ==== REMOVALS: Warning variants ====
        migrations.RemoveField(model_name="themesettings", name="warning_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="warning_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="warning_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="warning_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="warning_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="warning_text_emphasis_dark"),
        # ==== REMOVALS: Info variants ====
        migrations.RemoveField(model_name="themesettings", name="info_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="info_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="info_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="info_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="info_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="info_text_emphasis_dark"),
        # ==== REMOVALS: Light color and variants ====
        migrations.RemoveField(model_name="themesettings", name="light_color"),
        migrations.RemoveField(model_name="themesettings", name="light_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="light_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="light_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="light_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="light_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="light_text_emphasis_dark"),
        # ==== REMOVALS: Dark color and variants ====
        migrations.RemoveField(model_name="themesettings", name="dark_color"),
        migrations.RemoveField(model_name="themesettings", name="dark_bg_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="dark_border_subtle_light"),
        migrations.RemoveField(model_name="themesettings", name="dark_text_emphasis_light"),
        migrations.RemoveField(model_name="themesettings", name="dark_bg_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="dark_border_subtle_dark"),
        migrations.RemoveField(model_name="themesettings", name="dark_text_emphasis_dark"),
    ]
