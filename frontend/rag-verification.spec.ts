/**
 * RAG (Retrieval Augmented Generation) System Verification Test
 *
 * This test verifies that the RAG system is working correctly with:
 * - Semantic property search
 * - Research document search
 * - Compliance knowledge base
 * - Vector embeddings
 * - MCP tools integration
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_URL || 'https://ai-realtor.fly.dev';

test.describe('RAG System Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Set up any necessary authentication or configuration
    console.log(`Testing RAG system against: ${API_BASE}`);
  });

  test('1. Verify semantic property search works', async ({ request }) => {
    console.log('Testing semantic property search...');

    // Test semantic search with natural language
    const searchResponse = await request.post(`${API_BASE}/search/properties`, {
      data: {
        query: "modern condo with parking near good schools",
        limit: 5
      }
    });

    expect(searchResponse.ok()).toBeTruthy();

    const searchData = await searchResponse.json();
    console.log('Search response:', JSON.stringify(searchData, null, 2));

    // Verify response structure
    expect(searchData).toHaveProperty('results');
    expect(searchData).toHaveProperty('query');
    expect(searchData).toHaveProperty('count');
    expect(searchData).toHaveProperty('voice_summary');

    // Verify voice summary is present
    expect(searchData.voice_summary).toBeTruthy();
    expect(typeof searchData.voice_summary).toBe('string');

    console.log(`✅ Semantic search returned ${searchData.count} results`);
    console.log(`Voice summary: ${searchData.voice_summary}`);
  });

  test('2. Verify research document search functionality', async ({ request }) => {
    console.log('Testing research document search...');

    // Test research search
    const researchResponse = await request.post(`${API_BASE}/search/research`, {
      data: {
        query: "flood risk property inspection",
        dossier_limit: 3,
        evidence_limit: 5
      }
    });

    expect(researchResponse.ok()).toBeTruthy();

    const researchData = await researchResponse.json();
    console.log('Research search response:', JSON.stringify(researchData, null, 2));

    // Verify response structure
    expect(researchData).toHaveProperty('dossiers');
    expect(researchData).toHaveProperty('evidence');
    expect(researchData).toHaveProperty('query');
    expect(researchData).toHaveProperty('total_count');
    expect(researchData).toHaveProperty('voice_summary');

    console.log(`✅ Research search returned ${researchData.total_count} items`);
    console.log(`Voice summary: ${researchData.voice_summary}`);
  });

  test('3. Test compliance knowledge base access', async ({ request }) => {
    console.log('Testing compliance knowledge base...');

    // Get compliance rules
    const rulesResponse = await request.get(`${API_BASE}/compliance/knowledge/rules?limit=5`);
    expect(rulesResponse.ok()).toBeTruthy();

    const rules = await rulesResponse.json();
    console.log(`Found ${rules.length} compliance rules`);

    if (rules.length > 0) {
      const rule = rules[0];
      console.log(`Sample rule: ${rule.title} (${rule.rule_code})`);

      // Verify rule structure has real estate domain knowledge
      expect(rule).toHaveProperty('title');
      expect(rule).toHaveProperty('description');
      expect(rule).toHaveProperty('category');
      expect(rule).toHaveProperty('severity');
      expect(rule).toHaveProperty('state');

      // Test voice search for compliance rules
      const voiceSearchResponse = await request.get(`${API_BASE}/compliance/knowledge/voice/search-rules`, {
        params: {
          query: 'lead paint disclosure',
          state: 'NY'
        }
      });

      if (voiceSearchResponse.ok()) {
        const voiceData = await voiceSearchResponse.json();
        console.log(`Voice search found ${voiceData.count} rules`);
        console.log(`Voice summary: ${voiceData.voice_summary}`);
      }
    }

    console.log('✅ Compliance knowledge base is accessible');
  });

  test('4. Verify vector embeddings are working', async ({ request }) => {
    console.log('Testing vector embeddings functionality...');

    // Get list of properties first
    const propertiesResponse = await request.get(`${API_BASE}/properties/?limit=5`);
    expect(propertiesResponse.ok()).toBeTruthy();

    const properties = await propertiesResponse.json();
    console.log(`Found ${properties.length} properties to test with`);

    if (properties.length > 0) {
      const property = properties[0];
      console.log(`Testing with property ${property.id}: ${property.address}`);

      // Test finding similar properties (requires embeddings)
      const similarResponse = await request.get(`${API_BASE}/search/similar/${property.id}?limit=3`);
      expect(similarResponse.ok()).toBeTruthy();

      const similarData = await similarResponse.json();
      console.log('Similar properties response:', JSON.stringify(similarData, null, 2));

      // Verify response structure
      expect(similarData).toHaveProperty('property_id');
      expect(similarData).toHaveProperty('similar');
      expect(similarData).toHaveProperty('count');
      expect(similarData).toHaveProperty('voice_summary');

      console.log(`✅ Found ${similarData.count} similar properties`);
      console.log(`Voice summary: ${similarData.voice_summary}`);
    }

    // Test backfill functionality (to ensure embeddings can be generated)
    const backfillResponse = await request.post(`${API_BASE}/search/backfill`, {
      data: {
        table: 'properties'
      }
    });

    if (backfillResponse.ok()) {
      const backfillData = await backfillResponse.json();
      console.log('Backfill response:', JSON.stringify(backfillData, null, 2));
      console.log('✅ Vector embedding backfill is working');
    }
  });

  test('5. Test MCP tools integration (simulate)', async ({ request }) => {
    console.log('Testing MCP-like functionality...');

    // Test the same endpoints that MCP tools would use
    // This simulates what the semantic_search MCP tool does
    const mcpSearchResponse = await request.post(`${API_BASE}/search/properties`, {
      data: {
        query: "affordable family home with good schools",
        limit: 3,
        max_price: 500000
      }
    });

    expect(mcpSearchResponse.ok()).toBeTruthy();
    const mcpData = await mcpSearchResponse.json();

    // Verify the response is in voice-optimized format (as MCP tools expect)
    expect(mcpData.voice_summary).toBeTruthy();
    expect(mcpData.results).toBeDefined();

    console.log('✅ MCP-compatible search working');
    console.log(`MCP Voice Response: ${mcpData.voice_summary}`);

    // Test research search (as search_research MCP tool would)
    const mcpResearchResponse = await request.post(`${API_BASE}/search/research`, {
      data: {
        query: "property inspection checklist",
        dossier_limit: 2,
        evidence_limit: 3
      }
    });

    if (mcpResearchResponse.ok()) {
      const mcpResearchData = await mcpResearchResponse.json();
      console.log('✅ MCP-compatible research search working');
      console.log(`Research Voice Response: ${mcpResearchData.voice_summary}`);
    }
  });

  test('6. Comprehensive RAG system health check', async ({ request }) => {
    console.log('Running comprehensive RAG system health check...');

    const healthChecks = [];

    // Check 1: API endpoints are responding
    try {
      const searchCheck = await request.post(`${API_BASE}/search/properties`, {
        data: { query: "test search", limit: 1 }
      });
      healthChecks.push({ check: 'Semantic Search API', status: searchCheck.ok() ? 'PASS' : 'FAIL' });
    } catch (e) {
      healthChecks.push({ check: 'Semantic Search API', status: 'ERROR', error: e.message });
    }

    // Check 2: Research search
    try {
      const researchCheck = await request.post(`${API_BASE}/search/research`, {
        data: { query: "test research", dossier_limit: 1, evidence_limit: 1 }
      });
      healthChecks.push({ check: 'Research Search API', status: researchCheck.ok() ? 'PASS' : 'FAIL' });
    } catch (e) {
      healthChecks.push({ check: 'Research Search API', status: 'ERROR', error: e.message });
    }

    // Check 3: Compliance knowledge
    try {
      const complianceCheck = await request.get(`${API_BASE}/compliance/knowledge/rules?limit=1`);
      healthChecks.push({ check: 'Compliance Knowledge API', status: complianceCheck.ok() ? 'PASS' : 'FAIL' });
    } catch (e) {
      healthChecks.push({ check: 'Compliance Knowledge API', status: 'ERROR', error: e.message });
    }

    // Check 4: Properties endpoint (needed for embeddings)
    try {
      const propertiesCheck = await request.get(`${API_BASE}/properties/?limit=1`);
      healthChecks.push({ check: 'Properties API', status: propertiesCheck.ok() ? 'PASS' : 'FAIL' });
    } catch (e) {
      healthChecks.push({ check: 'Properties API', status: 'ERROR', error: e.message });
    }

    // Report health check results
    console.log('\n=== RAG SYSTEM HEALTH CHECK RESULTS ===');
    healthChecks.forEach(check => {
      const status = check.status === 'PASS' ? '✅' : '❌';
      console.log(`${status} ${check.check}: ${check.status}`);
      if (check.error) {
        console.log(`   Error: ${check.error}`);
      }
    });

    const passedChecks = healthChecks.filter(c => c.status === 'PASS').length;
    const totalChecks = healthChecks.length;

    console.log(`\nOverall Health: ${passedChecks}/${totalChecks} checks passed`);

    // Require at least 75% of checks to pass
    expect(passedChecks / totalChecks).toBeGreaterThanOrEqual(0.75);

    console.log('\n✅ RAG system health check completed!');
  });
});