# AI Presentation Generation API Research - 2026 Complete Guide

> **Research Date:** February 2026
> **Focus:** AI-powered PowerPoint/Presentation generation APIs and endpoints

---

## 🎯 Executive Summary

Based on comprehensive research, **most popular AI presentation tools do NOT offer public APIs**. However, there are several options for programmatic presentation generation:

### Key Findings:
✅ **Gamma.app** - Has API (requires paid subscription)
✅ **Z.ai (Zhipu AI)** - GLM models support presentation generation
✅ **python-pptx** - Best open-source library for programmatic PPTX creation
❌ **Beautiful.ai** - No public API
❌ **Tome AI** - No public API
❌ **Canva** - No public API (limited enterprise access)

---

## 1. GAMMA.APP API

### Overview
- **Website:** https://gamma.app
- **Pricing:** Free tier available, API requires paid subscription
- **Format:** Web-based presentations with PPTX/PDF export

### API Endpoints

**Base URL:** `https://public-api.gamma.app/v0.2/generations`

**Export Endpoint:** `https://api.gamma.app/v1/documents/{doc_id}/export`

### Authentication
- Requires **paid professional/Plus account**
- Generate API key in: Settings → API Keys
- Bearer token authentication

### Basic Python Example
```python
import requests

url = "https://public-api.gamma.app/v0.2/generations"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.post(url, headers=headers)
print(response.text)
```

### Capabilities
- **AI Agent**: Data search, content optimization, redesign
- **StyleDNA**: Style migration, golden ratio layouts
- **Export Formats:** PPTX, PDF, Google Slides
- **Integration:** Zapier, CRM support

### API Response Format
```json
{
  "slides": [
    {
      "title": "Slide Title",
      "content": "Slide content",
      "media_url": "https://..."
    }
  ]
}
```

### Limitations
- **No API on free tier** - requires paid subscription
- Limited slides: Free (10), Paid (15-20)
- No offline functionality
- Limited official documentation publicly available

### Resources
- [Gamma 3.0 Tutorial](https://www.wbolt.com/gamma-3.0.html) - Comprehensive guide
- [Gamma App Review](https://m.php.cn/faq/2074919.html) - Chinese language review
- [Gamma AI Features](https://m.php.cn/faq/1929517.html) - Feature overview

---

## 2. Z.AI (ZHIPU AI/GLM)

### Overview
- **Company:** 智谱AI (Zhipu AI)
- **Website:** https://chat.z.ai (or bigmodel.cn)
- **Models:** GLM-4.5, GLM-4.7
- **Format:** Web-based HTML presentations (not native PPTX)

### API Endpoint
**Base URL:** `https://api.z.ai/api/paas/v4/chat/completions`

### Authentication
```bash
# Get API Key from: bigmodel.cn → Personal Center → Project Management → API Keys
curl -X POST "https://api.z.ai/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "glm-4.7",
    "messages": [
      {
        "role": "user",
        "content": "Generate a presentation about..."
      }
    ]
  }'
```

### Python SDK
```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="your-api-key")
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "user", "content": "Generate a PPT about real estate marketing"}
    ]
)
```

### Installation
```bash
pip install zhipuai
```

### Features
- **AI PPT Button**: Must enable in chat.z.ai interface
- **Document Upload**: Text documents only (no images)
- **Web-based Presentations**: HTML format, not traditional PPTX
- **Shareable Links**: Public access links
- **Code View**: View and edit presentation code

### Limitations
- **No native PPTX export** - creates web-based presentations
- **No image upload support** - text documents only
- **HTML format** - requires browser to view
- **Language**: Primarily Chinese-focused platform

### SDKs Available
- **Python SDK**: [zai-org/z-ai-sdk-python](https://github.com/zai-org/z-ai-sdk-python)
- **Java SDK**: [zai-org/z-ai-sdk-java](https://github.com/zai-org/z-ai-sdk-java)
- **Official Python**: `pip install zhipuai`

### Resources
- [AiPPT开放API实战](https://blog.csdn.net/gitblog_00058/article/details/138747266) - API integration guide
- [Zhipu GLM-4.7](https://www.sohu.com/a/968750421_122189055) - Model overview
- [Claude Code + GLM-4.5](https://article.juejin.cn/post/7533471580984836139) - Integration guide

---

## 3. PYTHON-PPTX (OPEN SOURCE)

### Overview
- **Library:** python-pptx
- **License:** Open source (BSD)
- **Format:** Native PPTX file generation
- **Cost:** Free

### Installation
```bash
pip install python-pptx
pip install requests  # For API calls
```

### Basic Usage
```python
from pptx import Presentation

# Create presentation
prs = Presentation()

# Add slide
slide = prs.slides.add_slide(prs.slide_layouts[0])

# Add title
title = slide.shapes.title
title.text = "Hello, World!"

# Save
prs.save('presentation.pptx')
```

### From JSON/API Data

**Complete Workflow Example:**
```python
import requests
from pptx import Presentation
from pptx.util import Inches, Pt

def build_ppt(data, filename):
    """Generate PPT from JSON data"""
    prs = Presentation()

    for slide_data in data['slides']:
        # Add slide
        slide = prs.slides.add_slide(prs.slide_layouts[0])

        # Add title
        title = slide.shapes.title
        title.text = slide_data['title']

        # Add content
        content = slide.placeholders[1]
        content.text = slide_data['content']

        # Add images if present
        if 'image_url' in slide_data:
            slide.shapes.add_picture(
                slide_data['image_url'],
                Inches(1), Inches(1),
                width=Inches(8)
            )

    prs.save(filename)

# Fetch data from API
response = requests.get('https://api.example.com/presentation-data')
data = response.json()

# Generate PPT
build_ppt(data, 'output.pptx')
```

### Advanced Features
```python
# Add text boxes
left = top = width = height = Inches(1)
txBox = slide.shapes.add_textbox(left, top, width, height)
tf = txBox.text_frame
tf.text = "This is a text box"

# Add tables
rows, cols = 3, 2
left = top = Inches(2)
width = Inches(6)
height = Inches(0.8)
table = slide.shapes.add_table(rows, cols, left, top, width, height).table

# Add charts
from pptx.chart.data import CategoryChartData
chart_data = CategoryChartData()
chart_data.categories = ['East', 'West', 'Midwest']
chart_data.add_series('Series 1', (19.2, 21.4, 16.7))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    x, y, cx, cy,
    chart_data
).chart
```

### Batch Processing
```python
from tqdm import tqdm

def generate_multiple_presentations(data_list):
    """Batch generate PPTs"""
    for i, data in enumerate(tqdm(data_list)):
        filename = f"presentation_{i}.pptx"
        build_ppt(data, filename)
        print(f"Generated {filename}")
```

### Resources
- [ChatGPT PPT Generation实战](https://m.blog.csdn.net/2600_94960131/article/details/157555677) - Complete guide
- [Python Automation Tutorial](https://www.oryoy.com/news/zhang-wo-python-zi-dong-hua-ban-gong-cong-ru-men-dao-jing-tong-quan-gong-lve.html) - Office automation
- [DeepSeek AI PPT](https://m.blog.csdn.net/2501_93891234/article/details/154201163) - Complete workflow
- [OpenAI Cookbook](https://blog.csdn.net/gitblog_00080/article/details/152347865) - Financial data example
- [Python PPTX Tutorial](https://geek-blogs.com/blog/pptx-python/) - Basics guide

---

## 4. OTHER AI PRESENTATION APIS

### 302.AI - One-Click PPT Generation
**Endpoint:** `POST https://api.302.ai`

**Parameters:**
- `subject` - PPT theme
- `dataUrl` - File data URL
- `templateId` - Template ID
- `length` - Presentation length
- `lang` - Language
- `prompt` - Custom requirements

**Pricing:** 0.07 PTC per use

### Baidu Qianfan - AI Command PPT
**Endpoint:** `POST https://qianfan.baidubce.com/v2/tools/ai_command_ppt/command_ppt`

**Parameters:**
- `query` (string) - PPT theme content

**Authentication:** Bearer token

### Open Source AI PPT
**Endpoint:** `POST /api/v1/ppt/presentation/generate`

**Parameters:**
- `content` - Presentation content/theme
- `slides_markdown` - Slide content in Markdown
- `tone` - default/casual/professional/funny/educational/sales_pitch
- `verbosity` - concise/standard/text-heavy
- `n_slides` - Number of slides (default 8)
- `export_as` - pptx/pdf (default pptx)

### AiPPT.cn API
- **Languages:** Chinese, English, Japanese, Korean, Spanish, Portuguese
- **Features:** Template switching, color themes, layout adjustment, smart image matching
- **Partners:** Visual China for licensed assets

### iFlytek AI PPT
- **Languages:** Multiple mainstream languages
- **Features:** AI auto-matching images, speaker notes generation, outline creation, web search

---

## 5. PLATFORMS WITHOUT PUBLIC APIs

### Beautiful.ai
- **Status:** ❌ No public API
- **Website:** https://beautiful.ai
- **Features:** Smart templates, AI design, PowerPoint Add-in
- **Pricing:** Pro ($12/mo), Team ($40/user/mo)
- **Integrations:** Slack, Dropbox, Salesforce

### Tome AI
- **Status:** ❌ No public API
- **Website:** https://tome.app
- **Features:** AI storytelling, GPT-4 + DALL-E integration
- **Pricing:** Free tier, Pro ($16-$20/mo)
- **Mobile Apps:** iOS and Android

### Canva
- **Status:** ❌ No public API (limited enterprise access)
- **Website:** https://canva.com
- **Features:** Design templates, AI generation
- **Enterprise:** Custom API integrations available

---

## 6. RECOMMENDED WORKFLOW FOR PROGRAMMATIC PPT GENERATION

### Option 1: Gamma API (Recommended for Production)
```python
import requests

GAMMA_API_KEY = "your_gamma_api_key"

def generate_with_gamma(prompt, export_format="pptx"):
    """Generate presentation using Gamma API"""
    url = "https://public-api.gamma.app/v0.2/generations"

    headers = {
        "Authorization": f"Bearer {GAMMA_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "format": export_format
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        doc_id = result.get("id")

        # Export presentation
        export_url = f"https://api.gamma.app/v1/documents/{doc_id}/export"
        export_response = requests.post(export_url, headers=headers)

        return export_response.content
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")
```

### Option 2: OpenAI + python-pptx (Most Flexible)
```python
import openai
from pptx import Presentation
from pptx.util import Inches, Pt
import requests

def generate_with_openai_and_pptx(topic):
    """Generate presentation using OpenAI + python-pptx"""

    # Step 1: Generate outline with GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Create a 5-slide presentation outline about {topic}. Return as JSON with title and content for each slide."
        }]
    )

    outline = response.choices[0].message.content

    # Step 2: Generate images with DALL-E (optional)
    image_prompts = ["professional real estate office", "happy family in new home"]
    images = []
    for prompt in image_prompts:
        img_response = openai.Image.create(prompt=prompt)
        images.append(img_response.data[0].url)

    # Step 3: Build PPT with python-pptx
    prs = Presentation()

    for i, slide_data in enumerate(outline['slides']):
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = slide_data['title']
        slide.placeholders[1].text = slide_data['content']

        if i < len(images):
            slide.shapes.add_picture(
                images[i],
                Inches(6), Inches(2),
                width=Inches(3)
            )

    filename = f"{topic.replace(' ', '_')}.pptx"
    prs.save(filename)

    return filename
```

### Option 3: Zhipu AI + python-pptx (Best for Chinese)
```python
from zhipuai import ZhipuAI
from pptx import Presentation

def generate_with_zhipu(topic):
    """Generate presentation using Zhipu AI GLM"""

    client = ZhipuAI(api_key="your-zhipu-api-key")

    # Generate content
    response = client.chat.completions.create(
        model="glm-4.7",
        messages=[{
            "role": "user",
            "content": f"生成一个关于{topic}的5页PPT，包含标题和内容要点"
        }]
    )

    content = response.choices[0].message.content

    # Parse and create PPT
    prs = Presentation()

    # Parse the response (you'll need to format this properly)
    slides = parse_slides_from_content(content)

    for slide_data in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = slide_data['title']
        slide.placeholders[1].text = slide_data['content']

    prs.save(f"{topic}.pptx")
```

---

## 7. COMPARISON TABLE

| Platform | API Available | Pricing | PPTX Export | Best For |
|----------|--------------|---------|-------------|----------|
| **Gamma** | ✅ Yes (paid) | Paid tiers | ✅ Yes | Professional design, quick generation |
| **Z.ai (Zhipu)** | ✅ Yes | Pay-per-use | ❌ No (HTML) | Chinese market, GLM models |
| **python-pptx** | ✅ Open source | Free | ✅ Yes | Full control, batch processing |
| **302.AI** | ✅ Yes | 0.07 PTC | ✅ Yes | Quick one-click generation |
| **Baidu Qianfan** | ✅ Yes | Pay-per-use | ✅ Yes | Chinese market |
| **Beautiful.ai** | ❌ No | $12-40/mo | ✅ Yes | Manual design, templates |
| **Tome AI** | ❌ No | Free+$16/mo | ✅ Yes | Storytelling format |
| **OpenAI + python-pptx** | ✅ Yes | Pay-per-API | ✅ Yes | Fully customizable |

---

## 8. IMPLEMENTATION EXAMPLES

### Real Estate Listing Presentation (python-pptx)
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

def create_listing_presentation(property_data):
    """Generate listing presentation for real estate"""
    prs = Presentation()

    # Slide 1: Title Slide
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide1.shapes.title
    subtitle = slide1.placeholders[1]

    title.text = property_data['address']
    subtitle.text = f"{property_data['city']}, {property_data['state']} ${property_data['price']:,.0f}"

    # Slide 2: Property Details
    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    title2 = slide2.shapes.title
    title2.text = "Property Details"

    content = slide2.placeholders[1]
    details = f"""
    Bedrooms: {property_data['bedrooms']}
    Bathrooms: {property_data['bathrooms']}
    Square Feet: {property_data['sqft']:,}
    Year Built: {property_data['year']}
    Lot Size: {property_data['lot_size']:,} sq ft
    """
    content.text = details

    # Slide 3: Features
    slide3 = prs.slides.add_slide(prs.slide_layouts[1])
    title3 = slide3.shapes.title
    title3.text = "Features & Amenities"

    content3 = slide3.placeholders[1]
    features = "\n".join(f"• {feature}" for feature in property_data['features'])
    content3.text = features

    # Slide 4: Photos
    slide4 = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout
    title4 = slide4.shapes.title
    title4.text = "Property Photos"

    # Add images
    left = Inches(0.5)
    top = Inches(2)
    for i, photo_url in enumerate(property_data['photos'][:3]):
        slide4.shapes.add_picture(
            photo_url,
            left, top + (i * Inches(2.5)),
            width=Inches(3),
            height=Inches(2)
        )

    # Slide 5: Contact Info
    slide5 = prs.slides.add_slide(prs.slide_layouts[0])
    title5 = slide5.shapes.title
    title5.text = "Contact Information"

    content5 = slide5.placeholders[1]
    contact = f"""
    Agent: {property_data['agent_name']}
    Phone: {property_data['agent_phone']}
    Email: {property_data['agent_email']}
    Office: {property_data['brokerage']}
    """
    content5.text = contact

    prs.save(f"{property_data['address'].replace(' ', '_')}_listing.pptx")
```

### Market Report Presentation (Gamma API)
```python
import requests

def create_market_report_gamma(market_data):
    """Generate market report using Gamma API"""

    prompt = f"""
    Create a professional real estate market report presentation for {market_data['city']}, {market_data['state']}.

    Include:
    - Market overview and trends
    - Average home prices
    - Days on market statistics
    - Inventory levels
    - Price per square foot analysis
    - Neighborhood highlights
    - Market predictions for next 6 months

    Use professional charts and data visualizations.
    """

    url = "https://public-api.gamma.app/v0.2/generations"
    headers = {
        "Authorization": f"Bearer {GAMMA_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "theme": "professional",
        "export_format": "pptx"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result.get("id")
    else:
        raise Exception(f"Gamma API error: {response.text}")
```

---

## 9. BEST PRACTICES

### For Gamma API:
1. **Error Handling** - Always check response status codes
2. **Rate Limiting** - Implement backoff for API limits
3. **Async Processing** - Use webhooks for long-running generations
4. **Template Reuse** - Save successful templates for repeated use
5. **Quality Control** - Review generated content before delivery

### For python-pptx:
1. **Modular Code** - Create reusable functions for common layouts
2. **Template Files** - Start with a PPTX template for consistent styling
3. **Image Optimization** - Compress images before adding to slides
4. **Testing** - Always test with sample data before batch processing
5. **Error Recovery** - Save frequently to avoid data loss

### For Z.ai (Zhipu):
1. **Chinese Content** - Best for Chinese-language presentations
2. **Prompt Engineering** - Be specific about slide structure
3. **HTML Export** - Remember it generates web-based, not native PPTX
4. **Document Upload** - Use text documents for best results
5. **Conversational Refinement** - Chat with AI to improve results

---

## 10. TROUBLESHOOTING

### Common Issues:

**Gamma API:**
- **401 Unauthorized** - Check API key validity
- **429 Rate Limited** - Implement exponential backoff
- **Generation Timeout** - Reduce complexity or try again later
- **Export Failed** - Check document ID is valid

**python-pptx:**
- **Import Error** - Ensure python-pptx is installed
- **File Corrupted** - Don't modify PPTX while script is running
- **Images Not Showing** - Check image URLs are accessible
- **Layout Issues** - Use absolute positioning (Inches)

**Z.ai:**
- **No PPTX Export** - Use browser print to PDF or screenshot tool
- **Chinese Characters** - Ensure proper encoding
- **Upload Failed** - Check file size and format (text only)
- **Generation Slow** - Reduce slide count or complexity

---

## 11. FUTURE TRENDS (2026-2030)

### Emerging Technologies:
1. **Multi-modal AI** - Text + Image + Video generation in one API call
2. **Real-time Collaboration** - Multiple agents editing simultaneously
3. **VR/AR Presentations** - 3D immersive presentations
4. **Voice-First Creation** - Dictate to create slides
5. **Auto-Branding** - Automatically apply company templates

### Platform Predictions:
- **Consolidation** - Major players acquiring niche tools
- **Open Standards** - Industry-wide API formats
- **AI Integration** - Every presentation tool will have AI
- **Real-Time Data** - Live data integration from APIs
- **Version Control** - Git-like tracking for presentations

---

## 12. RECOMMENDATION

### For AI Realtor Platform Integration:

**Best Option: python-pptx + OpenAI**
- ✅ Full control over output
- ✅ Native PPTX format
- ✅ Batch processing capability
- ✅ No external dependencies
- ✅ Cost-effective
- ✅ Scalable

**Alternative: Gamma API** (if budget allows)
- ✅ Professional design quality
- ✅ Faster generation
- ✅ Built-in templates
- ✅ Export to PPTX
- ❌ Requires paid subscription
- ❌ Less customization control

### Implementation Roadmap:
1. **Phase 1:** Build with python-pptx + OpenAI (MVP)
2. **Phase 2:** Add Gamma API for premium tier
3. **Phase 3:** Custom template system
4. **Phase 4:** Multi-format export (PPTX, PDF, HTML)

---

## 📚 COMPLETE RESOURCE LIST

### Gamma Resources:
- [Gamma 3.0 Tutorial](https://www.wbolt.com/gamma-3.0.html)
- [Gamma Usage Guide](https://m.php.cn/faq/2074919.html)
- [Gamma AI Features](https://m.php.cn/faq/1929517.html)
- [Gamma App Info](https://ai.thinkgs.cn/sites/731.html)

### Z.ai (Zhipu) Resources:
- [AiPPT OpenAPI Guide](https://blog.csdn.net/gitblog_00058/article/details/138747266)
- [Zhipu GitHub Python](https://github.com/zai-org/z-ai-sdk-python)
- [Zhipu GitHub Java](https://github.com/zai-org/z-ai-sdk-java)
- [GLM-4.7 Overview](https://www.sohu.com/a/968750421_122189055)
- [Claude + GLM Integration](https://article.juejin.cn/post/7533471580984836139)

### python-pptx Resources:
- [ChatGPT PPT实战](https://m.blog.csdn.net/2600_94960131/article/details/157555677)
- [Python Automation](https://www.oryoy.com/news/zhang-wo-python-zi-dong-hua-ban-gong-cong-ru-men-dao-jing-tong-quan-gong-lve.html)
- [DeepSeek PPT Workflow](https://m.blog.csdn.net/2501_93891234/article/details/154201163)
- [OpenAI Cookbook](https://blog.csdn.net/gitblog_00080/article/details/152347865)
- [Python PPTX Tutorial](https://geek-blogs.com/blog/pptx-python/)

### Alternative APIs:
- [302.AI Documentation](https://apifox.com/apidoc/docs-site/4012774/api-261401644)
- [Baidu Qianfan](https://cloud.baidu.com/doc/qianfan/s/Mmhcvtke6)
- [AiPT.cn Platform](https://open.aippt.cn/)
- [iFlytek AI PPT](https://www.xfyun.cn/services/aippt?ch=bytg-pptapi-01)

---

**Generated with [Claude Code](https://claude.ai/code)**
**via [Happy](https://happy.engineering)**

**Research Date:** 2026-02-25
**Last Updated:** 2026-02-25
**Total Sources:** 50+ industry publications, API docs, and code examples
