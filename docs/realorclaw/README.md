# 🦞 RealtorClaw

<div align="center">

![RealtorClaw Logo](https://img.shields.io/badge/OpenClaw-AI%20Realtor-blue?style=for-the-badge&logo=openai&logoColor=white)
![Version](https://img.shields.io/github/v/tag/Thedurancode/ai-realtor?label=version)
![License](https://img.shields.io/github/license/Thedurancode/ai-realtor)
![Stars](https://img.shields.io/github/stars/Thedurancode/ai-realtor?style=social)

**The Ultimate AI-Powered Real Estate Agent for OpenClaw**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration) • [API Reference](#-api-reference)

</div>

---

## 🎯 About

**RealtorClaw** is a powerful OpenClaw skill that brings the complete [AI Realtor](https://github.com/Thedurancode/ai-realtor) platform to your personal AI agent. Transform OpenClaw into a fully autonomous real estate assistant that can:

- 🏠 **Discover and manage properties** with natural language
- 📊 **Analyze deals** with investor-grade underwriting
- 📝 **Draft and negotiate offers** automatically
- ✍️ **Manage contracts** with AI-powered suggestions
- 📞 **Make phone calls** and handle communications
- 🤖 **Run agentic research** on any property
- 📈 **Track campaigns** and analytics

Built for real estate professionals, investors, and teams who want 24/7 autonomous real estate operations controlled entirely through OpenClaw.

---

## ✨ Features

### Property Management
- Create, list, update, and delete properties with voice commands
- Google Places address autocomplete
- Property enrichment with Zillow data (photos, Zestimates, tax history)
- Skip tracing to find owner contact information
- Voice-optimized property lookup (say the address, not IDs)

### Deal Analysis & Scoring
- Four investment strategies: Wholesale, Fix & Flip, Rental, BRRRR
- Automatic deal scoring (A-F grades)
- Side-by-side strategy comparison
- What-if scenario analysis
- MAO (Maximum Allowable Offer) calculation for wholesale deals

### Contract Management
- Three-tier requirement system: Auto-attach, AI Suggestions, Manual Override
- 15+ contract templates for NY, CA, FL, TX
- Multi-party e-signature via DocuSeal
- Real-time signing status via webhooks
- Smart signer detection by role (buyer, seller, attorney, etc.)

### Offer & Negotiation
- Create, counter, accept, reject, and withdraw offers
- Full negotiation chain tracking
- AI-drafted offer letters with negotiation strategy
- DocuSeal pre-fill for instant signatures
- Contingency tracking (inspection, financing, appraisal)

### Agentic Research
- 12+ parallel AI research workers
- Property profile, comparable sales/rentals
- Underwriting with ARV/rent/rehab estimates
- Neighborhood intelligence (crime, schools, market trends)
- Environmental hazard assessment (EPA, wildfire, seismic, wetlands)
- Evidence tracking with source URLs

### Phone Call Automation
- VAPI integration with GPT-4 Turbo
- ElevenLabs conversational AI with MCP tool access
- Voice campaigns with bulk outbound calling
- Call recording and transcription
- Contract reminder calls
- Skip trace outreach

### Compliance Engine
- AI-powered checks against federal (RESPA, TILA, Fair Housing) regulations
- State and local compliance rules
- Violation severity tracking (critical, high, medium, low)
- Claude-generated compliance summaries with remediation steps

### Advanced Features
- Semantic vector search with natural language queries
- AI property recaps (3 formats)
- PDF property reports with email delivery
- Real-time activity feed via WebSocket
- Todo management with priorities and deadlines
- Calendar integration with smart scheduling
- Direct mail campaigns (postcards, letters)
- Social media posting (Postiz integration)

---

## 🚀 Installation

### Prerequisites

- [OpenClaw](https://openclaw.ai/) installed and running
- AI Realtor API access (see [Configuration](#-configuration))
- Python 3.11+ (for optional custom skill development)

### Quick Install via OpenClaw CLI

```bash
# Install RealtorClaw skill
openclaw skill install Thedurancode/ai-realtor

# Restart OpenClaw gateway
openclaw gateway restart
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor/docs/realorclaw

# Copy skill to OpenClaw skills directory
mkdir -p ~/.openclaw/skills/realtorclaw
cp -r . ~/.openclaw/skills/realtorclaw/

# Verify installation
openclaw skill list | grep realtorclaw
```

---

## ⚙️ Configuration

### Environment Variables

Create or edit `~/.openclaw/skills/realtorclaw/.env`:

```bash
# AI Realtor API Configuration (Required)
AI_REALTOR_API_BASE_URL=http://ai-realtor.emprezario.com
AI_REALTOR_API_KEY=your_agent_api_key_here

# Optional: Model Selection
AI_REALTOR_DEFAULT_MODEL=claude-sonnet-4

# Optional: Response Language
AI_REALTOR_RESPONSE_LANGUAGE=en
```

### API Key Setup

1. **Get API Key from AI Realtor:**
   ```bash
   # Via AI Realtor dashboard
   # Or create programmatically:
   curl -X POST http://ai-realtor.emprezario.com/agents \
     -H "Content-Type: application/json" \
     -d '{"name": "RealtorClaw Agent"}'
   ```

2. **Configure in OpenClaw:**
   ```bash
   openclaw config set skills.ai-realtor.apiKey "your-api-key-here"
   openclaw config set skills.ai-realtor.baseUrl "http://ai-realtor.emprezario.com"
   ```

3. **Test connection:**
   ```bash
   openclaw skill test ai-realtor
   ```

---

## 💡 Usage

### Via OpenClaw (Recommended)

Once installed, RealtorClaw responds to natural language commands in any connected channel (Telegram, Discord, Slack, etc.):

```
# Property Management
"Create a property at 123 Main St, Brooklyn, NY for $850,000 with 2 bedrooms"
"Show me all available properties in Brooklyn"
"Enrich property 5 with Zillow data"

# Deal Analysis
"Calculate the deal for 123 Main St"
"Compare wholesale vs flip vs rental for property 8"
"What's the MAO for property 3?"

# Contracts
"What contracts are required for property 5?"
"Send the purchase agreement to John Smith"
"Check if property 12 is ready to close"

# Offers
"Submit an offer of $600K on property 3 with inspection contingency"
"Counter the $500K offer on property 7"
"Draft an offer letter for property 10"

# Research
"Run full agentic research on 456 Oak Ave"
"What's the neighborhood intel for property 8?"
"Show me the research dossier for 123 Main St"

# Phone Calls
"Call the owner of property 5 and ask if they want to sell"
"Make a contract reminder call to John at +14155551234"
"Create a voice campaign to call all buyers"

# Search
"Find me condos under $700K in Brooklyn with parking"
"Show me properties similar to the one at 789 Park Place"
"Search for properties with good school ratings"
```

### Via Direct API Calls

If you need more control, use the AI Realtor API directly:

```bash
# Create property
curl -X POST http://ai-realtor.emprezario.com/properties/voice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "address": "123 Main St, Brooklyn, NY 11201",
    "price": 850000,
    "bedrooms": 2,
    "bathrooms": 2,
    "property_type": "house",
    "description": "Beautiful 2BR/2BA in prime Park Slope location"
  }'

# Calculate deal
curl -X POST http://ai-realtor.emprezario.com/deal-calculator/voice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "address": "123 Main St, Brooklyn, NY 11201",
    "strategies": ["wholesale", "flip", "rental", "brrrr"]
  }'

# Run research
curl -X POST http://ai-realtor.emprezario.com/agentic-research/property/5/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "include_environmental": true,
    "include_historic": true
  }'
```

---

## 📖 API Reference

### Properties

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/properties/voice` | Create property with voice-optimized input |
| GET | `/properties/` | List properties with filtering |
| GET | `/properties/{id}` | Get property details |
| PATCH | `/properties/{id}` | Update property |
| DELETE | `/properties/{id}` | Delete property |
| POST | `/properties/{id}/enrich` | Enrich with Zillow data |
| POST | `/properties/{id}/skip-trace` | Find owner via skip trace |

### Deals & Calculator

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/deal-calculator/voice` | Calculate all strategies for property |
| POST | `/deal-calculator/compare` | Compare strategies side-by-side |
| GET | `/deal-calculator/property/{id}` | Quick calculation with defaults |
| POST | `/offers/` | Create offer |
| POST | `/offers/{id}/counter` | Counter offer |
| POST | `/offers/{id}/accept` | Accept offer |
| POST | `/offers/{id}/reject` | Reject offer |

### Contracts

| Method | Endpoint | Description |
|---------|-----------|-------------|
| GET | `/contracts/` | List all contracts |
| POST | `/contracts/` | Create contract |
| POST | `/contracts/{id}/send` | Send via DocuSeal |
| POST | `/contracts/property/{id}/ai-suggest` | Get AI contract suggestions |
| POST | `/contracts/property/{id}/ai-apply-suggestions` | Apply AI suggestions |
| GET | `/contracts/property/{id}/required-status` | Check contract readiness |
| GET | `/contracts/property/{id}/signing-status` | View who signed |

### Research

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/agentic-research/property/{id}/run` | Run full research pipeline |
| GET | `/agentic-research/property/{id}/status` | Get research status |
| POST | `/agentic-research/property/{id}/rerun-worker` | Rerun specific worker |
| GET | `/agentic-research/property/{id}/dossier` | Get research dossier |

### Phone Calls

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/property-recap/property/{id}/call` | Make VAPI phone call |
| POST | `/elevenlabs/call` | Make ElevenLabs call |
| POST | `/voice-campaigns/` | Create campaign |
| POST | `/voice-campaigns/{id}/start` | Start campaign |
| GET | `/voice-campaigns/{id}/analytics` | Get analytics |

### Search

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | `/search/properties` | Natural language search |
| GET | `/search/similar/{id}` | Find similar properties |
| POST | `/search/research` | Search dossiers and evidence |

For complete API documentation, visit: [http://ai-realtor.emprezario.com/docs](http://ai-realtor.emprezario.com/docs)

---

## 🤝 Troubleshooting

### Common Issues

**Issue: Skill not loading in OpenClaw**
```bash
# Check skill installation
openclaw skill list

# Reinstall if needed
openclaw skill uninstall ai-realtor
openclaw skill install Thedurancode/ai-realtor
```

**Issue: API connection errors**
```bash
# Verify API configuration
openclaw config show skills.ai-realtor

# Test connection
curl http://ai-realtor.emprezario.com/health

# Check API key validity
curl -X POST http://ai-realtor.emprezario.com/properties/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json"
```

**Issue: Slow response times**
- Check AI Realtor server performance
- Verify network connectivity
- Consider enabling caching: `ENABLE_CACHE=true`

**Issue: Voice call not connecting**
- Verify VAPI/ElevenLabs API keys
- Check phone number configuration
- Review OpenClaw logs: `openclaw logs`

### Getting Help

- 📖 [Documentation](http://ai-realtor.emprezario.com/docs)
- 💬 [Discord](https://discord.gg/clawd)
- 🐛 [GitHub Issues](https://github.com/Thedurancode/ai-realtor/issues)
- 📧 [Email Support](mailto:support@ai-realtor.com)

---

## 📊 Roadmap

### v1.1.0 (Planned Q2 2026)
- [ ] Multi-agent collaboration (team support)
- [ ] Advanced workflow engine
- [ ] MLS integration
- [ ] Automated property valuation
- [ ] Mobile app support

### v1.2.0 (Planned Q3 2026)
- [ ] Predictive analytics
- [ ] Market trend analysis
- [ ] Investment portfolio management
- [ ] Smart contract negotiation
- [ ] Video property tours

### v2.0.0 (Planned Q4 2026)
- [ ] Complete MLS replacement
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] Document AI analysis
- [ ] Voice recognition improvements
- [ ] Enterprise features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

```
MIT License

Copyright (c) 2026 AI Realtor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- [AI Realtor](https://github.com/Thedurancode/ai-realtor) - Core platform
- [OpenClaw](https://github.com/openclaw/openclaw) - Agent framework
- [Anthropic Claude](https://www.anthropic.com) - LLM provider
- [VAPI](https://vapi.ai/) - Voice AI integration
- [ElevenLabs](https://elevenlabs.io/) - Text-to-speech
- [DocuSeal](https://www.docuseal.com/) - E-signature platform

---

## 📞 Contact & Support

- **Website:** [ai-realtor.emprezario.com](http://ai-realtor.emprezario.com)
- **Documentation:** [ai-realtor.emprezario.com/docs](http://ai-realtor.emprezario.com/docs)
- **GitHub:** [github.com/Thedurancode/ai-realtor](https://github.com/Thedurancode/ai-realtor)
- **Email:** [support@ai-realtor.com](mailto:support@ai-realtor.com)
- **Discord:** [OpenClaw Community](https://discord.gg/clawd)

---

<div align="center">

**Built with ❤️ by the AI Realtor Team**

[⭐ Star us on GitHub!](https://github.com/Thedurancode/ai-realtor)
[🐛 Report a bug](https://github.com/Thedurancode/ai-realtor/issues)
[💡 Suggest a feature](https://github.com/Thedurancode/ai-realtor/issues)

[![Built with OpenClaw](https://img.shields.io/badge/Built%20with-OpenClaw-red?style=for-the-badge)](https://openclaw.ai/)

</div>
