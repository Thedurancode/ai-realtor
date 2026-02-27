"""
Website Renderer Service

Converts website content into HTML for published websites
"""
from typing import Dict
from sqlalchemy.orm import Session

from app.models.property_website import PropertyWebsite
from app.models.property import Property


class WebsiteRenderer:
    """Render AI-generated websites as HTML"""

    def __init__(self, db: Session):
        self.db = db

    async def render_website(self, website: PropertyWebsite) -> str:
        """Render complete HTML for a website"""
        content = website.content
        theme = website.theme or {}

        # Build HTML sections
        html_parts = []

        # HTML Header
        html_parts.append(self._generate_html_head(website, theme))

        # Navigation
        html_parts.append(self._generate_navigation(website, theme))

        # Hero Section
        if "hero" in content.get("sections", {}):
            html_parts.append(self._render_hero_section(
                content["sections"]["hero"],
                theme
            ))

        # Features Section
        if "features" in content.get("sections", {}):
            html_parts.append(self._render_features_section(
                content["sections"]["features"],
                theme
            ))

        # Gallery Section
        if "gallery" in content.get("sections", {}):
            html_parts.append(self._render_gallery_section(
                content["sections"]["gallery"],
                theme
            ))

        # About Section
        if "about" in content.get("sections", {}):
            html_parts.append(self._render_about_section(
                content["sections"]["about"],
                theme
            ))

        # Contact Section
        if "contact" in content.get("sections", {}):
            html_parts.append(self._render_contact_section(
                content["sections"]["contact"],
                website,
                theme
            ))

        # CTA Section
        if "cta" in content.get("sections", {}):
            html_parts.append(self._render_cta_section(
                content["sections"]["cta"],
                website,
                theme
            ))

        # Footer
        html_parts.append(self._generate_footer(website, theme))

        # JavaScript
        html_parts.append(self._generate_javascript(website, theme))

        # Close HTML
        html_parts.append("</body></html>")

        return "\n".join(html_parts)

    def _generate_html_head(self, website: PropertyWebsite, theme: Dict) -> str:
        """Generate HTML <head> section"""
        primary_color = theme.get("primary_color", "#3b82f6")
        font = theme.get("font", "Inter")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(website.website_name)}</title>
    <meta name="description" content="{self._escape_html(content.get('sections', {}).get('hero', {}).get('subheadline', ''))}">
    <meta property="og:title" content="{self._escape_html(website.website_name)}">
    <meta property="og:description" content="{self._escape_html(content.get('sections', {}).get('hero', {}).get('subheadline', ''))}">
    <meta property="og:image" content="{content.get('sections', {}).get('hero', {}).get('background_image', '')}">
    <meta property="og:type" content="website">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family={font}:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <!-- Styles -->
    <style>
        /* Reset & Base */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: '{font}', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #ffffff;
        }}

        /* Hero Section */
        .hero {{
            height: 80vh;
            min-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            background: linear-gradient(135deg, {primary_color} 0%, {{theme.get('secondary_color', primary_color)}} 100%);
            color: #ffffff;
            position: relative;
            overflow: hidden;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('{content.get('sections', {}).get('hero', {}).get('background_image', '')}');
            background-size: cover;
            background-position: center;
            opacity: 0.3;
        }}

        .hero-overlay {{
            position: relative;
            z-index: 1;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .hero h1 {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            margin-bottom: 1rem;
            line-height: 1.2;
        }}

        .hero p {{
            font-size: clamp(1.125rem, 2vw, 1.5rem);
            opacity: 0.95;
            margin-bottom: 2rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }}

        .price-display {{
            font-size: clamp(2rem, 4vw, 3rem);
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .price-note {{
            font-size: 1rem;
            opacity: 0.9;
        }}

        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            border-radius: {{theme.get('border_radius', '8px')}};
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 1rem;
        }}

        .btn-primary {{
            background: #ffffff;
            color: {primary_color};
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}

        .btn-secondary {{
            background: transparent;
            color: #ffffff;
            border: 2px solid #ffffff;
        }}

        .btn-secondary:hover {{
            background: #ffffff;
            color: {primary_color};
        }}

        .btn-green {{
            background: #10b981;
            color: #ffffff;
        }}

        .btn-green:hover {{
            background: #059669;
            transform: translateY(-2px);
        }}

        /* Features Section */
        .features {{
            padding: 5rem 2rem;
            background: #f9fafb;
        }}

        .features-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .features h2 {{
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 3rem;
            color: {theme.get('text_color', '#1f2937')};
        }}

        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }}

        .feature-card {{
            background: #ffffff;
            padding: 2rem;
            border-radius: {{theme.get('border_radius', '8px')}};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}

        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        }}

        .feature-card h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: {theme.get('primary_color', '#3b82f6')};
        }}

        .feature-card p {{
            color: #6b7280;
            font-size: 0.875rem;
        }}

        /* Gallery Section */
        .gallery {{
            padding: 5rem 2rem;
        }}

        .gallery-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .gallery h2 {{
            text-align: center;
            font_size: 2.5rem;
            font-weight: 700;
            margin-bottom: 3rem;
            color: {theme.get('text_color', '#1f2937')};
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }}

        .gallery-item {{
            position: relative;
            overflow: hidden;
            border-radius: {{theme.get('border_radius', '8px')}};
            aspect-ratio: 16 / 9;
            background: #f3f4f6;
        }}

        .gallery-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .gallery-item:hover img {{
            transform: scale(1.05);
        }}

        /* Contact Section */
        .contact {{
            padding: 5rem 2rem;
            background: #ffffff;
        }}

        .contact-container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .contact h2 {{
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: {theme.get('text_color', '#1f2937')};
        }}

        .contact p {{
            text-align: center;
            font-size: 1.125rem;
            color: #6b7280;
            margin-bottom: 3rem;
        }}

        .contact-form {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .form-group {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .form-group label {{
            font-weight: 500;
            color: {theme.get('text_color', '#1f2937')};
            font-size: 0.875rem;
        }}

        .form-group input,
        .form-group textarea {{
            padding: 0.75rem 1rem;
            border: 1px solid #d1d5db;
            border-radius: 0.5rem;
            font-family: inherit;
            font-size: 1rem;
            transition: border-color 0.2s;
        }}

        .form-group input:focus,
        .form-group textarea:focus {{
            outline: none;
            border-color: {primary_color};
        }}

        .form-group textarea {{
            min-height: 120px;
            resize: vertical;
        }}

        /* CTA Section */
        .cta {{
            padding: 5rem 2rem;
            background: linear-gradient(135deg, {primary_color}15 0%, {{theme.get('secondary_color', primary_color)}}15 100%);
            color: #ffffff;
            text-align: center;
        }}

        .cta-content {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .cta h2 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}

        .cta p {{
            font-size: 1.25rem;
            opacity: 0.95;
            margin-bottom: 2rem;
        }}

        .cta-buttons {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }}

        /* Footer */
        .footer {{
            background: #111827;
            color: #f3f4f6;
            padding: 3rem 2rem;
        }}

        .footer-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }}

        .footer-section h3 {{
            color: #ffffff;
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}

        .footer-section p {{
            color: #d1d5db;
            font-size: 0.875rem;
            line-height: 1.6;
        }}

        .footer-bottom {{
            max-width: 1200px;
            margin: 2rem auto 0 auto;
            padding-top: 2rem;
            border-top: 1px solid #374151;
            text-align: center;
            color: #9ca3af;
            font-size: 0.875rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero {{
                height: 60vh;
            }}

            .features-grid,
            .gallery-grid {{
                grid-template-columns: 1fr;
            }}

            .cta-buttons {{
                flex-direction: column;
            }}
        }}
    </style>

    <!-- Google Analytics (would be added dynamically) -->
</head>
"""

    def _generate_navigation(self, website: PropertyWebsite, theme: Dict) -> str:
        """Generate navigation bar"""
        primary_color = theme.get("primary_color", "#3b82f6")

        return f"""
        <nav class="navigation">
            <div class="nav-container">
                <div class="nav-brand">
                    {website.website_name}
                </div>
                <ul class="nav-links">
                    <li><a href="#features">Features</a></li>
                    <li><a href="#gallery">Gallery</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </div>
        </nav>

        <style>
        .navigation {{
            background: #ffffff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}

        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .nav-brand {{
            font-weight: 700;
            font-size: 1.25rem;
            color: {primary_color};
            text-decoration: none;
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
            margin: 0;
            padding: 0;
        }}

        .nav-links a {{
            color: #374151;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}

        .nav-links a:hover {{
            color: {primary_color};
        }}

        @media (max-width: 768px) {{
            .nav-links {{
                display: none;
            }}
        }}
        </style>
        """

    def _render_hero_section(self, hero_content: Dict, theme: Dict) -> str:
        """Render hero section HTML"""
        return f"""
        <section class="hero">
            <div class="hero-overlay">
                <h1>{self._escape_html(hero_content.get('headline', 'Beautiful Property for Sale'))}</h1>
                <p>{self._escape_html(hero_content.get('subheadline', ''))}</p>
                {f'<div class="price-display">{hero_content.get("price_display", "")}</div>' if hero_content.get("price_display") else ''}
                {f'<p class="price-note">{hero_content.get("price_note", "")}</p>' if hero_content.get("price_note") else ''}
                <div class="hero-buttons">
                    <a href="#contact" class="btn btn-primary">{hero_content.get('primary_cta', {}).get('text', 'Contact Us')}</a>
                    {f'<a href="#gallery" class="btn btn-secondary">{hero_content.get('secondary_cta', {}).get('text', 'View Gallery')}</a>' if hero_content.get('secondary_cta') else ''}
                </div>
            </div>
        </section>
        """

    def _render_features_section(self, features_content: Dict, theme: Dict) -> str:
        """Render features section HTML"""
        features = features_content.get("features", [])

        feature_items = ""
        for feature in features[:12]:
            feature_items += f"""
            <div class="feature-card">
                <h3>{self._escape_html(feature.get('name', 'Feature'))}</h3>
                <p>{self._escape_html(feature.get('description', ''))}</p>
            </div>
            """

        return f"""
        <section id="features" class="features">
            <div class="features-container">
                <h2>{self._escape_html(features_content.get('title', 'Property Features'))}</h2>
                <div class="features-grid">
                    {feature_items}
                </div>
            </div>
        </section>
        """

    def _render_gallery_section(self, gallery_content: Dict, theme: Dict) -> str:
        """Render gallery section HTML"""
        images = gallery_content.get("images", [])

        gallery_items = ""
        for img in images[:12]:
            gallery_items += f"""
            <div class="gallery-item">
                <img src="{img.get('url', '')}" alt="{self._escape_html(img.get('alt', 'Property photo'))}">
            </div>
            """

        return f"""
        <section id="gallery" class="gallery">
            <div class="gallery-container">
                <h2>{self._escape_html(gallery_content.get('title', 'Property Gallery'))}</h2>
                <div class="gallery-grid">
                    {gallery_items}
                </div>
            </div>
        </section>
        """

    def _render_about_section(self, about_content: Dict, theme: Dict) -> str:
        """Render about section HTML"""
        return f"""
        <section class="about" style="padding: 5rem 2rem;">
            <div class="container">
                <h2>{self._escape_html(about_content.get('title', 'About This Property'))}</h2>
                <p style="max-width: 800px; margin: 1.5rem auto; line-height: 1.7;">
                    {self._escape_html(about_content.get('description', ''))}
                </p>
            </div>
        </section>
        """

    def _render_contact_section(self, contact_content: Dict, website: PropertyWebsite, theme: Dict) -> str:
        """Render contact form HTML"""
        form_fields = contact_content.get("form_fields", [])

        form_html = ""
        for field in form_fields:
            field_name = field.get("name", "")
            field_label = field.get("label", "")
            field_type = field.get("type", "text")
            required = field.get("required", False)

            required_attr = "required" if required else ""
            required_mark = " *" if required else ""

            if field_type == "textarea":
                form_html += f"""
                <div class="form-group">
                    <label for="{field_name}">{field_label}{required_mark}</label>
                    <textarea
                        id="{field_name}"
                        name="{field_name}"
                        placeholder="{field_label}"
                        {required_attr}
                    ></textarea>
                </div>
                """
            else:
                input_type = field_type if field_type not in ["text", "email"] else "text"
                form_html += f"""
                <div class="form-group">
                    <label for="{field_name}">{field_label}{required_mark}</label>
                    <input
                        type="{input_type}"
                        id="{field_name}"
                        name="{field_name}"
                        placeholder="{field_label}"
                        {required_attr}
                    >
                </div>
                """

        return f"""
        <section id="contact" class="contact">
            <div class="contact-container">
                <h2>{self._escape_html(contact_content.get('title', 'Contact Us'))}</h2>
                <p>{self._escape_html(contact_content.get('subtitle', ''))}</p>

                <form class="contact-form" method="POST" action="/api/websites/{website.website_slug}/submit">
                    {form_html}

                    <button type="submit" class="btn btn-green" style="width: 100%; margin-top: 1rem;">
                        {contact_content.get('submit_button', 'Send Message')}
                    </button>

                    <p style="text-align: center; font-size: 0.875rem; color: #6b7280; margin-top: 1rem;">
                        🔒 Your information is secure and will never be shared.
                    </p>
                </form>
            </div>
        </section>
        """

    def _render_cta_section(self, cta_content: Dict, website: PropertyWebsite, theme: Dict) -> str:
        """Render call-to-action section HTML"""
        return f"""
        <section class="cta">
            <div class="cta-content">
                <h2>{self._escape_html(cta_content.get('headline', 'Ready to Learn More?'))}</h2>
                <p>{self._escape_html(cta_content.get('subheadline', ''))}</p>
                <div class="cta-buttons">
                    <a href="#contact" class="btn btn-primary">
                        {cta_content.get('primary_cta', {}).get('text', 'Contact Us')}
                    </a>
                    {f'<a href="#gallery" class="btn btn-secondary">{cta_content.get('secondary_cta', {}).get('text', 'View Gallery')}</a>' if cta_content.get('secondary_cta') else ''}
                </div>
            </div>
        </section>
        """

    def _generate_footer(self, website: PropertyWebsite, theme: Dict) -> str:
        """Generate footer HTML"""
        return f"""
        <footer class="footer">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>{website.website_name}</h3>
                    <p>{website.content.get('seo', {}).get('description', '')[:200]}</p>
                </div>
                <div class="footer-section">
                    <h3>Quick Links</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><a href="#features" style="color: inherit; text-decoration: none;">Features</a></li>
                        <li><a href="#gallery" style="color: inherit; text-decoration: none;">Gallery</a></li>
                        <li><a href="#contact" style="color: inherit; text-decoration: none;">Contact</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Contact</h3>
                    <p>Interested in this property? Get in touch today!</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} {website.website_name}. All rights reserved.</p>
                <p>Powered by RealtorClaw AI</p>
            </div>
        </footer>
        """

    def _generate_javascript(self, website: PropertyWebsite, theme: Dict) -> str:
        """Generate JavaScript for interactivity"""
        return f"""
        <script>
            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});

            // Contact form submission
            const form = document.querySelector('form[action*="/submit"]');
            if (form) {{
                form.addEventListener('submit', async (e) => {{
                    e.preventDefault();

                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData);

                    try {{
                        const response = await fetch('/api/websites/{website.website_slug}/submit', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify(data)
                        }});

                        if (response.ok) {{
                            alert('Thank you for your inquiry! We will get back to you within 24 hours.');
                            form.reset();
                        }} else {{
                            alert('There was an error submitting your message. Please try again.');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('There was an error submitting your message. Please try again.');
                    }}
                }});
            }});

            // Track button clicks
            const ctaButtons = document.querySelectorAll('.cta-buttons a');
            ctaButtons.forEach(button => {{
                button.addEventListener('click', (e) => {{
                    // Track CTA clicks
                    fetch('/api/websites/{website.website_slug}/track', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            event_type: 'cta_click',
                            button_text: button.textContent.trim(),
                            destination: button.getAttribute('href')
                        }})
                    }}).catch(console.error);
                }});
        </script>
        """

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        import html
        return html.escape(text)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        import html
        return html.escape(text)
