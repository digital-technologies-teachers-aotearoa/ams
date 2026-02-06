# Features

## Core Capabilities

### 🎯 Membership Management

AMS provides comprehensive membership management for both individual and organization-based memberships. Configure multiple membership types with different pricing tiers and renewal cycles.
Organizations can manage their allocated seats, inviting and removing members as needed.
Custom profile fields allow you to collect association-specific information without requiring code changes.

The platform aims to handle the complete membership lifecycle.
Automated email notifications keep members informed at each stage, while administrators benefit from dashboard views showing membership statistics, pending applications, and upcoming renewals.

**Key Features:**

- Individual and organization membership models with seat allocation
- Flexible membership types with configurable pricing and benefits
- Custom profile fields for association-specific data collection
- Member self-service for profile updates and organization management
- Membership status tracking with activity history
- Bulk operations for membership administration

<!-- [Screenshot: Membership management interface with active/pending members list] -->

### 💳 Integrated Billing

Native integration with Xero accounting software streamlines all billing operations.
When a member applies, AMS automatically creates invoices in Xero, eliminating manual data entry and ensuring financial records remain accurate.
Real-time synchronization keeps payment status current in both systems.

The Xero integration provides secure, granular access without requiring shared passwords.
Configurable pricing allows for special pricing for different membership categories.

**Key Features:**

- Custom connection Xero integration for secure, automated invoice generation
- Automatic invoice creation for applications and transactions
- Real-time payment status synchronization between AMS and Xero
- Flexible pricing with support for tiered rates
- Rate limiting and error handling for reliable API communication

<!-- [Screenshot: Xero invoice generation and payment tracking] -->

### 📄 Content Management System

Built on Wagtail, AMS provides a powerful yet user-friendly content management system that empowers non-technical staff to create and publish rich content.
The StreamField architecture allows editors to build pages using reusable content blocks, maintaining consistency while providing creative flexibility.

Path-based multi-language routing enables associations to serve content in multiple languages—particularly valuable for New Zealand associations serving both English and Te Reo Māori speaking members.
The preview and workflow features allow content to be drafted, reviewed, and scheduled for publication without technical intervention.

**Key Features:**

- Wagtail CMS with intuitive editing interface
- StreamField blocks for flexible, structured content creation
- Multi-language content with path-based routing (e.g., `/en/about`, `/mi/about`)
- Full support for English and Te Reo Māori
- Draft, preview, and publish workflow with revision history
- Scheduled publishing for time-sensitive content
- Image management with automatic resizing and optimization
- Hierarchical page structure with customizable navigation

<!-- [Screenshot: Wagtail CMS page editor with StreamField blocks and multi-language tabs] -->

### 💬 Community Forum

Seamless integration with Discourse forum platform provides a dedicated space for member discussions, peer support, and community building.
Single sign-on (SSO) via OAuth2 means members use the same credentials across both AMS and the forum, eliminating the friction of separate accounts.

Access control is automatically synchronized with membership status.
Active members gain forum access, while lapsed memberships result in automatic access deactivation.

**Key Features:**

- Discourse forum integration with OAuth2 single sign-on
- Automatic access control based on active membership status
- Unified user credentials across AMS and forum
- Consistent branding and navigation between platforms
- Member profile synchronization
- Seamless transition between website and forum

<!-- [Screenshot: Discourse forum SSO login flow] -->

### 🎨 Customization and Branding

AMS provides extensive customization options without requiring code modifications.
Upload your association's logo, configure brand colors, and customize the visual theme to match your organization's identity.
The Bootstrap based design ensures responsive, modern styling across all devices.

Custom profile fields allow you to collect and display information specific to your association's context.
Whether you need to track certifications, specializations, employment details, or any other member attributes, custom fields can be configured through the admin interface.
Form-based configuration for membership types and pricing enable operational changes without developer involvement.

**Key Features:**

- Logo upload and branding customization
- Theme color configuration with live preview
- Bootstrap and CSS variables for advanced styling
- Custom profile fields with various field types (text, choice, date, etc.)
- Configurable membership types and pricing
- Multi-language content and interface text
- Responsive design for mobile, tablet, and desktop

<!-- [Screenshot: Theme customization panel with brand colors and logo upload] -->

### 🌏 Multi-Language Support (in progress)

AMS provides comprehensive multi-language capabilities, with full support for both English and Te Reo Māori.
Path-based routing allows content to be served in different languages (e.g., `/en/membership` vs `/mi/membership`), while the Wagtail CMS enables translation of all page content.
Interface text, system emails, and form labels are managed through Django's translation system, allowing for complete localization.

**Key Features:**

- English and Te Reo Māori interface support
- Path-based multi-language content routing
- Translatable CMS pages with language-specific content
- Localized system emails and notifications
- Translatable form labels and help text
- Language switcher for member convenience
- Fallback language configuration

## Who is AMS For?

### Association Administrators and Operations Staff

If you manage the day-to-day operations of a membership association, AMS streamlines your work.
Automated billing eliminates manual invoice creation and payment tracking.
Membership management dashboards provide at-a-glance views of applications and member statistics.
The intuitive CMS allows you to publish content without technical assistance.

**Benefits:**

- Reduce administrative overhead with automation
- Access real-time membership and financial data
- Manage content without developer dependency
- Streamline member onboarding and renewals
- Maintain accurate records across systems

### IT Teams and Developers

Built on proven, well-documented technologies, AMS provides a solid foundation for technical teams.
The Django framework, PostgreSQL database, and Docker-based deployment ensure reliability and scalability.
Comprehensive documentation covers installation, configuration, and customization.
The open-source codebase allows for extension and modification to meet specific requirements.

**Technical Benefits:**

- Modern Python/Django codebase with type hints
- PostgreSQL database with Django ORM
- Docker and Docker Compose for consistent deployment
- Wagtail CMS for content management
- RESTful API patterns for integration
- Comprehensive test suite with pytest
- CI/CD ready architecture
- Extensive developer documentation

### Association Members

Members benefit from a unified, self-service platform.
Update your profile, manage organization memberships, track membership expiry dates, and access association content all in one place.
Single sign-on provides seamless access to the community forum.
Clear membership status information and automated renewal reminders ensure continuous participation.

**Member Benefits:**

- Single account for all association services
- Self-service profile and membership management
- Clear visibility of membership status and benefits
- Access to member-only content and forums
- Mobile-friendly interface for on-the-go access
- Multi-language content options

## Why Choose AMS?

**Open Source:** Full transparency, no vendor lock-in, and community-driven development. Review the code, understand how it works, and modify it to suit your needs. Benefit from community contributions and share improvements back to the ecosystem.

**Self-Hosted:** Complete control over your data and infrastructure. Host on your own servers or cloud platform of choice. Ensure data sovereignty and privacy compliance. No per-user fees or forced upgrades.

**All-in-One:** Eliminate the complexity of integrating multiple separate systems for membership, billing, content, and community. Single platform, single database, unified user experience. Reduce vendor management overhead and integration maintenance.

**Built for NZ/AU:** Native Xero integration for seamless accounting, multi-currency support for regional and international members, and te reo Māori language support for New Zealand associations committed to bilingual service.

**Modern Stack:** Built on Django 4, Wagtail 5, PostgreSQL, and containerized with Docker. Benefit from mature, well-supported technologies with extensive documentation and active communities. Future-proof architecture with clear upgrade paths.

**Active Development:** Developed and maintained by DTTA for their own operational needs, ensuring continued evolution based on real-world association management requirements. Regular updates, bug fixes, and new features driven by practical experience.

<!-- markdownlint-disable -->
<style>
.md-sidebar--primary { display: none;}
</style>
