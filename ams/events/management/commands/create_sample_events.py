# ruff: noqa: E501

"""Module for the custom Django create_sample_events command."""

from datetime import timedelta
from decimal import Decimal

from django.core import management
from django.utils.timezone import now
from moneyed import Money

from ams.entities.models import Entity
from ams.events.models import Event
from ams.events.models import Location
from ams.events.models import Region
from ams.events.models import Series
from ams.events.models import Session
from ams.utils.management.commands._constants import LOG_HEADER

TODAY = now().replace(hour=0, minute=0, second=0, microsecond=0)


def _dt(days_offset, hour=9, minute=0):
    """Return a datetime offset from today at the given time."""
    return TODAY + timedelta(days=days_offset, hours=hour, minutes=minute)


class Command(management.base.BaseCommand):
    """Required command class for the custom Django create_sample_events command."""

    help = "Create sample events data."

    def handle(self, *args, **options):
        """Automatically called when the create_sample_events command is given."""
        self.stdout.write(LOG_HEADER.format("📅 Create sample events"))

        regions = self._create_regions()
        locations = self._create_locations(regions)
        series = self._create_series()
        entities = self._create_entities()

        self._create_events(regions, locations, series, entities)
        self.stdout.write("✅ Sample events created.")

    def _create_regions(self):
        regions = {}
        region_names = [
            "Auckland",
            "Wellington",
            "Canterbury",
            "Otago",
            "Bay of Plenty",
        ]
        for i, name in enumerate(region_names, start=1):
            regions[name], _ = Region.objects.get_or_create(
                name=name,
                defaults={"order": i},
            )
        self.stdout.write(f"✅ Created {len(regions)} regions.")
        return regions

    def _create_locations(self, regions):
        location_data = [
            {
                "name": "Auckland Convention Centre",
                "room": "Main Hall",
                "street_address": "50 Mayoral Drive",
                "city": "Auckland",
                "region": regions["Auckland"],
                "latitude": Decimal("-36.852095"),
                "longitude": Decimal("174.763745"),
            },
            {
                "name": "Auckland Convention Centre",
                "room": "Room A",
                "street_address": "50 Mayoral Drive",
                "city": "Auckland",
                "region": regions["Auckland"],
                "latitude": Decimal("-36.852095"),
                "longitude": Decimal("174.763745"),
            },
            {
                "name": "Auckland Convention Centre",
                "room": "Room B",
                "street_address": "50 Mayoral Drive",
                "city": "Auckland",
                "region": regions["Auckland"],
                "latitude": Decimal("-36.852095"),
                "longitude": Decimal("174.763745"),
            },
            {
                "name": "Te Papa Museum",
                "street_address": "55 Cable Street",
                "city": "Wellington",
                "region": regions["Wellington"],
                "latitude": Decimal("-41.290440"),
                "longitude": Decimal("174.781860"),
            },
            {
                "name": "Christchurch Town Hall",
                "street_address": "86 Kilmore Street",
                "city": "Christchurch",
                "region": regions["Canterbury"],
                "latitude": Decimal("-43.527620"),
                "longitude": Decimal("172.636440"),
            },
            {
                "name": "Dunedin Centre",
                "street_address": "1 Harrop Street",
                "city": "Dunedin",
                "region": regions["Otago"],
                "latitude": Decimal("-45.874160"),
                "longitude": Decimal("170.503580"),
            },
            {
                "name": "Tauranga Community Hub",
                "street_address": "21 Devonport Road",
                "city": "Tauranga",
                "region": regions["Bay of Plenty"],
                "latitude": Decimal("-37.687000"),
                "longitude": Decimal("176.167000"),
            },
            {
                "name": "Wanaka Lakeside Retreat",
                "street_address": "10 Lakeside Road",
                "suburb": "Wanaka",
                "city": "Queenstown-Lakes",
                "region": regions["Otago"],
                "latitude": Decimal("-44.693000"),
                "longitude": Decimal("169.132000"),
            },
        ]

        locations = []
        for data in location_data:
            loc, _ = Location.objects.get_or_create(
                name=data["name"],
                room=data.get("room", ""),
                defaults=data,
            )
            locations.append(loc)
        self.stdout.write(f"✅ Created {len(locations)} locations.")
        return locations

    def _create_series(self):
        series_data = [
            ("Annual Conference", "AC", "The flagship annual conference event."),
            (
                "Regional Workshop",
                "RW",
                "Hands-on workshops hosted in different regions.",
            ),
            ("Webinar Series", "WS", "Online webinars on current topics."),
        ]
        series = {}
        for name, abbr, desc in series_data:
            series[abbr], _ = Series.objects.get_or_create(
                abbreviation=abbr,
                defaults={"name": name, "description": desc},
            )
        self.stdout.write(f"✅ Created {len(series)} series.")
        return series

    def _create_entities(self):
        entity_names = [
            "TechCorp NZ",
            "Kiwi Foundation",
            "Pacific Innovations",
            "Southern Cross Media",
            "Green Solutions Ltd",
        ]
        entities = []
        for name in entity_names:
            entity, _ = Entity.objects.get_or_create(name=name)
            entities.append(entity)
        self.stdout.write(f"✅ Created {len(entities)} entities.")
        return entities

    def _add_sessions(self, event, session_defs, session_locations=None):
        """Create sessions for an event.

        session_defs: list of (name, start_dt, end_dt) tuples
        session_locations: optional dict mapping session index to list of locations
        """
        for i, (name, start, end) in enumerate(session_defs):
            session, _ = Session.objects.update_or_create(
                name=name,
                event=event,
                start=start,
                defaults={"end": end},
            )
            if session_locations and i in session_locations:
                session.locations.set(session_locations[i])
        event.update_datetimes()

    def _create_events(self, regions, locations, series, entities):  # noqa: PLR0915
        akl_main, akl_a, akl_b, te_papa, chch, dunedin, tauranga, wanaka = locations
        reg_link = "https://example.com/register"

        # --- 1. Past large conference (AC series) ---
        e1, _ = Event.objects.update_or_create(
            name="Conference 2025",
            defaults={
                "description": "<p>The 2025 annual conference reviewing the past year.</p>",
                "published": True,
                "show_schedule": True,
                "featured": False,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(350, "NZD"),
                "series": series["AC"],
            },
        )
        e1.locations.set([akl_main])
        e1.sponsors.set([entities[0], entities[1]])
        e1.organisers.set([entities[2]])
        base = _dt(-90)
        self._add_sessions(
            e1,
            [
                # Day 1
                ("Opening Keynote", base.replace(hour=9), base.replace(hour=10)),
                (
                    "Track A: Data Analytics",
                    base.replace(hour=10, minute=30),
                    base.replace(hour=12),
                ),
                (
                    "Track B: Leadership Forum",
                    base.replace(hour=10, minute=30),
                    base.replace(hour=12),
                ),
                ("Lunch & Networking", base.replace(hour=12), base.replace(hour=13)),
                (
                    "Track A: Cloud Infrastructure",
                    base.replace(hour=13),
                    base.replace(hour=14, minute=30),
                ),
                (
                    "Track B: People & Culture",
                    base.replace(hour=13),
                    base.replace(hour=14, minute=30),
                ),
                ("Day 1 Wrap-up", base.replace(hour=15), base.replace(hour=16)),
                # Day 2
                ("Morning Workshop: AI Fundamentals", _dt(-89, 9), _dt(-89, 12)),
                ("Afternoon Panel: Industry Trends", _dt(-89, 13), _dt(-89, 15)),
                ("Networking Mixer", _dt(-89, 16), _dt(-89, 18)),
                # Day 3
                ("Unconference Sessions", _dt(-88, 9), _dt(-88, 12)),
                ("Closing Keynote", _dt(-88, 13), _dt(-88, 14, 30)),
                ("Awards Ceremony", _dt(-88, 15), _dt(-88, 16, 30)),
            ],
            {
                1: [akl_a],
                2: [akl_b],
                4: [akl_a],
                5: [akl_b],
                0: [akl_main],
                6: [akl_main],
            },
        )
        self.stdout.write("✅ Event 1: Conference 2025 (past, multi-day)")

        # --- 2. Future large conference (AC series) ---
        e2, _ = Event.objects.update_or_create(
            name="Conference 2026",
            defaults={
                "description": "<p>The upcoming 2026 annual conference.</p>",
                "published": True,
                "show_schedule": True,
                "featured": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(400, "NZD"),
                "series": series["AC"],
            },
        )
        e2.locations.set([akl_main])
        e2.sponsors.set(entities[:3])
        e2.organisers.set([entities[3]])
        base = _dt(120)
        self._add_sessions(
            e2,
            [
                # Day 1
                ("Welcome & Opening", base.replace(hour=9), base.replace(hour=10)),
                (
                    "Track A: Machine Learning",
                    base.replace(hour=10, minute=30),
                    base.replace(hour=12),
                ),
                (
                    "Track B: Strategy & Growth",
                    base.replace(hour=10, minute=30),
                    base.replace(hour=12),
                ),
                ("Lunch", base.replace(hour=12), base.replace(hour=13)),
                (
                    "Track A: Security Best Practices",
                    base.replace(hour=13, minute=30),
                    base.replace(hour=15),
                ),
                (
                    "Track B: Wellbeing at Work",
                    base.replace(hour=13, minute=30),
                    base.replace(hour=15),
                ),
                ("Evening Social", base.replace(hour=17), base.replace(hour=20)),
                # Day 2
                ("Keynote: Future of Tech", _dt(121, 9), _dt(121, 10, 30)),
                ("Track A: DevOps Deep Dive", _dt(121, 11), _dt(121, 12, 30)),
                ("Track B: Change Management", _dt(121, 11), _dt(121, 12, 30)),
                ("Lunch & Exhibits", _dt(121, 12, 30), _dt(121, 13, 30)),
                ("Workshop: Hands-on Kubernetes", _dt(121, 14), _dt(121, 16)),
                ("Panel: Diversity in Tech", _dt(121, 14), _dt(121, 15, 30)),
                # Day 3
                ("Hackathon Morning", _dt(122, 9), _dt(122, 12)),
                ("Hackathon Presentations", _dt(122, 13), _dt(122, 15)),
                ("Closing & Awards", _dt(122, 15, 30), _dt(122, 17)),
            ],
            {
                1: [akl_a],
                2: [akl_b],
                4: [akl_a],
                5: [akl_b],
                8: [akl_a],
                9: [akl_b],
                12: [akl_b],
                0: [akl_main],
            },
        )
        self.stdout.write("✅ Event 2: Conference 2026 (future, multi-day)")

        # --- 3-5. Regional workshops (RW series) ---
        e3, _ = Event.objects.update_or_create(
            name="Wellington Workshop: Project Management",
            defaults={
                "description": "<p>A hands-on workshop covering modern project management techniques.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(120, "NZD"),
                "series": series["RW"],
            },
        )
        e3.locations.set([te_papa])
        base = _dt(30)
        self._add_sessions(
            e3,
            [
                (
                    "Introduction & Icebreaker",
                    base.replace(hour=9),
                    base.replace(hour=9, minute=45),
                ),
                (
                    "Agile Methodologies",
                    base.replace(hour=10),
                    base.replace(hour=11, minute=30),
                ),
                (
                    "Lunch Break",
                    base.replace(hour=11, minute=30),
                    base.replace(hour=12, minute=30),
                ),
                (
                    "Risk Management",
                    base.replace(hour=12, minute=30),
                    base.replace(hour=14),
                ),
                ("Q&A and Wrap-up", base.replace(hour=14), base.replace(hour=15)),
            ],
        )
        self.stdout.write("✅ Event 3: Wellington Workshop (future)")

        e4, _ = Event.objects.update_or_create(
            name="Canterbury Workshop: Data Governance",
            defaults={
                "description": "<p>Understanding data governance frameworks and best practices.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(100, "NZD"),
                "series": series["RW"],
            },
        )
        e4.locations.set([chch])
        base = _dt(60)
        self._add_sessions(
            e4,
            [
                ("Welcome", base.replace(hour=9), base.replace(hour=9, minute=30)),
                (
                    "Data Classification",
                    base.replace(hour=9, minute=30),
                    base.replace(hour=11),
                ),
                (
                    "Privacy & Compliance",
                    base.replace(hour=11, minute=30),
                    base.replace(hour=13),
                ),
            ],
        )
        self.stdout.write("✅ Event 4: Canterbury Workshop (future)")

        e5, _ = Event.objects.update_or_create(
            name="Otago Workshop: Communication Skills",
            defaults={
                "description": "<p>Improve your professional communication and presentation skills.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(80, "NZD"),
                "series": series["RW"],
            },
        )
        e5.locations.set([dunedin])
        base = _dt(-45)
        self._add_sessions(
            e5,
            [
                (
                    "Public Speaking Basics",
                    base.replace(hour=9),
                    base.replace(hour=10, minute=30),
                ),
                (
                    "Storytelling in Business",
                    base.replace(hour=11),
                    base.replace(hour=12, minute=30),
                ),
                (
                    "Persuasive Writing",
                    base.replace(hour=13, minute=30),
                    base.replace(hour=15),
                ),
            ],
        )
        self.stdout.write("✅ Event 5: Otago Workshop (past)")

        # --- 6-8. Webinars (WS series) ---
        e6, _ = Event.objects.update_or_create(
            name="Webinar: Intro to Sustainability Reporting",
            defaults={
                "description": "<p>Learn the basics of ESG and sustainability reporting.</p>",
                "published": True,
                "accessible_online": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
                "series": series["WS"],
            },
        )
        self._add_sessions(
            e6,
            [
                ("Sustainability Reporting", _dt(14, 12), _dt(14, 13, 30)),
            ],
        )
        self.stdout.write("✅ Event 6: Webinar (future, free)")

        e7, _ = Event.objects.update_or_create(
            name="Webinar: Cybersecurity Essentials",
            defaults={
                "description": "<p>Key cybersecurity practices every professional should know.</p>",
                "published": True,
                "accessible_online": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(25, "NZD"),
                "series": series["WS"],
            },
        )
        self._add_sessions(
            e7,
            [
                ("Cybersecurity Essentials", _dt(45, 10), _dt(45, 12)),
            ],
        )
        self.stdout.write("✅ Event 7: Webinar (future)")

        e8, _ = Event.objects.update_or_create(
            name="Webinar: Remote Work Best Practices",
            defaults={
                "description": "<p>Tips and tools for effective remote and hybrid work.</p>",
                "published": True,
                "accessible_online": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
                "series": series["WS"],
            },
        )
        self._add_sessions(
            e8,
            [
                ("Remote Work Best Practices", _dt(-30, 14), _dt(-30, 15)),
            ],
        )
        self.stdout.write("✅ Event 8: Webinar (past, free)")

        # --- 9-11. Networking/social events ---
        e9, _ = Event.objects.update_or_create(
            name="Auckland Networking Evening",
            defaults={
                "description": "<p>An informal evening of networking with industry professionals.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(15, "NZD"),
            },
        )
        e9.locations.set([akl_main])
        self._add_sessions(
            e9,
            [
                ("Drinks & Networking", _dt(-60, 17, 30), _dt(-60, 20)),
            ],
        )
        self.stdout.write("✅ Event 9: Networking Evening (past)")

        e10, _ = Event.objects.update_or_create(
            name="Wellington End-of-Year Social",
            defaults={
                "description": "<p>Celebrate the end of the year with colleagues and friends.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.INVITE_ONLY,
                "price": Money(0, "NZD"),
            },
        )
        e10.locations.set([te_papa])
        self._add_sessions(
            e10,
            [
                ("Social Evening", _dt(75, 18), _dt(75, 21)),
            ],
        )
        self.stdout.write("✅ Event 10: End-of-Year Social (future, invite only)")

        e11, _ = Event.objects.update_or_create(
            name="Christchurch Industry Mixer",
            defaults={
                "description": "<p>Connect with professionals from across Canterbury.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(10, "NZD"),
            },
        )
        e11.locations.set([chch])
        self.stdout.write("✅ Event 11: Industry Mixer (future, no sessions)")
        # Set dates manually since no sessions
        Event.objects.filter(pk=e11.pk).update(start=_dt(90, 17), end=_dt(90, 20))

        # --- 12-14. Training days ---
        e12, _ = Event.objects.update_or_create(
            name="Advanced Excel Training",
            defaults={
                "description": "<p>Master advanced Excel techniques for data analysis.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(200, "NZD"),
            },
        )
        e12.locations.set([akl_a])
        base = _dt(-120)
        self._add_sessions(
            e12,
            [
                (
                    "Pivot Tables & Power Query",
                    base.replace(hour=9),
                    base.replace(hour=10, minute=30),
                ),
                (
                    "Advanced Formulas",
                    base.replace(hour=10, minute=45),
                    base.replace(hour=12, minute=15),
                ),
                ("Lunch", base.replace(hour=12, minute=15), base.replace(hour=13)),
                (
                    "Macros & VBA Basics",
                    base.replace(hour=13),
                    base.replace(hour=14, minute=30),
                ),
                (
                    "Data Visualisation",
                    base.replace(hour=14, minute=45),
                    base.replace(hour=16),
                ),
                (
                    "Wrap-up & Resources",
                    base.replace(hour=16),
                    base.replace(hour=16, minute=30),
                ),
            ],
        )
        self.stdout.write("✅ Event 12: Excel Training (past)")

        e13, _ = Event.objects.update_or_create(
            name="Leadership Development Day",
            defaults={
                "description": "<p>Develop your leadership capabilities through interactive exercises.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(250, "NZD"),
            },
        )
        e13.locations.set([te_papa])
        base = _dt(40)
        self._add_sessions(
            e13,
            [
                (
                    "Leadership Styles Assessment",
                    base.replace(hour=9),
                    base.replace(hour=10, minute=30),
                ),
                (
                    "Conflict Resolution",
                    base.replace(hour=10, minute=45),
                    base.replace(hour=12),
                ),
                ("Lunch", base.replace(hour=12), base.replace(hour=13)),
                (
                    "Coaching & Mentoring",
                    base.replace(hour=13),
                    base.replace(hour=14, minute=30),
                ),
                (
                    "Action Planning",
                    base.replace(hour=14, minute=45),
                    base.replace(hour=16),
                ),
            ],
        )
        self.stdout.write("✅ Event 13: Leadership Development (future)")

        e14, _ = Event.objects.update_or_create(
            name="Financial Literacy for Managers",
            defaults={
                "description": "<p>Understand financial statements and budgeting essentials.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(180, "NZD"),
            },
        )
        e14.locations.set([chch])
        base = _dt(100)
        self._add_sessions(
            e14,
            [
                (
                    "Reading Financial Statements",
                    base.replace(hour=9),
                    base.replace(hour=10, minute=30),
                ),
                (
                    "Budgeting Fundamentals",
                    base.replace(hour=10, minute=45),
                    base.replace(hour=12),
                ),
                ("Lunch", base.replace(hour=12), base.replace(hour=13)),
                (
                    "Forecasting & Planning",
                    base.replace(hour=13),
                    base.replace(hour=14, minute=30),
                ),
            ],
        )
        self.stdout.write("✅ Event 14: Financial Literacy (future)")

        # --- 15-17. External events ---
        e15, _ = Event.objects.update_or_create(
            name="NZ Tech Summit 2026",
            defaults={
                "description": "<p>New Zealand's premier technology summit.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.EXTERNAL,
                "registration_link": "https://nztechsummit.example.com",
                "price": Money(500, "NZD"),
            },
        )
        Event.objects.filter(pk=e15.pk).update(start=_dt(150, 9), end=_dt(152, 17))
        self.stdout.write("✅ Event 15: NZ Tech Summit (future, external)")

        e16, _ = Event.objects.update_or_create(
            name="Australasian HR Conference",
            defaults={
                "description": "<p>Cross-Tasman HR professionals conference.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.EXTERNAL,
                "registration_link": "https://australasianhr.example.com",
                "price": Money(450, "NZD"),
            },
        )
        Event.objects.filter(pk=e16.pk).update(start=_dt(80, 9), end=_dt(81, 17))
        self.stdout.write("✅ Event 16: Australasian HR Conference (future, external)")

        e17, _ = Event.objects.update_or_create(
            name="Pacific Innovation Forum",
            defaults={
                "description": "<p>Regional innovation and entrepreneurship forum.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.EXTERNAL,
                "registration_link": "https://pacificinnovation.example.com",
                "price": Money(300, "NZD"),
            },
        )
        Event.objects.filter(pk=e17.pk).update(start=_dt(170, 9), end=_dt(170, 17))
        self.stdout.write("✅ Event 17: Pacific Innovation Forum (future, external)")

        # --- 18-20. Application-based events ---
        e18, _ = Event.objects.update_or_create(
            name="Emerging Leaders Programme",
            defaults={
                "description": "<p>A selective programme for emerging leaders in the sector.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.APPLY,
                "registration_link": reg_link,
                "price": Money(150, "NZD"),
            },
        )
        e18.locations.set([te_papa])
        base = _dt(-20)
        self._add_sessions(
            e18,
            [
                # Day 1
                ("Welcome & Orientation", base.replace(hour=9), base.replace(hour=10)),
                (
                    "Self-Assessment Workshop",
                    base.replace(hour=10, minute=30),
                    base.replace(hour=12),
                ),
                ("Mentorship Matching", base.replace(hour=13), base.replace(hour=15)),
                # Day 2
                ("Strategic Thinking", _dt(-19, 9), _dt(-19, 11)),
                ("Group Challenge", _dt(-19, 11, 30), _dt(-19, 14)),
                ("Reflection & Next Steps", _dt(-19, 14, 30), _dt(-19, 16)),
            ],
        )
        self.stdout.write("✅ Event 18: Emerging Leaders (past, apply)")

        e19, _ = Event.objects.update_or_create(
            name="Research Symposium 2026",
            defaults={
                "description": "<p>Present and discuss current research in our sector.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.APPLY,
                "registration_link": reg_link,
                "price": Money(100, "NZD"),
            },
        )
        e19.locations.set([chch])
        base = _dt(55)
        self._add_sessions(
            e19,
            [
                # Day 1
                (
                    "Paper Presentations: Morning",
                    base.replace(hour=9),
                    base.replace(hour=12),
                ),
                ("Poster Session", base.replace(hour=13), base.replace(hour=15)),
                (
                    "Keynote Speaker",
                    base.replace(hour=15, minute=30),
                    base.replace(hour=17),
                ),
                # Day 2
                ("Paper Presentations: Advanced", _dt(56, 9), _dt(56, 12)),
                ("Panel Discussion", _dt(56, 13), _dt(56, 14, 30)),
                ("Awards & Closing", _dt(56, 15), _dt(56, 16, 30)),
            ],
        )
        self.stdout.write("✅ Event 19: Research Symposium (future, apply)")

        e20, _ = Event.objects.update_or_create(
            name="Innovation Bootcamp",
            defaults={
                "description": "<p>An intensive two-day bootcamp for innovators and entrepreneurs.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.APPLY,
                "registration_link": reg_link,
                "price": Money(175, "NZD"),
            },
        )
        e20.locations.set([akl_a])
        base = _dt(110)
        self._add_sessions(
            e20,
            [
                # Day 1
                ("Design Thinking Intro", base.replace(hour=9), base.replace(hour=11)),
                (
                    "Ideation Sprint",
                    base.replace(hour=11, minute=30),
                    base.replace(hour=13),
                ),
                (
                    "Prototyping Workshop",
                    base.replace(hour=14),
                    base.replace(hour=16, minute=30),
                ),
                # Day 2
                ("User Testing", _dt(111, 9), _dt(111, 11)),
                ("Pitch Preparation", _dt(111, 11, minute=30), _dt(111, 14)),
                ("Final Pitches & Feedback", _dt(111, 14, 30), _dt(111, 17)),
            ],
        )
        self.stdout.write("✅ Event 20: Innovation Bootcamp (future, apply)")

        # --- 21-23. Community meetups ---
        e21, _ = Event.objects.update_or_create(
            name="Auckland Community Meetup",
            defaults={
                "description": "<p>Monthly community gathering for members in Auckland.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
            },
        )
        e21.locations.set([akl_main])
        base = _dt(-15)
        self._add_sessions(
            e21,
            [
                (
                    "Lightning Talks",
                    base.replace(hour=17, minute=30),
                    base.replace(hour=18, minute=30),
                ),
                (
                    "Open Discussion",
                    base.replace(hour=18, minute=30),
                    base.replace(hour=19, minute=30),
                ),
                (
                    "Casual Networking",
                    base.replace(hour=19, minute=30),
                    base.replace(hour=20, minute=30),
                ),
            ],
        )
        self.stdout.write("✅ Event 21: Auckland Meetup (past, free)")

        e22, _ = Event.objects.update_or_create(
            name="Wellington Community Meetup",
            defaults={
                "description": "<p>Monthly community gathering for members in Wellington.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
            },
        )
        e22.locations.set([te_papa])
        base = _dt(20)
        self._add_sessions(
            e22,
            [
                (
                    "Guest Speaker",
                    base.replace(hour=17, minute=30),
                    base.replace(hour=18, minute=30),
                ),
                (
                    "Workshop Activity",
                    base.replace(hour=18, minute=30),
                    base.replace(hour=19, minute=30),
                ),
            ],
        )
        self.stdout.write("✅ Event 22: Wellington Meetup (future, free)")

        e23, _ = Event.objects.update_or_create(
            name="Tauranga Community Meetup",
            defaults={
                "description": "<p>Community gathering for Bay of Plenty members.</p>",
                "published": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
            },
        )
        e23.locations.set([tauranga])
        base = _dt(50)
        self._add_sessions(
            e23,
            [
                (
                    "Show & Tell",
                    base.replace(hour=17, minute=30),
                    base.replace(hour=18, minute=30),
                ),
                (
                    "Group Discussion",
                    base.replace(hour=18, minute=30),
                    base.replace(hour=19, minute=30),
                ),
            ],
        )
        self.stdout.write("✅ Event 23: Tauranga Meetup (future, free)")

        # --- 24. Multi-day retreat ---
        e24, _ = Event.objects.update_or_create(
            name="Annual Leadership Retreat",
            defaults={
                "description": "<p>A four-day retreat for senior leaders in a stunning lakeside setting.</p>",
                "published": True,
                "show_schedule": True,
                "featured": True,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(500, "NZD"),
            },
        )
        e24.locations.set([wanaka])
        e24.sponsors.set([entities[3], entities[4]])
        base = _dt(140)
        self._add_sessions(
            e24,
            [
                # Day 1
                (
                    "Welcome & Check-in",
                    base.replace(hour=14),
                    base.replace(hour=15, minute=30),
                ),
                (
                    "Vision Setting Workshop",
                    base.replace(hour=16),
                    base.replace(hour=18),
                ),
                # Day 2
                ("Morning Mindfulness", _dt(141, 7), _dt(141, 8)),
                ("Track A: Strategic Planning", _dt(141, 9), _dt(141, 12)),
                ("Track B: Team Dynamics", _dt(141, 9), _dt(141, 12)),
                ("Collaborative Lunch", _dt(141, 12), _dt(141, 13)),
                ("Track A: Innovation Lab", _dt(141, 14), _dt(141, 16, 30)),
                ("Track B: Wellbeing & Resilience", _dt(141, 14), _dt(141, 16, 30)),
                # Day 3
                ("Morning Mindfulness", _dt(142, 7), _dt(142, 8)),
                ("Cross-team Projects", _dt(142, 9), _dt(142, 12)),
                ("Outdoor Team Challenge", _dt(142, 13), _dt(142, 16)),
                ("Evening Dinner & Reflection", _dt(142, 18), _dt(142, 21)),
                # Day 4
                ("Personal Action Plans", _dt(143, 9), _dt(143, 11)),
                ("Closing Circle", _dt(143, 11, 30), _dt(143, 13)),
            ],
        )
        self.stdout.write("✅ Event 24: Leadership Retreat (future, multi-day)")

        # --- 25. Cancelled/unpublished event ---
        e25, _ = Event.objects.update_or_create(
            name="Draft Workshop: TBD",
            defaults={
                "description": "<p>This event is still being planned.</p>",
                "published": False,
                "registration_type": Event.RegistrationType.REGISTER,
                "registration_link": reg_link,
                "price": Money(0, "NZD"),
            },
        )
        Event.objects.filter(pk=e25.pk).update(start=_dt(180, 9), end=_dt(180, 17))
        self.stdout.write("✅ Event 25: Draft Workshop (unpublished)")
