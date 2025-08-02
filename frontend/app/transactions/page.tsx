'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Search, CreditCard, DollarSign, Calendar, MapPin, Shield, ChevronLeft, ChevronRight, Loader2, ArrowRight } from 'lucide-react'
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
  fraud_status?: string
  fraud_reason?: string
  is_fraud: boolean
  transaction_type: string
  merchant: string
  device_id?: string
}

interface PaginatedTransactions {
  transactions: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export default function TransactionsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalTransactions, setTotalTransactions] = useState(0)
  const [pageSize] = useState(12)
  const [viewMode, setViewMode] = useState<'all' | 'flagged'>('all')

  // Load transactions on component mount and when view mode or page changes
  useEffect(() => {
    loadAllTransactions()
  }, [currentPage, viewMode])

  const loadAllTransactions = async () => {
    setLoading(true)
    try {
      const endpoint = viewMode === 'flagged' 
        ? `/transactions/flagged?page=${currentPage}&page_size=${pageSize}`
        : `/transactions?page=${currentPage}&page_size=${pageSize}`
      
      const response = await api.get(endpoint)
      const data: PaginatedTransactions = response.data
      setTransactions(data.transactions || [])
      setTotalPages(data.total_pages || 1)
      setTotalTransactions(data.total || 0)
    } catch (error) {
      console.error('Failed to load transactions:', error)
      // Fallback to mock data if API fails
      setTransactions([])
    } finally {
      setLoading(false)
    }
  }

  const searchTransactions = async () => {
    if (!searchQuery.trim()) {
      // If search is cleared, load all transactions
      setCurrentPage(1)
      loadAllTransactions()
      return
    }
    
    setSearchLoading(true)
    try {
      const response = await api.get(`/transactions/search?query=${searchQuery}&page=${currentPage}&page_size=${pageSize}`)
      const data: PaginatedTransactions = response.data
      setTransactions(data.transactions || [])
      setTotalPages(data.total_pages || 1)
      setTotalTransactions(data.total || 0)
    } catch (error) {
      console.error('Failed to search transactions:', error)
      setTransactions([])
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSearch = () => {
    setCurrentPage(1) // Reset to first page when searching
    searchTransactions()
  }

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR'
    }).format(amount)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {viewMode === 'flagged' ? 'Flagged Transactions' : 'Transaction Explorer'}
        </h1>
        <p className="text-muted-foreground">
          {viewMode === 'flagged' 
            ? 'View transactions that have been flagged by fraud detection'
            : 'Search and explore transaction details and patterns'
          }
        </p>
      </div>

      {/* View Mode Controls */}
      <div className="flex space-x-2">
        <Button
          variant={viewMode === 'all' ? 'default' : 'outline'}
          onClick={() => {
            setViewMode('all')
            setCurrentPage(1)
          }}
        >
          All Transactions
        </Button>
        <Button
          variant={viewMode === 'flagged' ? 'default' : 'outline'}
          onClick={() => {
            setViewMode('flagged')
            setCurrentPage(1)
          }}
        >
          Flagged Transactions
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTransactions}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <Shield className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {transactions.filter(t => (t.fraud_score || 0) >= 75).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Medium Risk</CardTitle>
            <Shield className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">
              {transactions.filter(t => (t.fraud_score || 0) >= 50 && (t.fraud_score || 0) < 75).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Risk</CardTitle>
            <Shield className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">
              {transactions.filter(t => (t.fraud_score || 0) < 50).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle>Search Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Search by transaction ID, sender, or receiver..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              <Search className="h-4 w-4 mr-2" />
              {searchLoading ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading transactions...</span>
            </div>
          </CardContent>
        </Card>
      ) : transactions.length > 0 ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Transaction Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">Transaction ID</th>
                      <th className="text-left p-3 font-medium">Sender</th>
                      <th className="text-left p-3 font-medium">Receiver</th>
                      <th className="text-left p-3 font-medium">Amount</th>
                      <th className="text-left p-3 font-medium">Date</th>
                      <th className="text-left p-3 font-medium">Location</th>
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Risk Score</th>
                      <th className="text-left p-3 font-medium">Fraud Status</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((transaction) => {
                      const risk = getRiskLevel(transaction.fraud_score || 0)
                      return (
                        <tr key={transaction.id} className="border-b hover:bg-muted/50">
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <CreditCard className="h-4 w-4 text-muted-foreground" />
                              <span className="font-mono text-sm">{transaction.id}</span>
                            </div>
                          </td>
                          <td className="p-3">
                            <span className="font-mono text-sm">{transaction.sender_id}</span>
                          </td>
                          <td className="p-3">
                            <span className="font-mono text-sm">{transaction.receiver_id}</span>
                          </td>
                          <td className="p-3">
                            <span className="font-medium">
                              {formatAmount(transaction.amount, transaction.currency)}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-sm">{formatDate(transaction.timestamp)}</span>
                          </td>
                          <td className="p-3">
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3 text-muted-foreground" />
                              <span className="text-sm">{transaction.location}</span>
                            </div>
                          </td>
                          <td className="p-3">
                            <Badge variant={getStatusColor(transaction.status) as any}>
                              {transaction.status}
                            </Badge>
                          </td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <span className="text-sm">{(transaction.fraud_score || 0).toFixed(1)}</span>
                              <Badge variant={risk.color as any} className="text-xs">
                                {risk.level}
                              </Badge>
                            </div>
                          </td>
                          <td className="p-3">
                            {transaction.fraud_status ? (
                              <div className="space-y-1">
                                <Badge 
                                  variant={
                                    transaction.fraud_status === 'blocked' ? 'destructive' : 
                                    transaction.fraud_status === 'review' ? 'secondary' : 
                                    'default'
                                  }
                                  className="text-xs"
                                >
                                  {transaction.fraud_status.toUpperCase()}
                                </Badge>
                                {transaction.fraud_reason && (
                                  <div className="text-xs text-muted-foreground">
                                    {transaction.fraud_reason}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <Badge variant="secondary" className="text-xs">
                                CLEAN
                              </Badge>
                            )}
                          </td>
                          <td className="p-3">
                            <Button variant="outline" size="sm">
                              View Details
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Pagination */}
          {totalPages > 1 && (
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalTransactions)} of {totalTransactions} transactions
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum
                        if (totalPages <= 5) {
                          pageNum = i + 1
                        } else if (currentPage <= 3) {
                          pageNum = i + 1
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i
                        } else {
                          pageNum = currentPage - 2 + i
                        }
                        
                        return (
                          <Button
                            key={pageNum}
                            variant={currentPage === pageNum ? "default" : "outline"}
                            size="sm"
                            onClick={() => handlePageChange(pageNum)}
                            className="w-8 h-8 p-0"
                          >
                            {pageNum}
                          </Button>
                        )
                      })}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? 'No transactions found matching your search' : 'No transactions available'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 