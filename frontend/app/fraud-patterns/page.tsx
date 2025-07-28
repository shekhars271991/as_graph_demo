'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Shield, Activity, TrendingUp, Users, CreditCard } from 'lucide-react'
import { api } from '@/lib/api'

interface FraudPattern {
  id: string
  name: string
  description: string
  risk_level: string
}

interface FraudResult {
  pattern_id: string
  pattern_name: string
  detected_entities: any[]
  risk_score: number
  timestamp: string
  details: any
}

const availablePatterns: FraudPattern[] = [
  {
    id: 'circular_flow',
    name: 'Circular Transaction Flow',
    description: 'Detect circular money flows between users',
    risk_level: 'high'
  },
  {
    id: 'shared_device',
    name: 'Shared Device Transactions',
    description: 'Detect transactions from the same device by different users',
    risk_level: 'medium'
  },
  {
    id: 'transaction_burst',
    name: 'Transaction Burst',
    description: 'Detect rapid successive transactions from same user',
    risk_level: 'medium'
  },
  {
    id: 'high_amount',
    name: 'High Amount Transactions',
    description: 'Detect unusually high transaction amounts',
    risk_level: 'high'
  },
  {
    id: 'cross_location',
    name: 'Cross-Location Transactions',
    description: 'Detect transactions between users in different locations',
    risk_level: 'medium'
  },
  {
    id: 'new_user_high_activity',
    name: 'New User High Activity',
    description: 'Detect new users with high transaction activity',
    risk_level: 'high'
  }
]

export default function FraudPatternsPage() {
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>([])
  const [results, setResults] = useState<FraudResult[]>([])
  const [loading, setLoading] = useState(false)

  const togglePattern = (patternId: string) => {
    setSelectedPatterns(prev => 
      prev.includes(patternId) 
        ? prev.filter(id => id !== patternId)
        : [...prev, patternId]
    )
  }

  const runPatterns = async () => {
    if (selectedPatterns.length === 0) return
    
    setLoading(true)
    try {
      const response = await api.post('/fraud-patterns/run', selectedPatterns)
      setResults(response.data.results || [])
    } catch (error) {
      console.error('Failed to run fraud patterns:', error)
    } finally {
      setLoading(false)
    }
  }

  const runAllPatterns = async () => {
    setLoading(true)
    try {
      const response = await api.get('/detect/fraudulent-transactions')
      setResults(response.data.results || [])
    } catch (error) {
      console.error('Failed to run all fraud patterns:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'destructive'
      case 'medium': return 'warning'
      case 'low': return 'success'
      default: return 'default'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Fraud Patterns</h1>
        <p className="text-muted-foreground">
          Run fraud detection algorithms and analyze suspicious patterns
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Available Patterns
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {availablePatterns.map((pattern) => (
              <div
                key={pattern.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedPatterns.includes(pattern.id)
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
                onClick={() => togglePattern(pattern.id)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{pattern.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {pattern.description}
                    </p>
                  </div>
                  <Badge variant={getRiskColor(pattern.risk_level) as any}>
                    {pattern.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
            
            <div className="flex gap-2 pt-4">
              <Button 
                onClick={runPatterns} 
                disabled={loading || selectedPatterns.length === 0}
                className="flex-1"
              >
                <Shield className="h-4 w-4 mr-2" />
                Run Selected
              </Button>
              <Button 
                onClick={runAllPatterns} 
                disabled={loading}
                variant="outline"
              >
                <Activity className="h-4 w-4 mr-2" />
                Run All
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Detection Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-4">
                {results.map((result, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium">{result.pattern_name}</h3>
                      <Badge variant="destructive">
                        Score: {result.risk_score.toFixed(1)}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      Detected {result.detected_entities.length} entities
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(result.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">
                  No results yet. Run a pattern to see results.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-destructive">
                  {results.length}
                </div>
                <p className="text-sm text-muted-foreground">Patterns Detected</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {results.reduce((sum, r) => sum + r.detected_entities.length, 0)}
                </div>
                <p className="text-sm text-muted-foreground">Total Entities</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-warning">
                  {(results.reduce((sum, r) => sum + r.risk_score, 0) / results.length).toFixed(1)}
                </div>
                <p className="text-sm text-muted-foreground">Avg Risk Score</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-success">
                  {results.filter(r => r.risk_score > 70).length}
                </div>
                <p className="text-sm text-muted-foreground">High Risk</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 