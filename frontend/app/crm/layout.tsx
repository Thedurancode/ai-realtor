'use client'

import CRMSidebar from '@/components/crm/CRMSidebar'

export default function CRMLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0B0D15] text-white">
      <CRMSidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
