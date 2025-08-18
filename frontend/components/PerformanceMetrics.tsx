'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Activity, Clock, TrendingUp, BarChart3 } from 'lucide-react'

interface PerformanceStats {
  total_calls: number
  total_time_ms: number
  avg_overall_time_ms: number
  avg_graph_call_time_ms: number
  last_updated: string
}

interface PerformanceLog {
  service: string
  tx_id: string
  overall_ms: number
  graph_calls: number
  total_graph_ms: number
  timestamp: string
  call_type: string
  call_details: Array<{
    operation: string
    time_ms: number
  }>
}

interface PerformanceOverview {
  service: string
  overview: {
    stats: PerformanceStats
    recent_logs_count: number
    sample_logs: PerformanceLog[]
  }
  timestamp: string
}

export default function PerformanceMetrics() {
  const [overview, setOverview] = useState<PerformanceOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTransactionId, setSelectedTransactionId] = useState<string>('')
  const [selectedLog, setSelectedLog] = useState<PerformanceLog | null>(null)

  const fetchPerformanceOverview = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('http://localhost:4000/performance/overview')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setOverview(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch performance data')
    } finally {
      setLoading(false)
    }
  }

  const fetchTransactionLog = async (transactionId: string) => {
    try {
      setError(null)
      
      const response = await fetch(`http://localhost:4000/performance/logs?transaction_id=${transactionId}`)
      if (!response.ok) {
        if (response.status === 404) {
          setError(`Transaction log not found for ID: ${transactionId}`)
          return
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setSelectedLog(data.log)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch transaction log')
    }
  }

  useEffect(() => {
    fetchPerformanceOverview()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchPerformanceOverview, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
          <p className="font-medium">Error loading performance metrics</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button onClick={fetchPerformanceOverview} variant="outline">
          Retry
        </Button>
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="text-center text-muted-foreground">
        No performance data available
      </div>
    )
  }

  const { stats } = overview.overview

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Performance Metrics</h1>
          <p className="text-muted-foreground">
            RT1 Fraud Detection Service Performance Overview
          </p>
        </div>
        <Button onClick={fetchPerformanceOverview} variant="outline">
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Performance Statistics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_calls}</div>
            <p className="text-xs text-muted-foreground">
              Total fraud detection calls
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_time_ms.toFixed(2)} ms</div>
            <p className="text-xs text-muted-foreground">
              Cumulative processing time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avg_overall_time_ms.toFixed(2)} ms</div>
            <p className="text-xs text-muted-foreground">
              Average per transaction
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Graph Call</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avg_graph_call_time_ms.toFixed(2)} ms</div>
            <p className="text-xs text-muted-foreground">
              Average per graph operation
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Transaction Log Lookup */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction Log Lookup</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter transaction ID"
              value={selectedTransactionId}
              onChange={(e) => setSelectedTransactionId(e.target.value)}
              className="flex-1 px-3 py-2 border border-input rounded-md"
            />
            <Button 
              onClick={() => fetchTransactionLog(selectedTransactionId)}
              disabled={!selectedTransactionId.trim()}
            >
              Lookup
            </Button>
          </div>
          
          {selectedLog && (
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Transaction: {selectedLog.tx_id}</h3>
                <Badge variant="outline">{selectedLog.call_type}</Badge>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium">Overall Time:</span>
                  <div className="text-lg font-bold text-primary">{selectedLog.overall_ms} ms</div>
                </div>
                <div>
                  <span className="font-medium">Graph Calls:</span>
                  <div className="text-lg font-bold">{selectedLog.graph_calls}</div>
                </div>
                <div>
                  <span className="font-medium">Total Graph Time:</span>
                  <div className="text-lg font-bold text-primary">{selectedLog.total_graph_ms} ms</div>
                </div>
              </div>
              
              <div>
                <span className="font-medium">Graph Call Breakdown:</span>
                <div className="mt-2 space-y-1">
                  {selectedLog.call_details.map((call, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{call.operation}:</span>
                      <span className="font-medium">{call.time_ms} ms</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="text-xs text-muted-foreground">
                Timestamp: {new Date(selectedLog.timestamp).toLocaleString()}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Sample Logs */}
      {overview.overview.sample_logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Sample Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overview.overview.sample_logs.map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium">{log.tx_id}</div>
                    <div className="text-sm text-muted-foreground">
                      {log.overall_ms} ms • {log.graph_calls} graph calls
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedTransactionId(log.tx_id)
                      setSelectedLog(log)
                    }}
                  >
                    View Details
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-xs text-muted-foreground text-center">
        Last updated: {new Date(overview.timestamp).toLocaleString()}
      </div>
    </div>
  )
}
