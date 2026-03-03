'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckSquare,
  Circle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Filter,
  RefreshCw,
  Calendar,
  Building2,
  XCircle,
  Loader2,
  ArrowUp,
  ArrowDown,
  Minus,
  ChevronDown,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const priorityConfig: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  urgent: { label: 'Urgent', color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20', icon: AlertTriangle },
  high: { label: 'High', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20', icon: ArrowUp },
  medium: { label: 'Medium', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', icon: Minus },
  low: { label: 'Low', color: 'text-gray-400', bg: 'bg-gray-500/10 border-gray-500/20', icon: ArrowDown },
}

const statusConfig: Record<string, { label: string; color: string; icon: any }> = {
  pending: { label: 'Pending', color: 'text-gray-400', icon: Circle },
  in_progress: { label: 'In Progress', color: 'text-blue-400', icon: Loader2 },
  completed: { label: 'Completed', color: 'text-emerald-400', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', color: 'text-gray-500', icon: XCircle },
}

function TaskItem({ task, onToggle }: { task: any; onToggle: (id: number, status: string) => void }) {
  const priority = priorityConfig[task.priority?.toLowerCase()] || priorityConfig.medium
  const status = statusConfig[task.status?.toLowerCase()] || statusConfig.pending
  const isComplete = task.status === 'completed'
  const PriorityIcon = priority.icon
  const StatusIcon = status.icon

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -5 }}
      className={`
        flex items-start gap-3 p-4 rounded-xl transition-all duration-200
        ${isComplete ? 'opacity-50' : ''}
        bg-[#111318] border border-[#1E2130] hover:border-[#2A2D3A]
      `}
    >
      {/* Toggle */}
      <button
        onClick={() => onToggle(task.id, isComplete ? 'pending' : 'completed')}
        className="mt-0.5 flex-shrink-0"
      >
        {isComplete ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
        ) : (
          <Circle className="w-5 h-5 text-gray-600 hover:text-blue-400 transition-colors" />
        )}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${isComplete ? 'text-gray-500 line-through' : 'text-white'}`}>
          {task.title}
        </p>
        {task.description && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{task.description}</p>
        )}
        <div className="flex items-center gap-3 mt-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border font-medium ${priority.bg} ${priority.color}`}>
            <PriorityIcon className="w-2.5 h-2.5" />
            {priority.label}
          </span>
          <span className={`inline-flex items-center gap-1 text-[10px] ${status.color}`}>
            <StatusIcon className={`w-2.5 h-2.5 ${task.status === 'in_progress' ? 'animate-spin' : ''}`} />
            {status.label}
          </span>
          {task.due_date && (
            <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
              <Calendar className="w-2.5 h-2.5" />
              {new Date(task.due_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([])
  const [properties, setProperties] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')

  const fetchData = useCallback(async () => {
    try {
      const propsRes = await fetch(`${API}/properties/?limit=200`)
      const propsData = await propsRes.json()
      const props = Array.isArray(propsData) ? propsData : []
      setProperties(props)

      const allTasks: any[] = []
      await Promise.all(
        props.map(async (p: any) => {
          try {
            const res = await fetch(`${API}/todos/property/${p.id}`)
            const data = await res.json()
            const todos = data.todos || []
            todos.forEach((t: any) => {
              t._propertyAddress = p.address
              t._propertyId = p.id
            })
            allTasks.push(...todos)
          } catch {}
        })
      )

      const unique = Array.from(new Map(allTasks.map(t => [t.id, t])).values())
      // Sort: urgent first, then by priority, then by date
      unique.sort((a, b) => {
        const priorityOrder: Record<string, number> = { urgent: 0, high: 1, medium: 2, low: 3 }
        const statusOrder: Record<string, number> = { in_progress: 0, pending: 1, completed: 2, cancelled: 3 }
        const sDiff = (statusOrder[a.status] || 1) - (statusOrder[b.status] || 1)
        if (sDiff !== 0) return sDiff
        return (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2)
      })
      setTasks(unique)
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleTask = async (id: number, newStatus: string) => {
    try {
      await fetch(`${API}/todos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      setTasks(prev => prev.map(t => t.id === id ? { ...t, status: newStatus } : t))
    } catch (err) {
      console.error('Failed to update task:', err)
    }
  }

  const filtered = tasks.filter((t) => {
    if (statusFilter !== 'all' && t.status !== statusFilter) return false
    if (priorityFilter !== 'all' && t.priority?.toLowerCase() !== priorityFilter) return false
    return true
  })

  const stats = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1000px] mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-2xl font-bold text-white">Tasks</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your property-related tasks</p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Total', value: stats.total, color: 'text-white' },
          { label: 'Pending', value: stats.pending, color: 'text-gray-400' },
          { label: 'In Progress', value: stats.inProgress, color: 'text-blue-400' },
          { label: 'Completed', value: stats.completed, color: 'text-emerald-400' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="p-3 rounded-xl bg-[#111318] border border-[#1E2130] text-center"
          >
            <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-[#111318] border border-[#1E2130] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
        >
          <option value="all">All Priority</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <div className="flex-1" />
        <button
          onClick={() => { setLoading(true); fetchData() }}
          className="px-4 py-2.5 rounded-lg bg-[#1A1D27] border border-[#2A2D3A] text-sm text-gray-300 hover:text-white hover:border-blue-500/30 transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Task List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="rounded-xl bg-[#111318] border border-[#1E2130] h-20 animate-pulse" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          <AnimatePresence>
            {filtered.map((task) => (
              <TaskItem key={task.id} task={task} onToggle={toggleTask} />
            ))}
          </AnimatePresence>
        </div>
      ) : (
        <div className="text-center py-20">
          <CheckSquare className="w-12 h-12 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">No tasks found</p>
          <p className="text-sm text-gray-600 mt-1">Tasks will appear as they are created for properties</p>
        </div>
      )}
    </div>
  )
}
