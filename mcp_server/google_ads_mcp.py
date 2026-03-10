"""
Google Ads Management MCP Server — Full CRUD.
Create campaigns, ad groups, ads, keywords, budgets, targeting, reporting.
Uses the Google Ads API v17 via google-ads Python client.
"""
import os
import json
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

app = Server("google-ads")

# ─── Config ───────────────────────────────────────────────────
DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")


def _ok(data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


def _get_client():
    """Get authenticated Google Ads client."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        return None, "google-ads package not installed. Run: pip install google-ads"

    if not DEVELOPER_TOKEN or not CLIENT_ID or not REFRESH_TOKEN:
        return None, "Google Ads credentials not configured. Set GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET, GOOGLE_ADS_REFRESH_TOKEN"

    config = {
        "developer_token": DEVELOPER_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "use_proto_plus": True,
    }
    if LOGIN_CUSTOMER_ID:
        config["login_customer_id"] = LOGIN_CUSTOMER_ID

    client = GoogleAdsClient.load_from_dict(config)
    return client, None


def _cid(args: dict) -> str:
    """Get customer ID from args or default."""
    return str(args.get("customer_id", CUSTOMER_ID)).replace("-", "")


# ─── Account ──────────────────────────────────────────────────

async def _list_accounts(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    accounts = [r for r in response.resource_names]
    return _ok({"accounts": accounts, "count": len(accounts)})


async def _account_info(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT customer.id, customer.descriptive_name, customer.currency_code,
               customer.time_zone, customer.manager
        FROM customer LIMIT 1
    """
    response = ga_service.search(customer_id=cid, query=query)
    for row in response:
        c = row.customer
        return _ok({"id": c.id, "name": c.descriptive_name,
                     "currency": c.currency_code, "timezone": c.time_zone,
                     "is_manager": c.manager})
    return _err("No account data found")


# ─── GAQL Query ───────────────────────────────────────────────

async def _run_query(args: dict) -> list[TextContent]:
    """Run any GAQL query against Google Ads."""
    client, err = _get_client()
    if err:
        return _err(err)
    query = args.get("query", "")
    if not query:
        return _err("query is required")
    cid = _cid(args)
    ga_service = client.get_service("GoogleAdsService")
    try:
        response = ga_service.search(customer_id=cid, query=query)
        results = []
        for row in response:
            results.append(str(row))
        return _ok({"query": query, "results": results, "count": len(results)})
    except Exception as ex:
        return _err(f"GAQL error: {ex}")


# ─── Campaigns ────────────────────────────────────────────────

async def _list_campaigns(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ga_service = client.get_service("GoogleAdsService")
    status_filter = args.get("status", "")
    query = """
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.advertising_channel_type, campaign.bidding_strategy_type,
               campaign_budget.amount_micros,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.conversions, metrics.ctr, metrics.average_cpc
        FROM campaign
    """
    VALID_STATUSES = {"ENABLED", "PAUSED", "REMOVED"}
    if status_filter:
        status_val = status_filter.upper()
        if status_val not in VALID_STATUSES:
            return _err(f"Invalid status_filter. Must be one of: {', '.join(VALID_STATUSES)}")
        query += f" WHERE campaign.status = '{status_val}'"
    query += " ORDER BY metrics.cost_micros DESC LIMIT 50"

    response = ga_service.search(customer_id=cid, query=query)
    campaigns = []
    for row in response:
        c = row.campaign
        m = row.metrics
        b = row.campaign_budget
        campaigns.append({
            "id": c.id, "name": c.name, "status": c.status.name,
            "channel": c.advertising_channel_type.name,
            "bidding": c.bidding_strategy_type.name,
            "budget_daily": b.amount_micros / 1_000_000 if b.amount_micros else 0,
            "impressions": m.impressions, "clicks": m.clicks,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "ctr": round(m.ctr * 100, 2), "avg_cpc": m.average_cpc / 1_000_000,
        })
    return _ok({"campaigns": campaigns, "count": len(campaigns)})


async def _create_campaign(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    name = args.get("name", "")
    budget_amount = args.get("daily_budget", 0)
    channel = args.get("channel_type", "SEARCH").upper()
    bidding = args.get("bidding_strategy", "MAXIMIZE_CLICKS").upper()

    if not name or not budget_amount:
        return _err("name and daily_budget are required")

    # Create budget
    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"{name} Budget"
    budget.amount_micros = int(float(budget_amount) * 1_000_000)
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

    budget_response = budget_service.mutate_campaign_budgets(
        customer_id=cid, operations=[budget_op]
    )
    budget_resource = budget_response.results[0].resource_name

    # Create campaign
    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.create
    campaign.name = name
    campaign.campaign_budget = budget_resource
    campaign.status = client.enums.CampaignStatusEnum.PAUSED  # Always start paused for safety

    # Set channel type
    channel_enum = client.enums.AdvertisingChannelTypeEnum
    channel_map = {
        "SEARCH": channel_enum.SEARCH,
        "DISPLAY": channel_enum.DISPLAY,
        "SHOPPING": channel_enum.SHOPPING,
        "VIDEO": channel_enum.VIDEO,
        "PERFORMANCE_MAX": channel_enum.PERFORMANCE_MAX,
    }
    campaign.advertising_channel_type = channel_map.get(channel, channel_enum.SEARCH)

    # Set bidding
    if bidding == "MAXIMIZE_CLICKS":
        campaign.maximize_clicks.cpc_bid_ceiling_micros = 0
    elif bidding == "MAXIMIZE_CONVERSIONS":
        campaign.maximize_conversions.target_cpa_micros = 0
    elif bidding == "TARGET_CPA":
        target_cpa = args.get("target_cpa", 10)
        campaign.target_cpa.target_cpa_micros = int(float(target_cpa) * 1_000_000)
    elif bidding == "TARGET_ROAS":
        target_roas = args.get("target_roas", 4.0)
        campaign.target_roas.target_roas = float(target_roas)
    elif bidding == "MANUAL_CPC":
        campaign.manual_cpc.enhanced_cpc_enabled = True

    # Network settings for Search
    if channel == "SEARCH":
        campaign.network_settings.target_google_search = True
        campaign.network_settings.target_search_network = True

    response = campaign_service.mutate_campaigns(
        customer_id=cid, operations=[campaign_op]
    )
    return _ok({
        "status": "created",
        "campaign": response.results[0].resource_name,
        "name": name,
        "state": "PAUSED (enable with update_campaign)",
        "daily_budget": budget_amount,
        "channel": channel,
        "bidding": bidding,
    })


async def _update_campaign(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    if not campaign_id:
        return _err("campaign_id is required")

    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.update
    campaign.resource_name = campaign_service.campaign_path(cid, campaign_id)

    field_mask = []
    if "name" in args:
        campaign.name = args["name"]
        field_mask.append("name")
    if "status" in args:
        status_map = {
            "ENABLED": client.enums.CampaignStatusEnum.ENABLED,
            "PAUSED": client.enums.CampaignStatusEnum.PAUSED,
            "REMOVED": client.enums.CampaignStatusEnum.REMOVED,
        }
        campaign.status = status_map.get(args["status"].upper(), client.enums.CampaignStatusEnum.PAUSED)
        field_mask.append("status")

    if not field_mask:
        return _err("Nothing to update. Provide name or status.")

    from google.api_core import protobuf_helpers
    client.copy_from(campaign_op.update_mask, protobuf_helpers.field_mask(None, campaign))

    response = campaign_service.mutate_campaigns(
        customer_id=cid, operations=[campaign_op]
    )
    return _ok({"status": "updated", "campaign": response.results[0].resource_name, "changes": field_mask})


async def _delete_campaign(args: dict) -> list[TextContent]:
    """Sets campaign status to REMOVED (Google Ads doesn't truly delete)."""
    args["status"] = "REMOVED"
    return await _update_campaign(args)


# ─── Ad Groups ────────────────────────────────────────────────

async def _list_ad_groups(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT ad_group.id, ad_group.name, ad_group.status,
               ad_group.cpc_bid_micros, campaign.id, campaign.name,
               metrics.impressions, metrics.clicks, metrics.cost_micros
        FROM ad_group
    """
    if campaign_id:
        if not str(campaign_id).isdigit():
            return _err("campaign_id must be numeric")
        query += f" WHERE campaign.id = {int(campaign_id)}"
    query += " ORDER BY metrics.cost_micros DESC LIMIT 50"

    response = ga_service.search(customer_id=cid, query=query)
    groups = []
    for row in response:
        ag = row.ad_group
        m = row.metrics
        groups.append({
            "id": ag.id, "name": ag.name, "status": ag.status.name,
            "cpc_bid": ag.cpc_bid_micros / 1_000_000 if ag.cpc_bid_micros else 0,
            "campaign_id": row.campaign.id, "campaign_name": row.campaign.name,
            "impressions": m.impressions, "clicks": m.clicks,
            "cost": m.cost_micros / 1_000_000,
        })
    return _ok({"ad_groups": groups, "count": len(groups)})


async def _create_ad_group(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    name = args.get("name", "")
    cpc_bid = args.get("cpc_bid", 1.0)

    if not campaign_id or not name:
        return _err("campaign_id and name are required")

    campaign_service = client.get_service("CampaignService")
    ad_group_service = client.get_service("AdGroupService")
    ad_group_op = client.get_type("AdGroupOperation")
    ag = ad_group_op.create
    ag.name = name
    ag.campaign = campaign_service.campaign_path(cid, campaign_id)
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ag.cpc_bid_micros = int(float(cpc_bid) * 1_000_000)

    response = ad_group_service.mutate_ad_groups(
        customer_id=cid, operations=[ad_group_op]
    )
    return _ok({"status": "created", "ad_group": response.results[0].resource_name,
                "name": name, "cpc_bid": cpc_bid})


async def _update_ad_group(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ad_group_id = args.get("ad_group_id", "")
    if not ad_group_id:
        return _err("ad_group_id is required")

    ad_group_service = client.get_service("AdGroupService")
    ad_group_op = client.get_type("AdGroupOperation")
    ag = ad_group_op.update
    ag.resource_name = ad_group_service.ad_group_path(cid, ad_group_id)

    field_mask = []
    if "name" in args:
        ag.name = args["name"]
        field_mask.append("name")
    if "status" in args:
        status_map = {"ENABLED": client.enums.AdGroupStatusEnum.ENABLED,
                      "PAUSED": client.enums.AdGroupStatusEnum.PAUSED,
                      "REMOVED": client.enums.AdGroupStatusEnum.REMOVED}
        ag.status = status_map.get(args["status"].upper())
        field_mask.append("status")
    if "cpc_bid" in args:
        ag.cpc_bid_micros = int(float(args["cpc_bid"]) * 1_000_000)
        field_mask.append("cpc_bid_micros")

    if not field_mask:
        return _err("Nothing to update")

    from google.api_core import protobuf_helpers
    client.copy_from(ad_group_op.update_mask, protobuf_helpers.field_mask(None, ag))

    response = ad_group_service.mutate_ad_groups(
        customer_id=cid, operations=[ad_group_op]
    )
    return _ok({"status": "updated", "ad_group": response.results[0].resource_name, "changes": field_mask})


# ─── Ads ──────────────────────────────────────────────────────

async def _list_ads(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.final_urls,
               ad_group.id, ad_group.name, campaign.id,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.conversions, metrics.ctr
        FROM ad_group_ad
    """
    campaign_id = args.get("campaign_id", "")
    ad_group_id = args.get("ad_group_id", "")
    if campaign_id:
        if not str(campaign_id).isdigit():
            return _err("campaign_id must be numeric")
        query += f" WHERE campaign.id = {int(campaign_id)}"
    elif ad_group_id:
        if not str(ad_group_id).isdigit():
            return _err("ad_group_id must be numeric")
        query += f" WHERE ad_group.id = {int(ad_group_id)}"
    query += " ORDER BY metrics.impressions DESC LIMIT 50"

    response = ga_service.search(customer_id=cid, query=query)
    ads = []
    for row in response:
        ad = row.ad_group_ad.ad
        m = row.metrics
        headlines = [h.text for h in ad.responsive_search_ad.headlines] if ad.responsive_search_ad.headlines else []
        descriptions = [d.text for d in ad.responsive_search_ad.descriptions] if ad.responsive_search_ad.descriptions else []
        ads.append({
            "id": ad.id, "status": row.ad_group_ad.status.name,
            "headlines": headlines, "descriptions": descriptions,
            "final_urls": list(ad.final_urls),
            "ad_group_id": row.ad_group.id, "campaign_id": row.campaign.id,
            "impressions": m.impressions, "clicks": m.clicks,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "ctr": round(m.ctr * 100, 2),
        })
    return _ok({"ads": ads, "count": len(ads)})


async def _create_responsive_search_ad(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ad_group_id = args.get("ad_group_id", "")
    headlines = args.get("headlines", [])
    descriptions = args.get("descriptions", [])
    final_url = args.get("final_url", "")

    if not ad_group_id or not headlines or not descriptions or not final_url:
        return _err("ad_group_id, headlines (3-15), descriptions (2-4), and final_url are required")

    ad_group_service = client.get_service("AdGroupService")
    ad_group_ad_service = client.get_service("AdGroupAdService")
    ad_group_ad_op = client.get_type("AdGroupAdOperation")
    aga = ad_group_ad_op.create
    aga.ad_group = ad_group_service.ad_group_path(cid, ad_group_id)
    aga.status = client.enums.AdGroupAdStatusEnum.PAUSED  # Start paused for review

    ad = aga.ad
    ad.final_urls.append(final_url)

    if args.get("path1"):
        ad.responsive_search_ad.path1 = args["path1"]
    if args.get("path2"):
        ad.responsive_search_ad.path2 = args["path2"]

    for h in headlines[:15]:
        headline = client.get_type("AdTextAsset")
        headline.text = h
        ad.responsive_search_ad.headlines.append(headline)

    for d in descriptions[:4]:
        desc = client.get_type("AdTextAsset")
        desc.text = d
        ad.responsive_search_ad.descriptions.append(desc)

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=cid, operations=[ad_group_ad_op]
    )
    return _ok({
        "status": "created",
        "ad": response.results[0].resource_name,
        "state": "PAUSED (enable with update_ad)",
        "headlines": headlines[:15],
        "descriptions": descriptions[:4],
        "final_url": final_url,
    })


async def _update_ad(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ad_group_id = args.get("ad_group_id", "")
    ad_id = args.get("ad_id", "")
    status = args.get("status", "")
    if not ad_group_id or not ad_id or not status:
        return _err("ad_group_id, ad_id, and status are required")

    ad_group_ad_service = client.get_service("AdGroupAdService")
    ad_group_ad_op = client.get_type("AdGroupAdOperation")
    aga = ad_group_ad_op.update
    aga.resource_name = ad_group_ad_service.ad_group_ad_path(cid, ad_group_id, ad_id)

    status_map = {"ENABLED": client.enums.AdGroupAdStatusEnum.ENABLED,
                  "PAUSED": client.enums.AdGroupAdStatusEnum.PAUSED,
                  "REMOVED": client.enums.AdGroupAdStatusEnum.REMOVED}
    aga.status = status_map.get(status.upper(), client.enums.AdGroupAdStatusEnum.PAUSED)

    from google.api_core import protobuf_helpers
    client.copy_from(ad_group_ad_op.update_mask, protobuf_helpers.field_mask(None, aga))

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=cid, operations=[ad_group_ad_op]
    )
    return _ok({"status": "updated", "ad": response.results[0].resource_name, "new_status": status})


# ─── Keywords ─────────────────────────────────────────────────

async def _list_keywords(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status, ad_group_criterion.quality_info.quality_score,
               ad_group.id, ad_group.name, campaign.id,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.conversions, metrics.ctr, metrics.average_cpc
        FROM keyword_view
    """
    ad_group_id = args.get("ad_group_id", "")
    campaign_id = args.get("campaign_id", "")
    if ad_group_id:
        if not str(ad_group_id).isdigit():
            return _err("ad_group_id must be numeric")
        query += f" WHERE ad_group.id = {int(ad_group_id)}"
    elif campaign_id:
        if not str(campaign_id).isdigit():
            return _err("campaign_id must be numeric")
        query += f" WHERE campaign.id = {int(campaign_id)}"
    query += " ORDER BY metrics.impressions DESC LIMIT 100"

    response = ga_service.search(customer_id=cid, query=query)
    keywords = []
    for row in response:
        kw = row.ad_group_criterion
        m = row.metrics
        keywords.append({
            "text": kw.keyword.text, "match_type": kw.keyword.match_type.name,
            "status": kw.status.name,
            "quality_score": kw.quality_info.quality_score if kw.quality_info.quality_score else None,
            "ad_group_id": row.ad_group.id, "campaign_id": row.campaign.id,
            "impressions": m.impressions, "clicks": m.clicks,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "ctr": round(m.ctr * 100, 2), "avg_cpc": m.average_cpc / 1_000_000,
        })
    return _ok({"keywords": keywords, "count": len(keywords)})


async def _add_keywords(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    ad_group_id = args.get("ad_group_id", "")
    keywords = args.get("keywords", [])
    match_type = args.get("match_type", "PHRASE").upper()

    if not ad_group_id or not keywords:
        return _err("ad_group_id and keywords list are required")

    ad_group_service = client.get_service("AdGroupService")
    criterion_service = client.get_service("AdGroupCriterionService")

    match_map = {
        "EXACT": client.enums.KeywordMatchTypeEnum.EXACT,
        "PHRASE": client.enums.KeywordMatchTypeEnum.PHRASE,
        "BROAD": client.enums.KeywordMatchTypeEnum.BROAD,
    }

    operations = []
    for kw_text in keywords:
        op = client.get_type("AdGroupCriterionOperation")
        criterion = op.create
        criterion.ad_group = ad_group_service.ad_group_path(cid, ad_group_id)
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = kw_text
        criterion.keyword.match_type = match_map.get(match_type, client.enums.KeywordMatchTypeEnum.PHRASE)
        operations.append(op)

    response = criterion_service.mutate_ad_group_criteria(
        customer_id=cid, operations=operations
    )
    return _ok({
        "status": "added",
        "keywords_added": len(response.results),
        "keywords": keywords,
        "match_type": match_type,
        "ad_group_id": ad_group_id,
    })


async def _add_negative_keywords(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    keywords = args.get("keywords", [])

    if not campaign_id or not keywords:
        return _err("campaign_id and keywords list are required")

    campaign_service = client.get_service("CampaignService")
    criterion_service = client.get_service("CampaignCriterionService")

    operations = []
    for kw_text in keywords:
        op = client.get_type("CampaignCriterionOperation")
        criterion = op.create
        criterion.campaign = campaign_service.campaign_path(cid, campaign_id)
        criterion.negative = True
        criterion.keyword.text = kw_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.EXACT
        operations.append(op)

    response = criterion_service.mutate_campaign_criteria(
        customer_id=cid, operations=operations
    )
    return _ok({"status": "added", "negative_keywords_added": len(response.results),
                "keywords": keywords, "campaign_id": campaign_id})


# ─── Targeting ────────────────────────────────────────────────

async def _set_location_targeting(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    location_ids = args.get("location_ids", [])

    if not campaign_id or not location_ids:
        return _err("campaign_id and location_ids are required. Use geo target constants (e.g., 1014221 for NJ)")

    campaign_service = client.get_service("CampaignService")
    criterion_service = client.get_service("CampaignCriterionService")
    geo_service = client.get_service("GeoTargetConstantService")

    operations = []
    for loc_id in location_ids:
        op = client.get_type("CampaignCriterionOperation")
        criterion = op.create
        criterion.campaign = campaign_service.campaign_path(cid, campaign_id)
        criterion.location.geo_target_constant = geo_service.geo_target_constant_path(loc_id)
        operations.append(op)

    response = criterion_service.mutate_campaign_criteria(
        customer_id=cid, operations=operations
    )
    return _ok({"status": "targeting_set", "locations_added": len(response.results),
                "campaign_id": campaign_id})


async def _search_locations(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    query = args.get("query", "")
    if not query:
        return _err("query is required (e.g., 'New Jersey', 'Bergen County')")

    geo_service = client.get_service("GeoTargetConstantService")
    req = client.get_type("SuggestGeoTargetConstantsRequest")
    req.locale = "en"
    req.country_code = "US"
    req.location_names.names.append(query)

    response = geo_service.suggest_geo_target_constants(request=req)
    locations = []
    for suggestion in response.geo_target_constant_suggestions:
        geo = suggestion.geo_target_constant
        locations.append({
            "id": geo.id, "name": geo.name,
            "canonical_name": geo.canonical_name,
            "target_type": geo.target_type,
        })
    return _ok({"locations": locations, "count": len(locations)})


# ─── Budget ───────────────────────────────────────────────────

async def _update_budget(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    campaign_id = args.get("campaign_id", "")
    new_budget = args.get("daily_budget", 0)

    if not campaign_id or not new_budget:
        return _err("campaign_id and daily_budget are required")

    # First get the budget resource name
    ga_service = client.get_service("GoogleAdsService")
    if not str(campaign_id).isdigit():
        return _err("campaign_id must be numeric")
    query = f"SELECT campaign.campaign_budget FROM campaign WHERE campaign.id = {int(campaign_id)}"
    response = ga_service.search(customer_id=cid, query=query)
    budget_resource = None
    for row in response:
        budget_resource = row.campaign.campaign_budget

    if not budget_resource:
        return _err(f"Campaign {campaign_id} not found")

    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.update
    budget.resource_name = budget_resource
    budget.amount_micros = int(float(new_budget) * 1_000_000)

    from google.api_core import protobuf_helpers
    client.copy_from(budget_op.update_mask, protobuf_helpers.field_mask(None, budget))

    result = budget_service.mutate_campaign_budgets(
        customer_id=cid, operations=[budget_op]
    )
    return _ok({"status": "budget_updated", "campaign_id": campaign_id,
                "new_daily_budget": new_budget})


# ─── Reporting ────────────────────────────────────────────────

async def _performance_report(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    date_range = args.get("date_range", "LAST_30_DAYS")
    level = args.get("level", "campaign").lower()

    if level == "campaign":
        query = f"""
            SELECT campaign.id, campaign.name, campaign.status,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.conversion_value,
                   metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion
            FROM campaign
            WHERE segments.date DURING {date_range}
              AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """
    elif level == "ad_group":
        query = f"""
            SELECT ad_group.id, ad_group.name, campaign.name,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.ctr, metrics.average_cpc
            FROM ad_group
            WHERE segments.date DURING {date_range}
            ORDER BY metrics.cost_micros DESC LIMIT 50
        """
    elif level == "keyword":
        query = f"""
            SELECT ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.quality_info.quality_score,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.ctr, metrics.average_cpc
            FROM keyword_view
            WHERE segments.date DURING {date_range}
            ORDER BY metrics.cost_micros DESC LIMIT 50
        """
    elif level == "search_term":
        query = f"""
            SELECT search_term_view.search_term, campaign.name, ad_group.name,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.ctr
            FROM search_term_view
            WHERE segments.date DURING {date_range}
            ORDER BY metrics.impressions DESC LIMIT 50
        """
    else:
        return _err("level must be: campaign, ad_group, keyword, or search_term")

    ga_service = client.get_service("GoogleAdsService")
    response = ga_service.search(customer_id=cid, query=query)
    results = []
    for row in response:
        results.append(str(row))
    return _ok({"report": level, "date_range": date_range, "rows": results, "count": len(results)})


async def _daily_spend(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    cid = _cid(args)
    days = args.get("days", 30)
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT segments.date, metrics.impressions, metrics.clicks,
               metrics.cost_micros, metrics.conversions, metrics.ctr
        FROM customer
        WHERE segments.date DURING LAST_{days}_DAYS
        ORDER BY segments.date DESC
    """
    response = ga_service.search(customer_id=cid, query=query)
    rows = []
    for row in response:
        rows.append({
            "date": str(row.segments.date),
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": row.metrics.cost_micros / 1_000_000,
            "conversions": row.metrics.conversions,
            "ctr": round(row.metrics.ctr * 100, 2),
        })
    return _ok({"daily_spend": rows, "days": len(rows)})


# ─── Check Connection ────────────────────────────────────────

async def _check_connection(args: dict) -> list[TextContent]:
    client, err = _get_client()
    if err:
        return _err(err)
    return _ok({"status": "connected", "customer_id": CUSTOMER_ID,
                "login_customer_id": LOGIN_CUSTOMER_ID or "not set"})


# ─── Tool Definitions ────────────────────────────────────────

def _t(name, desc, props, req=None):
    schema = {"type": "object", "properties": props}
    if req:
        schema["required"] = req
    return Tool(name=name, description=desc, inputSchema=schema)

_cid_prop = {"customer_id": {"type": "string", "description": "Google Ads customer ID (optional, uses default)"}}

TOOLS = [
    # Account
    _t("gads_list_accounts", "List all accessible Google Ads accounts", {}),
    _t("gads_account_info", "Get account details (name, currency, timezone)", _cid_prop),
    _t("gads_check_connection", "Verify Google Ads connection is working", {}),

    # GAQL
    _t("gads_query", "Run any GAQL query against Google Ads", {
        **_cid_prop, "query": {"type": "string", "description": "GAQL query string"}
    }, ["query"]),

    # Campaigns
    _t("gads_list_campaigns", "List all campaigns with performance metrics", {
        **_cid_prop, "status": {"type": "string", "enum": ["ENABLED", "PAUSED", "REMOVED"], "description": "Filter by status"}
    }),
    _t("gads_create_campaign", "Create a new Google Ads campaign (starts PAUSED)", {
        **_cid_prop,
        "name": {"type": "string", "description": "Campaign name"},
        "daily_budget": {"type": "number", "description": "Daily budget in dollars"},
        "channel_type": {"type": "string", "enum": ["SEARCH", "DISPLAY", "SHOPPING", "VIDEO", "PERFORMANCE_MAX"], "description": "Ad channel (default: SEARCH)"},
        "bidding_strategy": {"type": "string", "enum": ["MAXIMIZE_CLICKS", "MAXIMIZE_CONVERSIONS", "TARGET_CPA", "TARGET_ROAS", "MANUAL_CPC"], "description": "Bidding strategy (default: MAXIMIZE_CLICKS)"},
        "target_cpa": {"type": "number", "description": "Target CPA in dollars (for TARGET_CPA bidding)"},
        "target_roas": {"type": "number", "description": "Target ROAS (for TARGET_ROAS bidding, e.g., 4.0 = 400%)"},
    }, ["name", "daily_budget"]),
    _t("gads_update_campaign", "Update campaign name or status (ENABLED/PAUSED/REMOVED)", {
        **_cid_prop, "campaign_id": {"type": "string"}, "name": {"type": "string"},
        "status": {"type": "string", "enum": ["ENABLED", "PAUSED", "REMOVED"]}
    }, ["campaign_id"]),
    _t("gads_delete_campaign", "Remove a campaign", {**_cid_prop, "campaign_id": {"type": "string"}}, ["campaign_id"]),

    # Ad Groups
    _t("gads_list_ad_groups", "List ad groups with metrics", {
        **_cid_prop, "campaign_id": {"type": "string", "description": "Filter by campaign"}
    }),
    _t("gads_create_ad_group", "Create an ad group in a campaign", {
        **_cid_prop, "campaign_id": {"type": "string"}, "name": {"type": "string"},
        "cpc_bid": {"type": "number", "description": "Max CPC bid in dollars (default: 1.00)"}
    }, ["campaign_id", "name"]),
    _t("gads_update_ad_group", "Update ad group name, status, or bid", {
        **_cid_prop, "ad_group_id": {"type": "string"},
        "name": {"type": "string"}, "status": {"type": "string", "enum": ["ENABLED", "PAUSED", "REMOVED"]},
        "cpc_bid": {"type": "number"}
    }, ["ad_group_id"]),

    # Ads
    _t("gads_list_ads", "List ads with headlines, descriptions, and metrics", {
        **_cid_prop, "campaign_id": {"type": "string"}, "ad_group_id": {"type": "string"}
    }),
    _t("gads_create_responsive_search_ad", "Create a responsive search ad (starts PAUSED)", {
        **_cid_prop, "ad_group_id": {"type": "string"},
        "headlines": {"type": "array", "items": {"type": "string"}, "description": "3-15 headlines (max 30 chars each)"},
        "descriptions": {"type": "array", "items": {"type": "string"}, "description": "2-4 descriptions (max 90 chars each)"},
        "final_url": {"type": "string", "description": "Landing page URL"},
        "path1": {"type": "string", "description": "Display URL path 1 (max 15 chars)"},
        "path2": {"type": "string", "description": "Display URL path 2 (max 15 chars)"},
    }, ["ad_group_id", "headlines", "descriptions", "final_url"]),
    _t("gads_update_ad", "Enable, pause, or remove an ad", {
        **_cid_prop, "ad_group_id": {"type": "string"}, "ad_id": {"type": "string"},
        "status": {"type": "string", "enum": ["ENABLED", "PAUSED", "REMOVED"]}
    }, ["ad_group_id", "ad_id", "status"]),

    # Keywords
    _t("gads_list_keywords", "List keywords with quality scores and metrics", {
        **_cid_prop, "campaign_id": {"type": "string"}, "ad_group_id": {"type": "string"}
    }),
    _t("gads_add_keywords", "Add keywords to an ad group", {
        **_cid_prop, "ad_group_id": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keyword texts to add"},
        "match_type": {"type": "string", "enum": ["EXACT", "PHRASE", "BROAD"], "description": "Match type (default: PHRASE)"}
    }, ["ad_group_id", "keywords"]),
    _t("gads_add_negative_keywords", "Add negative keywords to a campaign", {
        **_cid_prop, "campaign_id": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}}
    }, ["campaign_id", "keywords"]),

    # Targeting
    _t("gads_search_locations", "Search for geo targeting locations (states, cities, counties)", {
        "query": {"type": "string", "description": "Location name (e.g., 'New Jersey', 'Bergen County')"}
    }, ["query"]),
    _t("gads_set_location_targeting", "Set geographic targeting for a campaign", {
        **_cid_prop, "campaign_id": {"type": "string"},
        "location_ids": {"type": "array", "items": {"type": "integer"}, "description": "Geo target constant IDs from search_locations"}
    }, ["campaign_id", "location_ids"]),

    # Budget
    _t("gads_update_budget", "Change a campaign's daily budget", {
        **_cid_prop, "campaign_id": {"type": "string"},
        "daily_budget": {"type": "number", "description": "New daily budget in dollars"}
    }, ["campaign_id", "daily_budget"]),

    # Reporting
    _t("gads_performance_report", "Get performance report at campaign, ad group, keyword, or search term level", {
        **_cid_prop,
        "level": {"type": "string", "enum": ["campaign", "ad_group", "keyword", "search_term"], "description": "Report level (default: campaign)"},
        "date_range": {"type": "string", "enum": ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "THIS_MONTH", "LAST_MONTH", "LAST_90_DAYS"], "description": "Date range (default: LAST_30_DAYS)"}
    }),
    _t("gads_daily_spend", "Get daily spend breakdown", {
        **_cid_prop, "days": {"type": "integer", "description": "Number of days (default: 30)"}
    }),
]

HANDLERS = {
    "gads_list_accounts": _list_accounts,
    "gads_account_info": _account_info,
    "gads_check_connection": _check_connection,
    "gads_query": _run_query,
    "gads_list_campaigns": _list_campaigns,
    "gads_create_campaign": _create_campaign,
    "gads_update_campaign": _update_campaign,
    "gads_delete_campaign": _delete_campaign,
    "gads_list_ad_groups": _list_ad_groups,
    "gads_create_ad_group": _create_ad_group,
    "gads_update_ad_group": _update_ad_group,
    "gads_list_ads": _list_ads,
    "gads_create_responsive_search_ad": _create_responsive_search_ad,
    "gads_update_ad": _update_ad,
    "gads_list_keywords": _list_keywords,
    "gads_add_keywords": _add_keywords,
    "gads_add_negative_keywords": _add_negative_keywords,
    "gads_search_locations": _search_locations,
    "gads_set_location_targeting": _set_location_targeting,
    "gads_update_budget": _update_budget,
    "gads_performance_report": _performance_report,
    "gads_daily_spend": _daily_spend,
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = HANDLERS.get(name)
    if not handler:
        return _err(f"Unknown tool: {name}")
    return await handler(arguments or {})


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
