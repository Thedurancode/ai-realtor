# Signature Realty Brand - Setup Complete

## Brand Profile

**Company:** Signature Realty
**Tagline:** Your Dream Home Awaits
**Agent ID:** 3
**Brand ID:** 1

### Brand Identity (Luxury Gold Theme)

- **Primary Color:** `#B45309` (Deep gold/brown)
- **Secondary Color:** `#D97706` (Golden amber)
- **Accent Color:** `#F59E0B` (Bright gold)
- **Background Color:** `#FFFBEB` (Warm cream)
- **Text Color:** `#78350F` (Dark brown)

### Contact Information

- **Phone:** +1 (415) 555-1234
- **Email:** hello@signaturerealty.com
- **Office:** 123 Market Street, Suite 500, San Francisco, CA 94105
- **Office Phone:** +1 (415) 555-1000

### Online Presence

- **Website:** https://signaturerealty.com
- **Facebook:** https://facebook.com/signaturerealty
- **Instagram:** https://instagram.com/signaturerealty
- **LinkedIn:** https://linkedin.com/company/signaturerealty
- **Twitter:** https://twitter.com/signaturerealty

### Services

**Specialties:**
- Luxury Homes
- First-Time Buyers
- Investment Properties
- Relocation

**Service Areas:**
- San Francisco, CA
- Palo Alto, CA
- Mountain View, CA

**Languages:** English, Spanish

### License

- **Display Name:** Jane Doe - CA BRE #12345678
- **License Number:** CA-12345678
- **Licensed States:** California

### Brand Description

**Bio:**
Signature Realty specializes in luxury residential properties in the greater Bay Area. With over 15 years of experience, we help clients find their perfect home.

**About Us:**
Founded in 2010, Signature Realty has helped over 500 families find their dream homes. Our commitment to excellence and personalized service sets us apart.

### Analytics

- **Google Analytics ID:** UA-123456789-1
- **Facebook Pixel ID:** 1234567890

---

## API Endpoints

You can now use the Signature Realty brand with these endpoints:

### Brand Management

```bash
# View brand
GET /agent-brand/3

# Update brand
PUT /agent-brand/3

# Generate preview
POST /agent-brand/3/generate-preview

# Get public profile
GET /agent-brand/public/3

# Apply color preset
POST /agent-brand/3/apply-preset
```

### Facebook Ads

```bash
# Generate campaign
POST /facebook-ads/campaigns/generate?agent_id=3

Body:
{
  "url": "https://signaturerealty.com/properties/luxury-condo",
  "campaign_objective": "leads",
  "daily_budget": 100
}

# Launch to Meta
POST /facebook-ads/campaigns/{id}/launch

# Track performance
POST /facebook-ads/campaigns/{id}/track
```

### Social Media (Postiz)

```bash
# Create post
POST /postiz/posts/create?agent_id=3

Body:
{
  "content_type": "property_promo",
  "caption": "🏠 Stunning luxury condo in SF!",
  "hashtags": ["#luxuryliving", "#sf", "#realestate"],
  "platforms": ["facebook", "instagram", "linkedin"],
  "use_branding": true
}

# Create campaign
POST /postiz/campaigns/create?agent_id=3

Body:
{
  "campaign_name": "Property Launch Campaign",
  "platforms": ["facebook", "instagram"],
  "post_count": 10,
  "auto_generate": true
}
```

---

## Color Presets Available

If you want to change the color scheme, you can apply any of these presets:

1. **Professional Blue** - Trustworthy and corporate
2. **Modern Green** - Fresh and eco-friendly
3. **Luxury Gold** - Premium and high-end (currently applied)
4. **Bold Red** - Energetic and attention-grabbing
5. **Minimalist Black** - Sleek and modern
6. **Ocean Teal** - Calm and professional

```bash
POST /agent-brand/3/apply-preset
Body: { "preset_name": "Professional Blue" }
```

---

## Next Steps

1. **Update the logo** - Replace the placeholder logo URL with your actual logo
2. **Add headshot** - Upload agent headshot for personal branding
3. **Create campaigns** - Set up Facebook ads or social media campaigns
4. **Test preview** - Generate a preview to see how your brand looks

---

## Database Records

**Agent Table:**
- ID: 3
- Name: Jane Doe
- Email: jane@signaturerealty.com
- Phone: +14155551234
- License: CA-12345678

**Agent Brand Table:**
- ID: 1
- Agent ID: 3
- Company: Signature Realty
- Status: Active

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
