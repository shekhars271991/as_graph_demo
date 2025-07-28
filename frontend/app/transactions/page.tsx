'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Search, CreditCard, DollarSign, Calendar, MapPin, Shield } from 'lucide-react'
import { api } from '@/lib/api'

interface Transaction {
  id: string
  sender_id: string
  receiver_id: string
  amount: number
  currency: string
  timestamp: string
  location: string
  status: string
  fraud_score: number
}

export default function TransactionsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)

  const searchTransactions = async () => {
    if (!searchQuery.trim()) return
    
    setLoading(true)
    try {
      const response = await api.get(`/transactions/search?query=${searchQuery}`)
      setTransactions(response.data.transactions || [])
    } catch (error) {
      console.error('Failed to search transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'pending': return 'warning'
      case 'failed': return 'destructive'
      case 'suspicious': return 'destructive'
      default: return 'default'
    }
  }

  const getRiskLevel = (score: number) => {
    if (score < 25) return { level: 'Low', color: 'success' }
    if (score < 50) return { level: 'Medium', color: 'warning' }
    if (score < 75) return { level: 'High', color: 'destructive' }
    return { level: 'Critical', color: 'destructive' }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Transaction Explorer</h1>
        <p className="text-muted-foreground">
          Search and explore transaction details and patterns
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Search by transaction ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchTransactions()}
            />
            <Button onClick={searchTransactions} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {transactions.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {transactions.map((transaction) => {
            const risk = getRiskLevel(transaction.fraud_score)
            return (
              <Card key={transaction.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <CreditCard className="h-5 w-5" />
                        {transaction.id}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {transaction.sender_id} → {transaction.receiver_id}
                      </p>
                    </div>
                    <Badge variant={getStatusColor(transaction.status) as any}>
                      {transaction.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">
                      {transaction.amount.toLocaleString()} {transaction.currency}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>{new Date(transaction.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span>{transaction.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Shield className="h-4 w-4 text-muted-foreground" />
                    <span>Risk Score: {transaction.fraud_score.toFixed(1)}</span>
                    <Badge variant={risk.color as any} className="ml-auto">
                      {risk.level}
                    </Badge>
                  </div>
                  <div className="pt-2">
                    <Button variant="outline" size="sm" className="w-full">
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {transactions.length === 0 && !loading && searchQuery && (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">No transactions found</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 