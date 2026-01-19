"""Module for the custom Django create_sample_profile_questions command."""

from django.core import management

from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Custom create_sample_profile_questions command."""

    help = "Create sample profile questions for development."

    def handle(self, *args, **options):
        """Automatically called when the command is called."""

        self.stdout.write(LOG_HEADER.format("🐾 Create sample profile questions"))

        # Create ProfileFieldGroup
        group, _ = ProfileFieldGroup.objects.update_or_create(
            name_translations={
                "en": "Pet questions",
                "mi": "Ngā pātai mō ngā kararehe",
            },
            defaults={
                "description_translations": {
                    "en": "Questions about your pets",
                    "mi": "Ngā pātai mō ō kararehe",
                },
                "order": 0,
                "is_active": True,
            },
        )

        # 1. TEXT - pet_name
        ProfileField.objects.update_or_create(
            field_key="pet_name",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.TEXT,
                "label_translations": {
                    "en": "What is your pet's name?",
                    "mi": "He aha te ingoa o tō kararehe?",
                },
                "help_text_translations": {
                    "en": "The name you call your pet",
                    "mi": "Te ingoa e karanga ana koe ki tō kararehe",
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 0,
            },
        )

        # 2. TEXTAREA - pet_description
        ProfileField.objects.update_or_create(
            field_key="pet_description",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.TEXTAREA,
                "label_translations": {
                    "en": "Tell us about your pet",
                    "mi": "Kōrerotia mai tō kararehe",
                },
                "help_text_translations": {
                    "en": (
                        "Share details about your pet's personality, habits, or "
                        "anything else",
                    ),
                    "mi": "Tohatohatia ngā taipitopito mō te āhua o tō kararehe",
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 1,
            },
        )

        # 3. CHECKBOX - pet_activities
        ProfileField.objects.update_or_create(
            field_key="pet_activities",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.CHECKBOX,
                "label_translations": {
                    "en": "What activities does your pet enjoy?",
                    "mi": "He aha ngā mahi e pai ana ki tō kararehe?",
                },
                "help_text_translations": {
                    "en": "Select all that apply",
                    "mi": "Tīpakohia ngā mea katoa e tika ana",
                },
                "options": {
                    "choices": [
                        {
                            "value": "walks",
                            "label_translations": {
                                "en": "Walks",
                                "mi": "Hikoi",
                            },
                        },
                        {
                            "value": "playing",
                            "label_translations": {
                                "en": "Playing",
                                "mi": "Tākaro",
                            },
                        },
                        {
                            "value": "sleeping",
                            "label_translations": {
                                "en": "Sleeping",
                                "mi": "Moe",
                            },
                        },
                        {
                            "value": "eating",
                            "label_translations": {
                                "en": "Eating",
                                "mi": "Kai",
                            },
                        },
                        {
                            "value": "swimming",
                            "label_translations": {
                                "en": "Swimming",
                                "mi": "Kaukau",
                            },
                        },
                    ],
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 2,
            },
        )

        # 4. RADIO - pet_type
        ProfileField.objects.update_or_create(
            field_key="pet_type",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.RADIO,
                "label_translations": {
                    "en": "What type of pet do you have?",
                    "mi": "He aha te momo kararehe tō?",
                },
                "help_text_translations": {
                    "en": "Select your primary pet type",
                    "mi": "Tīpakohia tō kararehe matua",
                },
                "options": {
                    "choices": [
                        {
                            "value": "dog",
                            "label_translations": {
                                "en": "Dog",
                                "mi": "Kurī",
                            },
                        },
                        {
                            "value": "cat",
                            "label_translations": {
                                "en": "Cat",
                                "mi": "Ngeru",
                            },
                        },
                        {
                            "value": "bird",
                            "label_translations": {
                                "en": "Bird",
                                "mi": "Manu",
                            },
                        },
                        {
                            "value": "fish",
                            "label_translations": {
                                "en": "Fish",
                                "mi": "Ika",
                            },
                        },
                        {
                            "value": "rabbit",
                            "label_translations": {
                                "en": "Rabbit",
                                "mi": "Rāpeti",
                            },
                        },
                        {
                            "value": "other",
                            "label_translations": {
                                "en": "Other",
                                "mi": "Ētahi atu",
                            },
                        },
                    ],
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 3,
            },
        )

        # 5. DATE - pet_birthday
        ProfileField.objects.update_or_create(
            field_key="pet_birthday",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.DATE,
                "label_translations": {
                    "en": "When is your pet's birthday?",
                    "mi": "Āhea te rā whānau o tō kararehe?",
                },
                "help_text_translations": {
                    "en": "Your pet's date of birth",
                    "mi": "Te rā whānau o tō kararehe",
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 4,
            },
        )

        # 6. MONTH - pet_adoption_month
        ProfileField.objects.update_or_create(
            field_key="pet_adoption_month",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.MONTH,
                "label_translations": {
                    "en": "When did you get your pet?",
                    "mi": "Nō āhea i riro mai ai tō kararehe ki a koe?",
                },
                "help_text_translations": {
                    "en": "The month and year you acquired your pet",
                    "mi": "Te marama me te tau i riro mai ai tō kararehe",
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 5,
            },
        )

        # 7. NUMBER - pet_age
        ProfileField.objects.update_or_create(
            field_key="pet_age",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.NUMBER,
                "label_translations": {
                    "en": "How old is your pet?",
                    "mi": "E hia ngā tau o tō kararehe?",
                },
                "help_text_translations": {
                    "en": "Your pet's age in years",
                    "mi": "Te pakeke o tō kararehe i ngā tau",
                },
                "min_value": 0,
                "max_value": 30,
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 6,
            },
        )

        # 8. SELECT - pet_size
        ProfileField.objects.update_or_create(
            field_key="pet_size",
            group=group,
            defaults={
                "field_type": ProfileField.FieldType.SELECT,
                "label_translations": {
                    "en": "What is your pet's size?",
                    "mi": "He aha te rahi o tō kararehe?",
                },
                "help_text_translations": {
                    "en": "Select the size that best describes your pet",
                    "mi": "Tīpakohia te rahi e tino whakaatu ana i tō kararehe",
                },
                "options": {
                    "choices": [
                        {
                            "value": "small",
                            "label_translations": {
                                "en": "Small",
                                "mi": "Iti",
                            },
                        },
                        {
                            "value": "medium",
                            "label_translations": {
                                "en": "Medium",
                                "mi": "Waenganui",
                            },
                        },
                        {
                            "value": "large",
                            "label_translations": {
                                "en": "Large",
                                "mi": "Nui",
                            },
                        },
                        {
                            "value": "extra_large",
                            "label_translations": {
                                "en": "Extra Large",
                                "mi": "Tino nui",
                            },
                        },
                    ],
                },
                "is_active": True,
                "is_required_for_membership": False,
                "is_read_only": False,
                "order": 7,
            },
        )

        self.stdout.write("✅ Sample profile questions created.\n")
