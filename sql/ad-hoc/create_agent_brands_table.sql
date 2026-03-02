-- Create agent_brands table
CREATE TABLE IF NOT EXISTS agent_brands (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL UNIQUE REFERENCES agents(id) ON DELETE CASCADE,

    -- Brand Identity
    company_name VARCHAR(255),
    tagline VARCHAR(500),
    logo_url TEXT,
    website_url TEXT,

    -- About
    bio TEXT,
    about_us TEXT,
    specialties JSONB DEFAULT '[]'::jsonb,
    service_areas JSONB DEFAULT '[]'::jsonb,
    languages JSONB DEFAULT '[]'::jsonb,

    -- Brand Colors (5-color system)
    primary_color CHAR(7),
    secondary_color CHAR(7),
    accent_color CHAR(7),
    background_color CHAR(7),
    text_color CHAR(7),

    -- Contact Display
    display_phone VARCHAR(50),
    display_email VARCHAR(255),
    office_address TEXT,
    office_phone VARCHAR(50),

    -- Social Media
    social_media JSONB DEFAULT '{}'::jsonb,

    -- License Display
    license_display_name VARCHAR(255),
    license_number VARCHAR(100),
    license_states JSONB DEFAULT '[]'::jsonb,

    -- Privacy Settings
    show_profile BOOLEAN DEFAULT true,
    show_contact_info BOOLEAN DEFAULT true,
    show_social_media BOOLEAN DEFAULT true,

    -- Additional Brand Assets
    headshot_url TEXT,
    banner_url TEXT,
    company_badge_url TEXT,

    -- Email & Reports
    email_template_style VARCHAR(50) DEFAULT 'modern',
    report_logo_placement VARCHAR(50) DEFAULT 'top-left',

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    keywords JSONB DEFAULT '[]'::jsonb,

    -- Analytics
    google_analytics_id VARCHAR(50),
    facebook_pixel_id VARCHAR(50),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index on agent_id
CREATE INDEX IF NOT EXISTS idx_agent_brands_agent_id ON agent_brands(agent_id);

-- Create index on company_name
CREATE INDEX IF NOT EXISTS idx_agent_brands_company_name ON agent_brands(company_name);

-- Add comment
COMMENT ON TABLE agent_brands IS 'Agent brand profiles for marketing hub';
