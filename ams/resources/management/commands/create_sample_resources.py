# ruff: noqa: E501

"""Module for the custom Django create_sample_resources command."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management

from ams.entities.models import Entity
from ams.resources import file_types
from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.utils.management.commands._constants import LOG_HEADER

GOOGLE_DOC = "https://docs.google.com/document/d/118YeEQNp9G9_xjxBw3tq5FotOSmnWfJuxi8Mi6V3E0g/edit"
GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lWqt7c0EgHLXVPfq11vifyrQUu54fK-93oUCcdjRPsk/edit"
GOOGLE_SLIDES = "https://docs.google.com/presentation/d/1NpOWO4YSUK1yUn5MexpQI0MqC2hesahbxgq9NKkPEiE/edit"
GOOGLE_DRAWINGS = "https://docs.google.com/drawings/d/1Ew3DSKGRr3rYRLglXDvn_Y2SY9vuPpPJRAH53B7w8ZA/edit"
GOOGLE_DRIVE_FILE = (
    "https://drive.google.com/file/d/1vrLflxSlIqQMnUr_6Wrr2P-5_Hsqgd2R/view"
)
YOUTUBE = "https://www.youtube.com/watch?v=v5yeq5u2RMI"
VIMEO = "https://vimeo.com/58336187"


class Command(management.base.BaseCommand):
    """Required command class for the custom Django create_sample_resources command."""

    help = "Create sample resources data."

    def handle(self, *args, **options):
        """Automatically called when the create_sample_resources command is given."""
        self.stdout.write(LOG_HEADER.format("📚 Create sample resources"))
        users = self._get_users()
        entities = self._get_entities()
        resources = self._create_resources(users, entities)
        self._create_all_components(resources)
        self.stdout.write("✅ Sample resources created.")

    def _get_users(self):
        User = get_user_model()  # noqa: N806
        u1 = User.objects.filter(email=settings.SAMPLE_DATA_USER_EMAIL).first()
        u2 = User.objects.filter(email="user2@example.com").first()
        u3 = User.objects.filter(email="user3@example.com").first()
        return u1, u2, u3

    def _get_entities(self):
        entity_names = [
            "TechCorp NZ",
            "Kiwi Foundation",
            "Pacific Innovations",
            "Southern Cross Media",
            "Green Solutions Ltd",
        ]
        entities = {}
        for name in entity_names:
            entity, _ = Entity.objects.get_or_create(name=name)
            entities[name] = entity
        return entities

    def _create_resources(self, users, entities):
        u1, u2, u3 = users
        tc = entities["TechCorp NZ"]
        kf = entities["Kiwi Foundation"]
        pi = entities["Pacific Innovations"]
        sc = entities["Southern Cross Media"]
        gs = entities["Green Solutions Ltd"]

        resource_data = [
            # --- 1 component each (resources 1-10) ---
            {
                "name": "Introduction to Data Analysis",
                "description": "<p>A beginner-friendly video introduction to data analysis techniques used in association management.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [],
            },
            {
                "name": "Conference Highlights Reel",
                "description": "<p>Video highlights from the annual conference showcasing key moments and speaker presentations.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Annual Report 2024",
                "description": "<p>The association's comprehensive annual report covering financial performance, membership growth, and key initiatives for 2024.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc],
            },
            {
                "name": "Member Survey Results",
                "description": "<p>Compiled results from the annual member satisfaction survey with trend analysis and recommendations.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc],
            },
            {
                "name": "Conference Slides 2024",
                "description": "<p>Presentation slides from the 2024 annual conference plenary sessions.</p>",
                "published": True,
                "author_users": [u2],
                "author_entities": [pi],
            },
            {
                "name": "Organisation Chart",
                "description": "<p>Current organisational structure diagram showing reporting lines and committee relationships.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Member Portal Guide",
                "description": "<p>Step-by-step guide to using the online member portal, covering profile management and resource access.</p>",
                "published": True,
                "author_users": [u1, u2],
                "author_entities": [],
            },
            {
                "name": "Shared Files Repository",
                "description": "<p>Central repository of shared files including templates, forms, and reference documents.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [gs],
            },
            {
                "name": "Policy Document PDF",
                "description": "<p>Official association policy document covering member conduct, governance, and operational procedures.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [],
            },
            {
                "name": "Board Meeting Recording",
                "description": "<p>Audio recording of the most recent board meeting, available to members for review.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc, kf],
            },
            # --- 2 components each (resources 11-20) ---
            {
                "name": "Workshop Materials Pack",
                "description": "<p>Complete materials package for the professional development workshop series, including video and supporting documentation.</p>",
                "published": True,
                "author_users": [u1, u2, u3],
                "author_entities": [],
            },
            {
                "name": "Governance Framework",
                "description": "<p>Comprehensive governance framework documents covering board responsibilities, policies, and procedural guidelines.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Technology Roadmap",
                "description": "<p>Strategic technology roadmap outlining planned digital initiatives and infrastructure improvements for the next three years.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc, kf, pi],
            },
            {
                "name": "Research Summary",
                "description": "<p>Summary of recent industry research findings relevant to association members, with links to full reports.</p>",
                "published": True,
                "author_users": [u2],
                "author_entities": [],
            },
            {
                "name": "Media Kit",
                "description": "<p>Press and media kit containing brand assets, logos, and official imagery for use in publications.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Training Video Series - Module 1",
                "description": "<p>First module of the member training video series covering foundational concepts and onboarding essentials.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc],
            },
            {
                "name": "Financial Overview",
                "description": "<p>Financial overview including budget summaries, expenditure tracking, and quarterly financial reports.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc],
            },
            {
                "name": "Event Archive 2023",
                "description": "<p>Complete archive of 2023 events including recordings, materials, and downloadable assets.</p>",
                "published": True,
                "author_users": [u3],
                "author_entities": [],
            },
            {
                "name": "Podcast Episode - Leadership",
                "description": "<p>Audio podcast exploring leadership challenges in association management, featuring interviews with industry experts.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Innovation Report",
                "description": "<p>Draft report examining innovation trends in the sector with case studies and strategic recommendations.</p>",
                "published": False,
                "author_users": [u1],
                "author_entities": [],
            },
            # --- 3 components each (resources 21-30) ---
            {
                "name": "New Member Onboarding Kit",
                "description": "<p>Complete onboarding resource pack for new members including welcome video, handbook, and portal access guide.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc, kf],
            },
            {
                "name": "Annual Conference Pack 2024",
                "description": "<p>Full resource pack from the 2024 annual conference including slide decks, session schedule, and proceedings document.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc, kf],
            },
            {
                "name": "Strategic Plan 2025-2030",
                "description": "<p>Five-year strategic plan setting out the association's vision, goals, and key performance indicators through 2030.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Diversity & Inclusion Resources",
                "description": "<p>Curated resources supporting diversity and inclusion initiatives, including training video, policy guide, and external links.</p>",
                "published": True,
                "author_users": [u1, u2],
                "author_entities": [tc],
            },
            {
                "name": "Regional Chapter Toolkit",
                "description": "<p>Operational toolkit for regional chapter coordinators covering administration, event planning, and reporting templates.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [pi],
            },
            {
                "name": "Webinar Recordings Playlist",
                "description": "<p>Curated playlist of recorded webinars from the past year covering a range of professional development topics.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Member Benefits Overview",
                "description": "<p>Overview of all membership benefits, including links to partner discounts, training resources, and networking opportunities.</p>",
                "published": False,
                "author_users": [u2],
                "author_entities": [pi],
            },
            {
                "name": "Compliance Checklist",
                "description": "<p>Regulatory compliance checklist for member organisations, with reference spreadsheet and guidance notes.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc],
            },
            {
                "name": "Community Engagement Guide",
                "description": "<p>Guide to effective community engagement strategies, featuring case studies, a tutorial video, and external resources.</p>",
                "published": False,
                "author_users": [u1, u2],
                "author_entities": [],
            },
            {
                "name": "Sponsorship Prospectus",
                "description": "<p>Sponsorship prospectus for the upcoming annual conference, including partnership packages and promotional materials.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [sc],
            },
            # --- 4 components each (resources 31-40) ---
            {
                "name": "Complete Event Handbook",
                "description": "<p>End-to-end handbook for organising association events, covering planning, logistics, budgeting, and post-event review.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc],
            },
            {
                "name": "Software Tools Resource Hub",
                "description": "<p>Curated collection of software tools and platforms recommended for association management, with tutorials and documentation.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc, kf, pi],
            },
            {
                "name": "Leadership Development Program",
                "description": "<p>Structured leadership development program materials including video training, presentation decks, reference guides, and assessment tools.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Member Research Library",
                "description": "<p>Curated research library for members, aggregating reports, data sets, and external resources on key industry topics.</p>",
                "published": True,
                "author_users": [u1, u2, u3],
                "author_entities": [],
            },
            {
                "name": "Digital Archive 2022",
                "description": "<p>Complete digital archive of 2022 association activities, including website snapshots, downloadable archives, and video recordings.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [gs],
            },
            {
                "name": "Communications Templates",
                "description": "<p>Professional communications templates for member newsletters, social media, presentations, and internal reporting.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Environmental Policy Resources",
                "description": "<p>Resources supporting the association's environmental sustainability commitments, including policy documents, training, and guidance.</p>",
                "published": True,
                "author_users": [u2],
                "author_entities": [gs],
            },
            {
                "name": "Professional Development Hub",
                "description": "<p>Central hub for professional development resources including video courses, presentation materials, and external learning platforms.</p>",
                "published": False,
                "author_users": [u3],
                "author_entities": [],
            },
            {
                "name": "Historical Records Collection",
                "description": "<p>Archived collection of historical association records, publications, and documents spanning the organisation's history.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Volunteer Training Materials",
                "description": "<p>Comprehensive training materials for association volunteers covering roles, responsibilities, and practical guidance.</p>",
                "published": True,
                "author_users": [u1, u2],
                "author_entities": [tc],
            },
            # --- 5 components each, including TYPE_RESOURCE cross-links (resources 41-50) ---
            {
                "name": "Master Knowledge Base",
                "description": "<p>Central knowledge base aggregating key association documents, data, videos, and linked resources into a single reference point.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc, kf],
            },
            {
                "name": "Executive Resource Pack",
                "description": "<p>Curated resource pack for board executives and senior leaders, covering strategy, governance, and key reference documents.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [tc, kf],
            },
            {
                "name": "Comprehensive Training Suite",
                "description": "<p>Full training suite combining video content, presentations, and structured learning pathways for member professional development.</p>",
                "published": True,
                "author_users": [u1, u2, u3],
                "author_entities": [],
            },
            {
                "name": "Complete Governance Library",
                "description": "<p>Complete library of governance documents, policies, frameworks, and supporting data for board and committee members.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [kf],
            },
            {
                "name": "Multimedia Learning Centre",
                "description": "<p>Multimedia learning centre bringing together video, audio, and interactive resources for member continuing education.</p>",
                "published": True,
                "author_users": [u2],
                "author_entities": [pi],
            },
            {
                "name": "Research & Analytics Portal",
                "description": "<p>Comprehensive portal for association research and analytics, including data sets, reports, and reference documentation.</p>",
                "published": True,
                "author_users": [u1],
                "author_entities": [tc],
            },
            {
                "name": "Events Resource Centre",
                "description": "<p>Full resource centre for event management, combining presentation templates, video guides, web resources, and downloadable assets.</p>",
                "published": True,
                "author_users": [],
                "author_entities": [sc],
            },
            {
                "name": "Innovation & Technology Hub",
                "description": "<p>Hub for innovation and technology resources, bringing together web tools, tutorials, documentation, and strategic references.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [tc, kf, pi],
            },
            {
                "name": "Community Resources Portal",
                "description": "<p>Open community portal aggregating web guides, documentation, tutorial videos, and reference materials for broader community use.</p>",
                "published": False,
                "author_users": [],
                "author_entities": [],
            },
            {
                "name": "Full Library Index",
                "description": "<p>Master index of all association resources, combining data exports, reference documents, video content, and downloadable archives.</p>",
                "published": True,
                "author_users": [u1, u2],
                "author_entities": [tc],
            },
        ]

        resources = {}
        for item in resource_data:
            resource, _ = Resource.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "published": item["published"],
                },
            )
            resource.author_users.set([u for u in item["author_users"] if u])
            resource.author_entities.set(item["author_entities"])
            resources[item["name"]] = resource

        self.stdout.write(f"✅ Created/updated {len(resources)} resources.")
        return resources

    def _add_component(
        self,
        resource,
        name,
        *,
        url=None,
        linked_resource=None,
        override_type=None,
    ):
        defaults = {}
        if url:
            defaults["component_url"] = url
        if linked_resource:
            defaults["component_resource"] = linked_resource
        component, _ = ResourceComponent.objects.update_or_create(
            resource=resource,
            name=name,
            defaults=defaults,
        )
        if override_type is not None:
            ResourceComponent.objects.filter(pk=component.pk).update(
                component_type=override_type,
            )

    def _create_all_components(self, resources):  # noqa: PLR0915
        r = resources

        def add(resource_name, comp_name, **kwargs):
            self._add_component(r[resource_name], comp_name, **kwargs)

        # --- Resources 1-10: 1 component each ---

        add(
            "Introduction to Data Analysis",
            "Watch: Data Analysis Overview",
            url=YOUTUBE,
        )
        add("Conference Highlights Reel", "Watch: Conference Highlights", url=VIMEO)
        add("Annual Report 2024", "Read: Annual Report 2024", url=GOOGLE_DOC)
        add("Member Survey Results", "View: Survey Data", url=GOOGLE_SHEET)
        add("Conference Slides 2024", "View: Conference Slides", url=GOOGLE_SLIDES)
        add("Organisation Chart", "View: Organisation Chart", url=GOOGLE_DRAWINGS)
        add(
            "Member Portal Guide",
            "Visit: Member Portal",
            url="https://example.com/member-portal",
        )
        add("Shared Files Repository", "Open: Shared Files", url=GOOGLE_DRIVE_FILE)
        add(
            "Policy Document PDF",
            "Download: Policy Document",
            url="https://example.com/association-policy.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Board Meeting Recording",
            "Listen: Board Meeting Audio",
            url="https://example.com/board-meeting-2024.mp3",
            override_type=file_types.TYPE_AUDIO,
        )

        # --- Resources 11-20: 2 components each ---

        add("Workshop Materials Pack", "Watch: Workshop Introduction", url=YOUTUBE)
        add("Workshop Materials Pack", "Read: Workshop Handbook", url=GOOGLE_DOC)

        add("Governance Framework", "Read: Governance Policy", url=GOOGLE_DOC)
        add("Governance Framework", "View: Governance Presentation", url=GOOGLE_SLIDES)

        add("Technology Roadmap", "View: Roadmap Presentation", url=GOOGLE_SLIDES)
        add("Technology Roadmap", "View: Roadmap Data", url=GOOGLE_SHEET)

        add("Research Summary", "Read: Research Summary Document", url=GOOGLE_DOC)
        add(
            "Research Summary",
            "Visit: Research Portal",
            url="https://example.com/research-portal",
        )

        add("Media Kit", "View: Brand Assets", url=GOOGLE_DRAWINGS)
        add("Media Kit", "Open: Full Media Kit", url=GOOGLE_DRIVE_FILE)

        add("Training Video Series - Module 1", "Watch: Module 1 Part A", url=YOUTUBE)
        add("Training Video Series - Module 1", "Watch: Module 1 Part B", url=VIMEO)

        add("Financial Overview", "View: Budget Tracker", url=GOOGLE_SHEET)
        add(
            "Financial Overview",
            "Download: Financial Report",
            url="https://example.com/financial-report-2024.pdf",
            override_type=file_types.TYPE_PDF,
        )

        add(
            "Event Archive 2023",
            "Visit: 2023 Event Archive",
            url="https://example.com/events/2023",
        )
        add(
            "Event Archive 2023",
            "Download: Event Assets Pack",
            url="https://example.com/event-assets-2023.zip",
            override_type=file_types.TYPE_ARCHIVE,
        )

        add(
            "Podcast Episode - Leadership",
            "Listen: Leadership Podcast",
            url="https://example.com/podcast/leadership-ep1.mp3",
            override_type=file_types.TYPE_AUDIO,
        )
        add(
            "Podcast Episode - Leadership",
            "Visit: Podcast Website",
            url="https://example.com/podcast",
        )

        add("Innovation Report", "Read: Draft Report", url=GOOGLE_DOC)
        add(
            "Innovation Report",
            "Download: Report PDF",
            url="https://example.com/innovation-report-draft.pdf",
            override_type=file_types.TYPE_PDF,
        )

        # --- Resources 21-30: 3 components each ---

        add("New Member Onboarding Kit", "Watch: Welcome Video", url=YOUTUBE)
        add("New Member Onboarding Kit", "Read: Member Handbook", url=GOOGLE_DOC)
        add(
            "New Member Onboarding Kit",
            "Visit: Member Portal",
            url="https://example.com/new-member-portal",
        )

        add("Annual Conference Pack 2024", "View: Conference Slides", url=GOOGLE_SLIDES)
        add("Annual Conference Pack 2024", "View: Session Schedule", url=GOOGLE_SHEET)
        add(
            "Annual Conference Pack 2024",
            "Download: Conference Proceedings",
            url="https://example.com/conference-proceedings-2024.pdf",
            override_type=file_types.TYPE_PDF,
        )

        add("Strategic Plan 2025-2030", "Read: Strategic Plan Document", url=GOOGLE_DOC)
        add(
            "Strategic Plan 2025-2030",
            "View: Strategy Presentation",
            url=GOOGLE_SLIDES,
        )
        add(
            "Strategic Plan 2025-2030",
            "Download: Strategic Plan PDF",
            url="https://example.com/strategic-plan-2025-2030.pdf",
            override_type=file_types.TYPE_PDF,
        )

        add("Diversity & Inclusion Resources", "Watch: D&I Training Video", url=YOUTUBE)
        add("Diversity & Inclusion Resources", "Read: D&I Policy Guide", url=GOOGLE_DOC)
        add(
            "Diversity & Inclusion Resources",
            "Visit: D&I External Resources",
            url="https://example.com/diversity-inclusion",
        )

        add(
            "Regional Chapter Toolkit",
            "Read: Chapter Operations Guide",
            url=GOOGLE_DOC,
        )
        add("Regional Chapter Toolkit", "View: Reporting Templates", url=GOOGLE_SHEET)
        add(
            "Regional Chapter Toolkit",
            "View: Chapter Branding Assets",
            url=GOOGLE_DRAWINGS,
        )

        add(
            "Webinar Recordings Playlist",
            "Watch: Webinar - Digital Strategy",
            url=YOUTUBE,
        )
        add(
            "Webinar Recordings Playlist",
            "Watch: Webinar - Member Engagement",
            url=VIMEO,
        )
        add(
            "Webinar Recordings Playlist",
            "Visit: Webinar Platform",
            url="https://example.com/webinars",
        )

        add(
            "Member Benefits Overview",
            "View: Benefits Presentation",
            url=GOOGLE_SLIDES,
        )
        add(
            "Member Benefits Overview",
            "Visit: Partner Discounts Portal",
            url="https://example.com/member-discounts",
        )
        add("Member Benefits Overview", "Watch: Benefits Overview Video", url=VIMEO)

        add("Compliance Checklist", "View: Compliance Tracker", url=GOOGLE_SHEET)
        add(
            "Compliance Checklist",
            "Download: Compliance Checklist PDF",
            url="https://example.com/compliance-checklist.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Compliance Checklist",
            "Visit: Regulatory Guidance",
            url="https://example.com/regulatory-guidance",
        )

        add("Community Engagement Guide", "Read: Engagement Strategies", url=GOOGLE_DOC)
        add(
            "Community Engagement Guide",
            "Watch: Community Engagement Case Study",
            url=YOUTUBE,
        )
        add(
            "Community Engagement Guide",
            "Visit: Engagement Resources",
            url="https://example.com/community-engagement",
        )

        add(
            "Sponsorship Prospectus",
            "View: Sponsorship Presentation",
            url=GOOGLE_SLIDES,
        )
        add(
            "Sponsorship Prospectus",
            "Download: Sponsorship Prospectus PDF",
            url="https://example.com/sponsorship-prospectus.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add("Sponsorship Prospectus", "Open: Sponsorship Assets", url=GOOGLE_DRIVE_FILE)

        # --- Resources 31-40: 4 components each ---

        add("Complete Event Handbook", "Read: Event Planning Guide", url=GOOGLE_DOC)
        add("Complete Event Handbook", "View: Budget Template", url=GOOGLE_SHEET)
        add("Complete Event Handbook", "Watch: Event Setup Tutorial", url=YOUTUBE)
        add(
            "Complete Event Handbook",
            "Visit: Event Management Platform",
            url="https://example.com/event-management",
        )

        add(
            "Software Tools Resource Hub",
            "Visit: Tools Directory",
            url="https://example.com/software-tools",
        )
        add(
            "Software Tools Resource Hub",
            "Read: Tools Comparison Guide",
            url=GOOGLE_DOC,
        )
        add("Software Tools Resource Hub", "Watch: Platform Walkthrough", url=VIMEO)
        add(
            "Software Tools Resource Hub",
            "View: Implementation Roadmap",
            url=GOOGLE_SLIDES,
        )

        add(
            "Leadership Development Program",
            "Watch: Leadership Foundations",
            url=YOUTUBE,
        )
        add("Leadership Development Program", "View: Program Slides", url=GOOGLE_SLIDES)
        add(
            "Leadership Development Program",
            "Read: Leadership Handbook",
            url=GOOGLE_DOC,
        )
        add(
            "Leadership Development Program",
            "Download: Program Assessment",
            url="https://example.com/leadership-assessment.pdf",
            override_type=file_types.TYPE_PDF,
        )

        add("Member Research Library", "Read: Research Index", url=GOOGLE_DOC)
        add(
            "Member Research Library",
            "Download: Industry Report 2024",
            url="https://example.com/industry-report-2024.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Member Research Library",
            "Visit: External Research Portal",
            url="https://example.com/research-library",
        )
        add("Member Research Library", "View: Data Summary", url=GOOGLE_SHEET)

        add(
            "Digital Archive 2022",
            "Visit: 2022 Archive Website",
            url="https://example.com/archive/2022",
        )
        add("Digital Archive 2022", "Open: Archive Files", url=GOOGLE_DRIVE_FILE)
        add(
            "Digital Archive 2022",
            "Download: Full Archive",
            url="https://example.com/archive-2022-full.zip",
            override_type=file_types.TYPE_ARCHIVE,
        )
        add("Digital Archive 2022", "Watch: 2022 Year in Review", url=VIMEO)

        add(
            "Communications Templates",
            "View: Presentation Templates",
            url=GOOGLE_SLIDES,
        )
        add("Communications Templates", "Read: Copywriting Guide", url=GOOGLE_DOC)
        add(
            "Communications Templates",
            "View: Visual Brand Assets",
            url=GOOGLE_DRAWINGS,
        )
        add("Communications Templates", "View: Content Calendar", url=GOOGLE_SHEET)

        add(
            "Environmental Policy Resources",
            "Read: Environmental Policy",
            url=GOOGLE_DOC,
        )
        add(
            "Environmental Policy Resources",
            "Watch: Sustainability Training",
            url=YOUTUBE,
        )
        add(
            "Environmental Policy Resources",
            "Download: Sustainability Report",
            url="https://example.com/sustainability-report.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Environmental Policy Resources",
            "Visit: Environmental Resources",
            url="https://example.com/environmental-resources",
        )

        add("Professional Development Hub", "Watch: PD Course - Module 1", url=YOUTUBE)
        add("Professional Development Hub", "Watch: PD Course - Module 2", url=VIMEO)
        add("Professional Development Hub", "View: Course Slides", url=GOOGLE_SLIDES)
        add(
            "Professional Development Hub",
            "Visit: Learning Platform",
            url="https://example.com/learning-platform",
        )

        add(
            "Historical Records Collection",
            "Open: Scanned Records Archive",
            url=GOOGLE_DRIVE_FILE,
        )
        add(
            "Historical Records Collection",
            "Download: Historical Documents",
            url="https://example.com/historical-documents.zip",
            override_type=file_types.TYPE_ARCHIVE,
        )
        add(
            "Historical Records Collection",
            "Visit: History Portal",
            url="https://example.com/association-history",
        )
        add(
            "Historical Records Collection",
            "Download: Historical Report",
            url="https://example.com/historical-report.pdf",
            override_type=file_types.TYPE_PDF,
        )

        add(
            "Volunteer Training Materials",
            "Watch: Volunteer Orientation Video",
            url=YOUTUBE,
        )
        add("Volunteer Training Materials", "Read: Volunteer Handbook", url=GOOGLE_DOC)
        add(
            "Volunteer Training Materials",
            "View: Training Presentation",
            url=GOOGLE_SLIDES,
        )
        add(
            "Volunteer Training Materials",
            "Download: Volunteer Guide PDF",
            url="https://example.com/volunteer-guide.pdf",
            override_type=file_types.TYPE_PDF,
        )

        # --- Resources 41-50: 5 components each, including TYPE_RESOURCE cross-links ---

        add("Master Knowledge Base", "Read: KB Index Document", url=GOOGLE_DOC)
        add("Master Knowledge Base", "View: Data Overview", url=GOOGLE_SHEET)
        add("Master Knowledge Base", "Watch: KB Introduction Video", url=YOUTUBE)
        add(
            "Master Knowledge Base",
            "Visit: Knowledge Base Portal",
            url="https://example.com/knowledge-base",
        )
        add(
            "Master Knowledge Base",
            "Reference: Annual Report",
            linked_resource=r["Annual Report 2024"],
        )

        add("Executive Resource Pack", "Read: Executive Briefing", url=GOOGLE_DOC)
        add("Executive Resource Pack", "View: Executive Slides", url=GOOGLE_SLIDES)
        add(
            "Executive Resource Pack",
            "Download: Executive Summary PDF",
            url="https://example.com/executive-summary.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add("Executive Resource Pack", "Watch: Executive Briefing Video", url=VIMEO)
        add(
            "Executive Resource Pack",
            "Reference: Strategic Plan",
            linked_resource=r["Strategic Plan 2025-2030"],
        )

        add(
            "Comprehensive Training Suite",
            "Watch: Training Series Part 1",
            url=YOUTUBE,
        )
        add("Comprehensive Training Suite", "Watch: Training Series Part 2", url=VIMEO)
        add(
            "Comprehensive Training Suite",
            "View: Training Slide Deck",
            url=GOOGLE_SLIDES,
        )
        add("Comprehensive Training Suite", "Read: Training Guide", url=GOOGLE_DOC)
        add(
            "Comprehensive Training Suite",
            "Reference: Onboarding Kit",
            linked_resource=r["New Member Onboarding Kit"],
        )

        add("Complete Governance Library", "Read: Governance Overview", url=GOOGLE_DOC)
        add(
            "Complete Governance Library",
            "Download: Governance Policies PDF",
            url="https://example.com/governance-policies.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add("Complete Governance Library", "View: Governance Data", url=GOOGLE_SHEET)
        add(
            "Complete Governance Library",
            "View: Board Presentations",
            url=GOOGLE_SLIDES,
        )
        add(
            "Complete Governance Library",
            "Reference: Governance Framework",
            linked_resource=r["Governance Framework"],
        )

        add(
            "Multimedia Learning Centre",
            "Watch: Learning Centre Introduction",
            url=YOUTUBE,
        )
        add("Multimedia Learning Centre", "Watch: Featured Lecture", url=VIMEO)
        add(
            "Multimedia Learning Centre",
            "Listen: Expert Interview Podcast",
            url="https://example.com/podcast/expert-interview.mp3",
            override_type=file_types.TYPE_AUDIO,
        )
        add(
            "Multimedia Learning Centre",
            "Visit: Learning Centre Platform",
            url="https://example.com/learning-centre",
        )
        add(
            "Multimedia Learning Centre",
            "Reference: Training Module 1",
            linked_resource=r["Training Video Series - Module 1"],
        )

        add(
            "Research & Analytics Portal",
            "View: Analytics Dashboard",
            url=GOOGLE_SHEET,
        )
        add("Research & Analytics Portal", "Read: Research Methodology", url=GOOGLE_DOC)
        add(
            "Research & Analytics Portal",
            "Download: Analytics Report PDF",
            url="https://example.com/analytics-report.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Research & Analytics Portal",
            "Visit: Analytics Platform",
            url="https://example.com/analytics",
        )
        add(
            "Research & Analytics Portal",
            "Reference: Member Survey Results",
            linked_resource=r["Member Survey Results"],
        )

        add("Events Resource Centre", "View: Event Templates", url=GOOGLE_SLIDES)
        add("Events Resource Centre", "Watch: Event Planning Tutorial", url=YOUTUBE)
        add(
            "Events Resource Centre",
            "Visit: Events Platform",
            url="https://example.com/events-platform",
        )
        add(
            "Events Resource Centre",
            "Download: Event Assets Pack",
            url="https://example.com/event-assets.zip",
            override_type=file_types.TYPE_ARCHIVE,
        )
        add(
            "Events Resource Centre",
            "Reference: Event Handbook",
            linked_resource=r["Complete Event Handbook"],
        )

        add(
            "Innovation & Technology Hub",
            "Visit: Tech Resources Portal",
            url="https://example.com/tech-resources",
        )
        add("Innovation & Technology Hub", "Watch: Innovation Showcase", url=YOUTUBE)
        add("Innovation & Technology Hub", "Read: Technology Guide", url=GOOGLE_DOC)
        add("Innovation & Technology Hub", "Watch: Tech Demo Video", url=VIMEO)
        add(
            "Innovation & Technology Hub",
            "Reference: Technology Roadmap",
            linked_resource=r["Technology Roadmap"],
        )

        add(
            "Community Resources Portal",
            "Visit: Community Hub",
            url="https://example.com/community-hub",
        )
        add("Community Resources Portal", "Read: Community Guide", url=GOOGLE_DOC)
        add("Community Resources Portal", "Watch: Community Introduction", url=YOUTUBE)
        add(
            "Community Resources Portal",
            "Download: Community Resources PDF",
            url="https://example.com/community-resources.pdf",
            override_type=file_types.TYPE_PDF,
        )
        add(
            "Community Resources Portal",
            "Reference: Engagement Guide",
            linked_resource=r["Community Engagement Guide"],
        )

        add("Full Library Index", "View: Library Index Spreadsheet", url=GOOGLE_SHEET)
        add("Full Library Index", "Read: Library Catalogue", url=GOOGLE_DOC)
        add("Full Library Index", "Watch: Library Overview Video", url=VIMEO)
        add(
            "Full Library Index",
            "Download: Full Archive",
            url="https://example.com/full-library-archive.zip",
            override_type=file_types.TYPE_ARCHIVE,
        )
        add(
            "Full Library Index",
            "Reference: Digital Archive 2022",
            linked_resource=r["Digital Archive 2022"],
        )

        count = ResourceComponent.objects.filter(resource__in=r.values()).count()
        self.stdout.write(f"✅ Created/updated {count} resource components.")
