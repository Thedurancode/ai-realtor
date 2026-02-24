# TV Display Component - Quick Reference Guide

## What You're Building

A **real-time contract management dashboard** for a TV display showing:
- Contract status (sent, opened, completed, declined)
- Individual signer progress
- Property information
- Agent activity
- Task/todo tracking

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TV Display (Frontend)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              React / Next.js Application                  │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────┐    │ │
│  │  │         Contract Status Dashboard              │    │ │
│  │  │  - Show all contracts & signer progress       │    │ │
│  │  │  - Real-time status updates (polling)        │    │ │
│  │  │  - Kanban board by status                    │    │ │
│  │  └──────────────────────────────────────────────────┘    │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────┐    │ │
│  │  │         Property Dashboard                      │    │ │
│  │  │  - List properties by agent                    │    │ │
│  │  │  - Status filter (available, pending, sold)  │    │ │
│  │  │  - Quick metrics display                      │    │ │
│  │  └──────────────────────────────────────────────────┘    │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────┐    │ │
│  │  │         Activity Feed                           │    │ │
│  │  │  - Recent contract sends                       │    │ │
│  │  │  - Signer updates with timestamps             │    │ │
│  │  │  - Task completions                           │    │ │
│  │  └──────────────────────────────────────────────────┘    │ │
│  │                                                            │ │
│  │  Auto-refresh every 30 seconds                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (HTTP/REST)
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│                  http://localhost:8000                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              REST API Endpoints                           │ │
│  │                                                            │ │
│  │  GET  /agents/                 → List all agents         │ │
│  │  GET  /properties/             → List properties         │ │
│  │  GET  /contracts/property/{id} → Property contracts      │ │
│  │  GET  /contracts/{id}/status   → Contract status + signers
│  │  GET  /contacts/property/{id}  → Property contacts       │ │
│  │  GET  /todos/                  → Task list               │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           SQLite Database (realtor.db)                   │ │
│  │                                                            │ │
│  │  Tables:                                                 │ │
│  │  - agents                  (agent info)                  │ │
│  │  - properties              (property listings)           │ │
│  │  - contracts               (contract docs)               │ │
│  │  - contract_submitters     (individual signers)          │ │
│  │  - contacts                (buyers, lawyers, etc.)       │ │
│  │  - todos                   (tasks)                       │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           External Services                               │ │
│  │                                                            │ │
│  │  - DocuSeal (contract signing)                           │ │
│  │  - Resend (email notifications)                          │ │
│  │  - Google Places (address autocomplete)                  │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Data Flows for TV Display

### Contract Status Display Flow
```
User opens TV Display
         ↓
Frontend polls: GET /contracts/property/{property_id}
         ↓
API returns: [Contract, Contract, ...]
         ↓
Frontend polls: GET /contracts/{id}/status?refresh=true
         ↓
API returns: Contract with submitters array
         ↓
Display shows:
  - Contract name
  - Each signer's status (pending, opened, completed, declined)
  - Timestamps (sent_at, opened_at, completed_at)
  - Overall progress bar
         ↓
Auto-refresh every 30 seconds
```

### Real-Time Status Update Flow
```
Signer opens document in DocuSeal
         ↓
DocuSeal webhook → API
         ↓
Database updates: submitter.status = "opened"
         ↓
Frontend polls at next interval (30 sec)
         ↓
Status appears on TV Display
```

---

## Frontend Implementation Plan

### Folder Structure
```
frontend/
├── public/
│   └── images/
├── src/
│   ├── pages/
│   │   ├── index.tsx           # Dashboard home
│   │   ├── contracts.tsx       # Contract board
│   │   └── properties.tsx      # Property list
│   ├── components/
│   │   ├── ContractCard.tsx    # Individual contract display
│   │   ├── SignerStatus.tsx    # Show signer progress
│   │   ├── ActivityFeed.tsx    # Recent activity
│   │   ├── PropertyCard.tsx    # Property info
│   │   └── Dashboard.tsx       # Main layout
│   ├── hooks/
│   │   ├── useContracts.ts     # Fetch & cache contracts
│   │   ├── useProperties.ts    # Fetch properties
│   │   └── usePolling.ts       # Auto-refresh logic
│   ├── services/
│   │   ├── api.ts              # API client (axios/fetch)
│   │   └── types.ts            # TypeScript types
│   ├── styles/
│   │   └── globals.css         # TV display styling
│   └── app.tsx
├── package.json
└── tsconfig.json
```

---

## API Integration Checklist

### Essential Endpoints

- [x] `GET /agents/` - List agents
  ```typescript
  const agents = await fetch('/api/agents/');
  ```

- [x] `GET /properties/` - List properties
  ```typescript
  const properties = await fetch('/api/properties/');
  ```

- [x] `GET /contracts/property/{property_id}` - Get contracts for property
  ```typescript
  const contracts = await fetch(`/api/contracts/property/${propertyId}`);
  ```

- [x] `GET /contracts/{contract_id}/status` - Get contract status with signers
  ```typescript
  const status = await fetch(`/api/contracts/${contractId}/status?refresh=true`);
  ```

- [x] `GET /contacts/property/{property_id}` - Get property contacts
  ```typescript
  const contacts = await fetch(`/api/contacts/property/${propertyId}`);
  ```

- [x] `GET /todos/` - Get task list
  ```typescript
  const todos = await fetch('/api/todos/');
  ```

---

## Data Structures to Display

### Contract with Signers
```typescript
interface ContractStatus {
  id: number;
  name: string;
  status: "draft" | "sent" | "in_progress" | "completed" | "cancelled" | "expired";
  sent_at: string;           // ISO datetime
  completed_at: string | null;
  docuseal_url: string;
  property_id: number;
  submitters: ContractSubmitter[];
}

interface ContractSubmitter {
  id: number;
  name: string;
  email: string;
  role: string;              // "First Party", "Second Party", etc.
  status: "pending" | "opened" | "completed" | "declined";
  signing_order: number;
  sent_at: string | null;
  opened_at: string | null;
  completed_at: string | null;
}
```

### Property
```typescript
interface Property {
  id: number;
  title: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  property_type: "house" | "apartment" | "condo" | "townhouse" | "land" | "commercial";
  status: "available" | "pending" | "sold" | "rented" | "off_market";
  agent_id: number;
  created_at: string;
  updated_at: string;
}
```

### Agent
```typescript
interface Agent {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  license_number: string | null;
  created_at: string;
  updated_at: string;
}
```

---

## TV Display Specific Features

### 1. Full-Screen Optimization
```css
/* Large fonts for visibility */
body {
  font-size: 18px;
  line-height: 1.8;
}

h1 { font-size: 48px; }
h2 { font-size: 36px; }
h3 { font-size: 28px; }

/* High contrast colors */
background-color: #1a1a1a;  /* Dark background */
color: #ffffff;             /* White text */
```

### 2. Auto-Refresh
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    // Fetch latest contract status
    fetchContracts();
  }, 30000);  // Refresh every 30 seconds
  
  return () => clearInterval(interval);
}, []);
```

### 3. Status Indicators
```typescript
const getStatusColor = (status: string) => {
  switch(status) {
    case "draft":      return "gray";
    case "sent":       return "blue";
    case "opened":     return "orange";
    case "completed":  return "green";
    case "declined":   return "red";
    default:           return "gray";
  }
}
```

### 4. Progress Visualization
```typescript
// Show what % of signers have completed
const completionRate = (completed / total) * 100;
// Display as: "2 of 3 signers completed (67%)"
```

---

## Development Quick Start

### 1. Start the API Server
```bash
cd /Users/edduran/Documents/GitHub/ai-realtor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test it:
```bash
curl http://localhost:8000/docs
```

### 2. Create Next.js Frontend
```bash
cd /Users/edduran/Documents/GitHub/ai-realtor
npx create-next-app@latest frontend --typescript
cd frontend
npm install axios swr react-query
```

### 3. Create API Client
```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
});

export const contractsAPI = {
  getAll: () => api.get('/contracts'),
  getForProperty: (propertyId: number) => 
    api.get(`/contracts/property/${propertyId}`),
  getStatus: (contractId: number) => 
    api.get(`/contracts/${contractId}/status?refresh=true`),
};

export const propertiesAPI = {
  getAll: () => api.get('/properties'),
  getById: (id: number) => api.get(`/properties/${id}`),
};

export const contactsAPI = {
  getForProperty: (propertyId: number) => 
    api.get(`/contacts/property/${propertyId}`),
};
```

### 4. Create Custom Hook for Auto-Refresh
```typescript
// frontend/src/hooks/useContracts.ts
import { useState, useEffect } from 'react';
import { contractsAPI } from '@/services/api';

export function useContracts(propertyId: number) {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchContracts = async () => {
    try {
      const { data } = await contractsAPI.getForProperty(propertyId);
      setContracts(data);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContracts();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchContracts, 30000);
    return () => clearInterval(interval);
  }, [propertyId]);

  return { contracts, loading, refetch: fetchContracts };
}
```

---

## Display Examples

### Contract Status Board
```
┌─────────────────────────────────────────────────────────┐
│  CONTRACTS - 123 Main Street, Brooklyn, NY             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Purchase Agreement               Status: SENT         │
│  Sent: Feb 4, 2:45 PM                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 67%      │
│                                                         │
│  1. John Smith (Buyer)          ✓ Completed           │
│     Opened: Feb 4, 2:47 PM  Signed: Feb 4, 3:15 PM  │
│                                                         │
│  2. Sarah Johnson (Seller)      ⏳ Opened               │
│     Opened: Feb 4, 3:20 PM                            │
│                                                         │
│  3. Mike Davis (Agent)          ⏸ Pending              │
│     Waiting for signature...                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Property Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  PROPERTIES - Agent: John Broker                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 123 Main St  │  │ 456 Oak Ave   │  │ 789 Pine Dr  │ │
│  │ $750,000     │  │ $600,000      │  │ PENDING      │ │
│  │ 4BR, 3BA     │  │ AVAILABLE     │  │ $825,000     │ │
│  │ ✓ Available  │  │ Showing: 3pm  │  │ 5BR, 4BA     │ │
│  │              │  │ Next: 4pm     │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  Total: 3 Properties  |  Available: 2  |  Pending: 1  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Tips

1. **Implement Polling Efficiently**
   - Don't refresh all data every 30 seconds
   - Only refresh contract statuses (lightweight)
   - Cache property/agent data (refresh hourly)

2. **Show Loading States**
   - Prevent UI jumps
   - Indicate when data is refreshing

3. **Handle Errors Gracefully**
   - Show "Connection lost" message
   - Retry automatically

4. **Optimize Rendering**
   - Use React.memo for contract cards
   - Virtualize long lists
   - Avoid re-renders on unchanged data

---

## Testing Checklist

- [ ] API server running on localhost:8000
- [ ] Frontend can fetch contracts list
- [ ] Frontend can fetch contract status with signers
- [ ] Auto-refresh works every 30 seconds
- [ ] Status colors display correctly
- [ ] Timestamps format correctly
- [ ] Handles missing data gracefully
- [ ] Responsive on TV display size (4K, etc.)

---

## Troubleshooting

### Frontend can't reach API
```bash
# Check API is running
curl http://localhost:8000/docs

# Check CORS is enabled (FastAPI auto-enables for development)
# If needed, add to main.py:
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Data not updating
- Check console for errors
- Verify polling interval is running
- Check API endpoint returns fresh data
- Refresh page manually

### Styling issues on TV
- Increase font sizes further
- Use higher contrast colors
- Test on actual TV resolution
- Simplify layouts (larger spacing)

---

## Next Steps

1. Create Next.js frontend
2. Build API client service
3. Create main dashboard component
4. Implement auto-refresh polling
5. Add contract status display
6. Add property list view
7. Test with real data
8. Optimize for TV display

