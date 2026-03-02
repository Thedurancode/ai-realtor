-- Create Facebook Ads tables for Marketing Hub

-- Main campaigns table
CREATE TABLE IF NOT EXISTS facebook_campaigns (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL,

    -- Campaign details
    campaign_name VARCHAR(255) NOT NULL,
    campaign_objective VARCHAR(100) NOT NULL,
    campaign_status VARCHAR(50) DEFAULT 'draft',

    -- Targeting
    targeting_audience JSONB,
    targeting_custom_audiences JSONB,
    targeting_lookalike JSONB,

    -- Budget
    daily_budget FLOAT,
    lifetime_budget FLOAT,

    -- Schedule
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,

    -- Ad content
    ad_creatives JSONB,
    ad_copy JSONB,
    ad_format VARCHAR(50) DEFAULT 'single_image',

    -- Generation
    source_url VARCHAR(500),
    generated_by VARCHAR(50) DEFAULT 'ai',
    generation_model VARCHAR(100),

    -- Meta integration
    campaign_id_meta VARCHAR(100),
    meta_access_token VARCHAR(500),

    -- Metrics
    metrics JSONB,
    last_synced_at TIMESTAMP WITH TIME ZONE,

    -- Intelligence
    review_insights JSONB,
    sentiment_score FLOAT,
    key_phrases JSONB,
    competitor_analysis JSONB,
    competitor_spend_patterns JSONB,

    -- Auto-launch
    auto_launch BOOLEAN DEFAULT false,
    launch_config JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_facebook_campaigns_agent_id ON facebook_campaigns(agent_id);
CREATE INDEX IF NOT EXISTS ix_facebook_campaigns_property_id ON facebook_campaigns(property_id);
CREATE INDEX IF NOT EXISTS ix_facebook_campaigns_campaign_status ON facebook_campaigns(campaign_status);

COMMENT ON TABLE facebook_campaigns IS 'Facebook ad campaigns for agent marketing';

-- Ad sets table
CREATE TABLE IF NOT EXISTS facebook_ad_sets (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES facebook_campaigns(id) ON DELETE CASCADE,

    ad_set_name VARCHAR(255) NOT NULL,
    targeting JSONB,
    optimization_goal VARCHAR(100),
    billing_event VARCHAR(50),
    bid_strategy VARCHAR(50),
    daily_budget FLOAT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,

    ad_set_id_meta VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_facebook_ad_sets_campaign_id ON facebook_ad_sets(campaign_id);

COMMENT ON TABLE facebook_ad_sets IS 'Facebook ad sets for campaign organization';

-- Creatives table
CREATE TABLE IF NOT EXISTS facebook_creatives (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES facebook_campaigns(id) ON DELETE CASCADE,

    creative_name VARCHAR(255) NOT NULL,
    creative_format VARCHAR(50) NOT NULL,
    image_url VARCHAR(500),
    video_url VARCHAR(500),
    carousel_items JSONB,
    primary_text TEXT,
    headline VARCHAR(255),
    description VARCHAR(255),
    call_to_action VARCHAR(50),

    creative_id_meta VARCHAR(100),
    asset_spec JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_facebook_creatives_campaign_id ON facebook_creatives(campaign_id);

COMMENT ON TABLE facebook_creatives IS 'Facebook ad creative assets';

-- Ads table
CREATE TABLE IF NOT EXISTS facebook_ads (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES facebook_campaigns(id) ON DELETE CASCADE,
    ad_set_id INTEGER REFERENCES facebook_ad_sets(id) ON DELETE SET NULL,
    creative_id INTEGER REFERENCES facebook_creatives(id) ON DELETE SET NULL,

    ad_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    ad_id_meta VARCHAR(100),

    tracking_specs JSONB,
    adset_spec JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_facebook_ads_campaign_id ON facebook_ads(campaign_id);
CREATE INDEX IF NOT EXISTS ix_facebook_ads_ad_set_id ON facebook_ads(ad_set_id);

COMMENT ON TABLE facebook_ads IS 'Individual Facebook ads';

-- Audiences table
CREATE TABLE IF NOT EXISTS facebook_audiences (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    audience_name VARCHAR(255) NOT NULL,
    audience_type VARCHAR(50) NOT NULL, -- custom, lookalike, saved
    description TEXT,

    -- Audience definition
    targeting JSONB,
    source_audience_id VARCHAR(100), -- for lookalike
    lookalike_spec JSONB,

    -- Meta integration
    audience_id_meta VARCHAR(100),
    size_estimate INTEGER,

    -- Readiness
    ready_for_use BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_facebook_audiences_agent_id ON facebook_audiences(agent_id);

COMMENT ON TABLE facebook_audiences IS 'Facebook audience definitions for targeting';

-- Metrics table
CREATE TABLE IF NOT EXISTS facebook_ad_metrics (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES facebook_campaigns(id) ON DELETE CASCADE,
    ad_set_id INTEGER REFERENCES facebook_ad_sets(id) ON DELETE SET NULL,
    ad_id INTEGER REFERENCES facebook_ads(id) ON DELETE SET NULL,

    -- Date
    metrics_date DATE NOT NULL,

    -- Performance metrics
    impressions BIGINT DEFAULT 0,
    reach BIGINT DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    link_clicks INTEGER DEFAULT 0,
    engagements INTEGER DEFAULT 0,

    -- Conversion metrics
    conversions INTEGER DEFAULT 0,
    leads INTEGER DEFAULT 0,
    purchases INTEGER DEFAULT 0,

    -- Financial metrics
    spend FLOAT DEFAULT 0,
    cost_per_click FLOAT DEFAULT 0,
    cost_per_lead FLOAT DEFAULT 0,
    cost_per_conversion FLOAT DEFAULT 0,
    cost_per_thousand_impressions FLOAT DEFAULT 0,

    -- Rate metrics
    click_through_rate FLOAT,
    conversion_rate FLOAT,
    return_on_ad_spend FLOAT,

    -- Video metrics (if applicable)
    video_views INTEGER DEFAULT 0,
    video_watches_25_pct INTEGER DEFAULT 0,
    video_watches_50_pct INTEGER DEFAULT 0,
    video_watches_75_pct INTEGER DEFAULT 0,
    video_watches_100_pct INTEGER DEFAULT 0,

    -- Meta metadata
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, ad_set_id, ad_id, metrics_date)
);

CREATE INDEX IF NOT EXISTS ix_facebook_ad_metrics_campaign_id ON facebook_ad_metrics(campaign_id);
CREATE INDEX IF NOT EXISTS ix_facebook_ad_metrics_date ON facebook_ad_metrics(metrics_date);

COMMENT ON TABLE facebook_ad_metrics IS 'Facebook ad performance metrics over time';
