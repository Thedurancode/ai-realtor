"""
Tests for Direct Mail Template System
"""

import pytest
from unittest.mock import Mock, patch
from jinja2 import Template

from app.templates.direct_mail import (
    get_template,
    list_templates,
    render_template,
    seed_direct_mail_templates,
    TEMPLATES
)


class TestDirectMailTemplates:
    """Test direct mail template system"""

    def test_all_templates_exist(self):
        """Test that all required templates are defined"""
        expected_templates = [
            "just_sold",
            "open_house",
            "market_update",
            "new_listing",
            "price_reduction",
            "hello"
        ]

        for template_name in expected_templates:
            assert template_name in TEMPLATES, f"Template '{template_name}' not found"

    def test_template_structure(self):
        """Test that templates have required fields"""
        required_fields = [
            "name",
            "description",
            "template_type",
            "campaign_type",
            "front_html"
        ]

        for template_name, template in TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"Template '{template_name}' missing field '{field}'"

    def test_get_template_by_name(self):
        """Test retrieving a specific template"""
        template = get_template("just_sold")

        assert template is not None
        assert template["name"] == "Just Sold"
        assert template["campaign_type"] == "just_sold"
        assert template["template_type"] == "postcard"
        assert len(template["front_html"]) > 0

    def test_get_template_invalid_name(self):
        """Test that invalid template name raises error"""
        with pytest.raises(ValueError, match="Template 'invalid_template' not found"):
            get_template("invalid_template")

    def test_list_templates(self):
        """Test listing all templates"""
        templates = list_templates()

        assert len(templates) == 6
        assert all("name" in t for t in templates)
        assert all("description" in t for t in templates)
        assert all("type" in t for t in templates)

        template_names = [t["name"] for t in templates]
        assert "Just Sold" in template_names
        assert "Open House" in template_names

    def test_render_template_basic(self):
        """Test basic template rendering"""
        template_html = "<div>Hello {{name}}!</div>"
        variables = {"name": "World"}

        result = render_template(template_html, variables)

        assert result == "<div>Hello World!</div>"

    def test_render_template_with_property_data(self):
        """Test rendering with property variables"""
        template_html = """
        <div>
            <h1>{{property_address}}</h1>
            <p>Sold for {{sold_price}}</p>
            <p>Agent: {{agent_name}}</p>
        </div>
        """

        variables = {
            "property_address": "123 Main St",
            "sold_price": "$500,000",
            "agent_name": "Jane Doe"
        }

        result = render_template(template_html, variables)

        assert "123 Main St" in result
        assert "$500,000" in result
        assert "Jane Doe" in result

    def test_render_template_missing_variable(self):
        """Test rendering with missing variables (graceful handling)"""
        template_html = "<div>{{property_address}} - {{missing_var}}</div>"
        variables = {"property_address": "123 Main St"}

        result = render_template(template_html, variables)

        # Should preserve the missing variable placeholder
        assert "123 Main St" in result
        assert "{{missing_var}}" in result or "missing_var" in result

    def test_render_template_with_property_photo(self):
        """Test rendering with conditional property photo"""
        template_html = """
        {% if property_photo %}
        <img src="{{property_photo}}">
        {% else %}
        <p>No photo</p>
        {% endif %}
        """

        # With photo
        result_with = render_template(template_html, {"property_photo": "http://example.com/photo.jpg"})
        assert "http://example.com/photo.jpg" in result_with
        assert "No photo" not in result_with

        # Without photo
        result_without = render_template(template_html, {})
        assert "No photo" in result_without
        assert "property_photo" not in result_without

    def test_just_sold_template_content(self):
        """Test Just Sold template has expected content"""
        template = get_template("just_sold")

        assert "JUST SOLD!" in template["front_html"]
        assert "property_address" in template["front_html"]
        assert "sold_price" in template["front_html"]
        assert "agent_name" in template["front_html"]

    def test_open_house_template_content(self):
        """Test Open House template has expected content"""
        template = get_template("open_house")

        assert "OPEN HOUSE" in template["front_html"].upper()
        assert "date" in template["front_html"]
        assert "time" in template["front_html"]

    def test_market_update_template_content(self):
        """Test Market Update template has expected content"""
        template = get_template("market_update")

        assert "MARKET UPDATE" in template["front_html"].upper()
        assert "neighborhood" in template["front_html"]

    def test_new_listing_template_content(self):
        """Test New Listing template has expected content"""
        template = get_template("new_listing")

        assert "NEW LISTING" in template["front_html"].upper()
        assert "property_address" in template["front_html"]

    def test_price_reduction_template_content(self):
        """Test Price Reduction template has expected content"""
        template = get_template("price_reduction")

        assert "PRICE REDUCTION" in template["front_html"].upper()
        assert "old_price" in template["front_html"]
        assert "new_price" in template["front_html"]

    def test_hello_template_content(self):
        """Test Hello/Farming template has expected content"""
        template = get_template("hello")

        assert "agent_name" in template["front_html"]
        assert "company" in template["front_html"]

    def test_template_required_variables(self):
        """Test that templates declare required variables"""
        templates_with_vars = ["just_sold", "open_house", "new_listing", "price_reduction"]

        for template_name in templates_with_vars:
            template = get_template(template_name)
            assert "required_variables" in template
            assert isinstance(template["required_variables"], list)
            assert len(template["required_variables"]) > 0

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db

    def test_seed_templates_creates_new_templates(self, mock_db):
        """Test that seeding creates templates that don't exist"""
        # Mock that no templates exist yet
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.templates.direct_mail.DirectMailTemplate') as MockTemplate:
            mock_template_instance = Mock()
            MockTemplate.return_value = mock_template_instance

            count = seed_direct_mail_templates(mock_db, agent_id=1)

            # Should have created all 6 templates
            assert count == 6
            assert mock_db.add.call_count == 6
            assert mock_db.commit.call_count == 1

    def test_seed_templates_skips_existing(self, mock_db):
        """Test that seeding skips existing templates"""
        # Mock that templates already exist
        existing_template = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_template

        with patch('app.templates.direct_mail.DirectMailTemplate'):
            count = seed_direct_mail_templates(mock_db, agent_id=1)

            # Should not create any new templates
            assert count == 0
            assert mock_db.add.call_count == 0

    def test_seed_templates_handles_errors(self, mock_db):
        """Test that seeding handles database errors gracefully"""
        mock_db.query.side_effect = Exception("Database error")

        with patch('app.templates.direct_mail.DirectMailTemplate'):
            count = seed_direct_mail_templates(mock_db, agent_id=1)

            # Should return 0 on error
            assert count == 0
            assert mock_db.rollback.call_count == 1

    def test_template_html_is_well_formed(self):
        """Test that template HTML is well-formed"""
        for template_name, template in TEMPLATES.items():
            html = template["front_html"]

            # Basic HTML structure checks
            assert "<div" in html or "<html" in html
            assert "</div>" in html or "</html>" in html

            # Should have proper closing tags for common elements
            if "<h1>" in html:
                assert "</h1>" in html
            if "<h2>" in html:
                assert "</h2>" in html
            if "<p>" in html:
                assert "</p>" in html

    def test_templates_use_jinja2_syntax(self):
        """Test that templates use proper Jinja2 syntax"""
        for template_name, template in TEMPLATES.items():
            html = template["front_html"]

            # Should have Jinja2 variables
            assert "{{" in html
            assert "}}" in html

            # Should not have malformed syntax
            assert "{{{" not in html  # Triple braces are not needed
            assert "}}}" not in html
