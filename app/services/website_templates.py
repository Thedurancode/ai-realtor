"""
Website Templates

Pre-defined landing page templates with different layouts and styles
"""
from typing import Dict, List


class WebsiteTemplates:
    """Website template definitions and structures"""

    def __init__(self):
        self.templates = {
            "modern": {
                "name": "Modern",
                "description": "Contemporary design with bold colors and clean layout",
                "layout": [
                    "hero",
                    "features",
                    "gallery",
                    "about",
                    "contact",
                    "cta"
                ]
            },
            "luxury": {
                "name": "Luxury",
                "description": "Elegant design with refined typography and gold accents",
                "layout": [
                    "hero",
                    "about",
                    "features",
                    "gallery",
                    "contact",
                    "cta"
                ]
            },
            "minimal": {
                "name": "Minimal",
                "description": "Clean, simple design with lots of white space",
                "layout": [
                    "hero",
                    "features",
                    "gallery",
                    "contact"
                ]
            },
            "corporate": {
                "name": "Corporate",
                "description": "Professional business-oriented design",
                "layout": [
                    "hero",
                    "stats",
                    "about",
                    "features",
                    "testimonials",
                    "contact"
                ]
            }
        }

    def get_template_structure(self, template_name: str) -> Dict:
        """Get the section layout for a template"""
        return self.templates.get(template_name, self.templates["modern"])

    def get_available_templates(self) -> List[Dict]:
        """List all available templates"""
        return [
            {
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "section_count": len(template["layout"])
            }
            for template_id, template in self.templates.items()
        ]

    def get_section_config(self, section: str, template: str) -> Dict:
        """Get configuration for a specific section"""
        section_configs = {
            "hero": {
                "modern": {
                    "height": "80vh",
                    "overlay": True,
                    "text_align": "center",
                    "animations": True
                },
                "luxury": {
                    "height": "90vh",
                    "overlay": True,
                    "text_align": "center",
                    "animations": True
                }
            },
            "features": {
                "modern": {
                    "columns": 3,
                    "icons": True,
                    "cards": True
                },
                "luxury": {
                    "columns": 2,
                    "icons": True,
                    "cards": True
                }
            },
            "gallery": {
                "modern": {
                    "layout": "masonry",
                    "hover_effect": "zoom",
                    "lazy_loading": True
                },
                "luxury": {
                    "layout": "grid",
                    "hover_effect": "fade",
                    "lazy_loading": True
                }
            }
        }

        return section_configs.get(section, {}).get(template, {})
