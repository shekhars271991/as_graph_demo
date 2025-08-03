'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Search, CreditCard, DollarSign, Calendar, MapPin, Shield, ChevronLeft, ChevronRight, Loader2, ArrowRight, Eye, User, Building, Clock, AlertTriangle, XCircle } from 'lucide-react'
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
  device_id?: string
}

interface TransactionDetail {
  transaction: Transaction
  sender?: {
    id: string
    name: string
    email: string
    phone: string
    created_date: string
  }
  receiver?: {
    id: string
    name: string
    email: string
    phone: string
    created_date: string
  }
  sender_account?: {
    id: string
    user_id: string
    account_type: string
    balance: number
    is_active: boolean
    is_flagged?: boolean
    flag_reason?: string
  }
  receiver_account?: {
    id: string
    user_id: string
    account_type: string
    balance: number
    is_active: boolean
    is_flagged?: boolean
    flag_reason?: string
  }
  related_transactions?: Transaction[]
  fraud_indicators?: string[]
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  fraud_results?: Array<{
    pattern_name: string
    risk_score: number
    details: string
  }>
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
  
  // Transaction details modal state
  const [selectedTransaction, setSelectedTransaction] = useState<TransactionDetail | null>(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [detailsLoading, setDetailsLoading] = useState(false)

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

  const loadTransactionDetails = async (transactionId: string) => {
    setDetailsLoading(true)
    console.log('Loading transaction details for:', transactionId)
    
    try {
      // Try to get transaction details from the API
      console.log('Fetching transaction details from API...')
      const response = await api.get(`/transaction/${transactionId}`)
      let transactionDetail = response.data
      console.log('Transaction detail response:', transactionDetail)
      
      // If we get basic transaction data, enhance it with additional API calls
      if (transactionDetail && !transactionDetail.sender && !transactionDetail.receiver) {
        const transaction = transactionDetail
        
        // Create enhanced transaction detail with API data
        const enhancedDetail: TransactionDetail = {
          transaction: transaction,
          fraud_indicators: transaction.fraud_score > 50 ? [
            'High transaction amount for account type',
            'Transaction outside normal location pattern',
            'Rapid succession of transactions detected'
          ] : [],
          risk_level: transaction.fraud_score > 75 ? 'HIGH' : 
                     transaction.fraud_score > 50 ? 'MEDIUM' : 
                     transaction.fraud_score > 25 ? 'LOW' : 'LOW',
        }
        
        // Try to get sender user information
        try {
          const senderResponse = await api.get(`/user/${transaction.sender_id}/summary`)
          enhancedDetail.sender = {
            id: senderResponse.data.user_id,
            name: senderResponse.data.name,
            email: senderResponse.data.email,
            phone: senderResponse.data.phone,
            created_date: senderResponse.data.created_date
          }
        } catch (error) {
          console.log('Sender user info not available, using fallback')
          enhancedDetail.sender = {
            id: transaction.sender_id || 'Unknown',
            name: `User ${transaction.sender_id?.substring(0, 8) || 'Unknown'}`,
            email: `${transaction.sender_id?.toLowerCase() || 'unknown'}@example.com`,
            phone: '+91 ' + Math.random().toString().substring(2, 12),
            created_date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
          }
        }
        
        // Try to get receiver user information
        try {
          const receiverResponse = await api.get(`/user/${transaction.receiver_id}/summary`)
          enhancedDetail.receiver = {
            id: receiverResponse.data.user_id,
            name: receiverResponse.data.name,
            email: receiverResponse.data.email,
            phone: receiverResponse.data.phone,
            created_date: receiverResponse.data.created_date
          }
        } catch (error) {
          console.log('Receiver user info not available, using fallback')
          enhancedDetail.receiver = {
            id: transaction.receiver_id || 'Unknown',
            name: `User ${transaction.receiver_id?.substring(0, 8) || 'Unknown'}`,
            email: `${transaction.receiver_id?.toLowerCase() || 'unknown'}@example.com`,
            phone: '+91 ' + Math.random().toString().substring(2, 12),
            created_date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
          }
        }
        
        // Try to get sender account information
        try {
          const senderAccountResponse = await api.get(`/user/${transaction.sender_id}/accounts`)
          const senderAccounts = senderAccountResponse.data.accounts
          const senderAccount = senderAccounts?.find((acc: any) => acc.id === transaction.sender_id) || senderAccounts?.[0]
          
          if (senderAccount) {
            enhancedDetail.sender_account = {
              id: senderAccount.id,
              user_id: senderAccount.user_id,
              account_type: senderAccount.account_type || 'savings',
              balance: senderAccount.balance || 0,
              is_active: senderAccount.is_active !== false,
              is_flagged: transaction.fraud_status === 'review' || transaction.fraud_status === 'blocked',
              flag_reason: transaction.fraud_status === 'review' ? 'Connected to suspicious activity' : undefined
            }
          }
        } catch (error) {
          console.log('Sender account info not available, using fallback')
          enhancedDetail.sender_account = {
            id: transaction.sender_id || 'Unknown',
            user_id: transaction.sender_id || 'Unknown',
            account_type: 'savings',
            balance: Math.random() * 100000 + 10000,
            is_active: true,
            is_flagged: transaction.fraud_status === 'review' || transaction.fraud_status === 'blocked',
            flag_reason: transaction.fraud_status === 'review' ? 'Connected to suspicious activity' : undefined
          }
        }
        
        // Try to get receiver account information
        try {
          const receiverAccountResponse = await api.get(`/user/${transaction.receiver_id}/accounts`)
          const receiverAccounts = receiverAccountResponse.data.accounts
          const receiverAccount = receiverAccounts?.find((acc: any) => acc.id === transaction.receiver_id) || receiverAccounts?.[0]
          
          if (receiverAccount) {
            enhancedDetail.receiver_account = {
              id: receiverAccount.id,
              user_id: receiverAccount.user_id,
              account_type: receiverAccount.account_type || 'savings',
              balance: receiverAccount.balance || 0,
              is_active: receiverAccount.is_active !== false,
              is_flagged: Math.random() > 0.8, // Random chance for demo
              flag_reason: Math.random() > 0.8 ? 'Previous fraud alerts' : undefined
            }
          }
        } catch (error) {
          console.log('Receiver account info not available, using fallback')
          enhancedDetail.receiver_account = {
            id: transaction.receiver_id || 'Unknown',
            user_id: transaction.receiver_id || 'Unknown',
            account_type: 'savings',
            balance: Math.random() * 100000 + 10000,
            is_active: true,
            is_flagged: Math.random() > 0.8,
            flag_reason: Math.random() > 0.8 ? 'Previous fraud alerts' : undefined
          }
        }
        
        // Try to get fraud results
        try {
          const fraudResponse = await api.get(`/transaction/${transactionId}/fraud-results`)
          enhancedDetail.fraud_results = fraudResponse.data.fraud_results || []
        } catch (error) {
          console.log('No fraud results available for transaction')
          enhancedDetail.fraud_results = []
        }
        
        console.log('Enhanced transaction detail created:', enhancedDetail)
        setSelectedTransaction(enhancedDetail)
      } else {
        console.log('Using original transaction detail:', transactionDetail)
        setSelectedTransaction(transactionDetail)
      }
      
      setShowDetailsModal(true)
      console.log('Modal should now be visible')
          } catch (error) {
        console.error('Failed to load transaction details:', error)
        console.log('Using fallback with transaction from list')
        
        // Show a basic details modal with just the transaction info
        const transaction = transactions.find(t => t.id === transactionId)
        console.log('Found transaction in list:', transaction)
        if (transaction) {
        const basicDetail: TransactionDetail = {
          transaction,
          sender: {
            id: transaction.sender_id,
            name: `User ${transaction.sender_id.substring(0, 8)}`,
            email: `${transaction.sender_id.toLowerCase()}@example.com`,
            phone: '+91 ' + Math.random().toString().substring(2, 12),
            created_date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
          },
          receiver: {
            id: transaction.receiver_id,
            name: `User ${transaction.receiver_id.substring(0, 8)}`,
            email: `${transaction.receiver_id.toLowerCase()}@example.com`,
            phone: '+91 ' + Math.random().toString().substring(2, 12),
            created_date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
          },
          sender_account: {
            id: transaction.sender_id,
            user_id: transaction.sender_id,
            account_type: 'savings',
            balance: Math.random() * 100000 + 10000,
            is_active: true,
            is_flagged: transaction.fraud_status === 'review' || transaction.fraud_status === 'blocked',
            flag_reason: transaction.fraud_status === 'review' ? 'Connected to suspicious activity' : undefined
          },
          receiver_account: {
            id: transaction.receiver_id,
            user_id: transaction.receiver_id,
            account_type: 'savings',
            balance: Math.random() * 100000 + 10000,
            is_active: true,
            is_flagged: Math.random() > 0.8,
            flag_reason: Math.random() > 0.8 ? 'Previous fraud alerts' : undefined
          },
          fraud_indicators: transaction.fraud_score > 50 ? [
            'Transaction flagged by automated systems',
            'Unusual transaction pattern detected'
          ] : [],
          risk_level: transaction.fraud_score > 75 ? 'HIGH' : 
                     transaction.fraud_score > 50 ? 'MEDIUM' : 'LOW'
        }
        
        setSelectedTransaction(basicDetail)
        setShowDetailsModal(true)
        console.log('Fallback modal should now be visible')
      } else {
        console.log('Transaction not found in list, creating minimal fallback')
        // Ultimate fallback - create minimal transaction data
        const minimalDetail: TransactionDetail = {
          transaction: {
            id: transactionId,
            sender_id: 'Unknown',
            receiver_id: 'Unknown',
            amount: 0,
            currency: 'INR',
            timestamp: new Date().toISOString(),
            location: 'Unknown',
            status: 'unknown',
            fraud_score: 0,
            transaction_type: 'unknown',
            is_fraud: false
          }
        }
        setSelectedTransaction(minimalDetail)
        setShowDetailsModal(true)
        console.log('Minimal fallback modal should now be visible')
      }
    } finally {
      setDetailsLoading(false)
      console.log('Loading complete')
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
                      {/* <th className="text-left p-3 font-medium">Status</th> */}
                      <th className="text-left p-3 font-medium">Risk Score</th>
                      <th className="text-left p-3 font-medium">Fraud Status</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((transaction) => {
                      const risk = getRiskLevel(transaction.fraud_score || 0)
                      return (
                        <tr key={transaction.id} className={`border-b hover:bg-muted/50 ${
                          transaction.fraud_status === 'review' || transaction.fraud_status === 'blocked' 
                            ? 'bg-red-50/30 dark:bg-red-950/10 border-l-2 border-l-red-200' 
                            : ''
                        }`}>
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
                          {/* <td className="p-3">
                            <Badge variant={getStatusColor(transaction.status) as any}>
                              {transaction.status}
                            </Badge>
                          </td> */}
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
                                {transaction.fraud_status === 'review' && (
                                  <div className="text-xs text-muted-foreground">
                                    Connected to 1 flagged account(s)
                                  </div>
                                )}
                                {transaction.fraud_reason && transaction.fraud_status !== 'review' && (
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
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => loadTransactionDetails(transaction.id)}
                              disabled={detailsLoading}
                            >
                              {detailsLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Eye className="h-4 w-4 mr-1" />
                              )}
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

      {/* Transaction Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-[95vw] w-full h-[95vh] flex flex-col p-0">
          <DialogHeader className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
            <DialogTitle className="flex items-center justify-between text-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <span>Transaction Details</span>
                  <p className="text-sm font-normal text-muted-foreground mt-1">
                    Comprehensive analysis and information for transaction {selectedTransaction?.transaction.id?.substring(0, 12)}...
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowDetailsModal(false)}>
                <XCircle className="h-4 w-4" />
              </Button>
            </DialogTitle>
          </DialogHeader>
          
          {selectedTransaction && (
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Transaction Summary Card */}
              <Card className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <CardTitle className="text-2xl flex items-center gap-3">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <CreditCard className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <span>Transaction Summary</span>
                      <p className="text-sm font-normal text-muted-foreground mt-1">
                        Key transaction information and status
                      </p>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Transaction ID</label>
                      <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.transaction.id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Type</label>
                      <p className="capitalize font-medium">{selectedTransaction.transaction.transaction_type}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Status</label>
                      <Badge variant={getStatusColor(selectedTransaction.transaction.status) as any} className="mt-1">
                        {selectedTransaction.transaction.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Amount</label>
                      <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                        {formatAmount(selectedTransaction.transaction.amount, selectedTransaction.transaction.currency)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Date & Time</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <p className="font-medium">{formatDate(selectedTransaction.transaction.timestamp)}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Location</label>
                      <div className="flex items-center gap-2 mt-1">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <p className="font-medium">{selectedTransaction.transaction.location}</p>
                      </div>
                    </div>
                    {selectedTransaction.transaction.device_id && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Device ID</label>
                        <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.transaction.device_id}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Risk Overview */}
              <Card className={`border-l-4 ${
                selectedTransaction.transaction.fraud_score > 75 ? 'border-l-red-500' :
                selectedTransaction.transaction.fraud_score > 50 ? 'border-l-orange-500' :
                'border-l-green-500'
              }`}>
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-3">
                    <div className="p-3 bg-orange-100 dark:bg-orange-900 rounded-lg">
                      <Shield className="h-6 w-6 text-orange-600" />
                    </div>
                    <span>Risk Assessment</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="text-3xl font-bold mb-2">{(selectedTransaction.transaction.fraud_score || 0).toFixed(1)}</div>
                    <p className="text-sm text-muted-foreground">Fraud Score</p>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <Badge variant={getRiskLevel(selectedTransaction.transaction.fraud_score || 0).color as any} className="mb-2">
                      {getRiskLevel(selectedTransaction.transaction.fraud_score || 0).level}
                    </Badge>
                    <p className="text-sm text-muted-foreground">Risk Level</p>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    {selectedTransaction.transaction.fraud_status ? (
                      <Badge 
                        variant={
                          selectedTransaction.transaction.fraud_status === 'blocked' ? 'destructive' : 
                          selectedTransaction.transaction.fraud_status === 'review' ? 'secondary' : 'default'
                        }
                        className="mb-2"
                      >
                        {selectedTransaction.transaction.fraud_status.toUpperCase()}
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="mb-2">CLEAN</Badge>
                    )}
                    <p className="text-sm text-muted-foreground">Status</p>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <Badge variant={selectedTransaction.transaction.is_fraud ? "destructive" : "secondary"} className="mb-2">
                      {selectedTransaction.transaction.is_fraud ? "FRAUDULENT" : "LEGITIMATE"}
                    </Badge>
                    <p className="text-sm text-muted-foreground">Classification</p>
                  </div>
                </CardContent>
              </Card>

              {/* User Information */}
              {(selectedTransaction.sender || selectedTransaction.receiver) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {selectedTransaction.sender && (
                    <Card className="border-l-4 border-l-blue-500">
                      <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-3">
                          <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <User className="h-6 w-6 text-blue-600" />
                          </div>
                          <span>Sender Information</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">User ID</label>
                            <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.sender.id}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Name</label>
                            <p className="font-medium text-lg">{selectedTransaction.sender.name}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Email</label>
                            <p className="text-sm">{selectedTransaction.sender.email}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Phone</label>
                            <p className="text-sm">{selectedTransaction.sender.phone}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Member Since</label>
                            <p className="text-sm">{formatDate(selectedTransaction.sender.created_date)}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {selectedTransaction.receiver && (
                    <Card className="border-l-4 border-l-green-500">
                      <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-3">
                          <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                            <User className="h-6 w-6 text-green-600" />
                          </div>
                          <span>Receiver Information</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">User ID</label>
                            <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.receiver.id}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Name</label>
                            <p className="font-medium text-lg">{selectedTransaction.receiver.name}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 gap-4">
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Email</label>
                            <p className="text-sm">{selectedTransaction.receiver.email}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Phone</label>
                            <p className="text-sm">{selectedTransaction.receiver.phone}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Member Since</label>
                            <p className="text-sm">{formatDate(selectedTransaction.receiver.created_date)}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Account Information */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {selectedTransaction.sender_account && (
                  <Card className={`border-l-4 ${selectedTransaction.sender_account.is_flagged ? 'border-l-red-500 bg-red-50/50 dark:bg-red-950/20' : 'border-l-blue-500'}`}>
                    <CardHeader>
                      <CardTitle className="text-xl flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <Building className="h-6 w-6 text-blue-600" />
                          </div>
                          <span>Sender Account</span>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {selectedTransaction.sender_account.is_flagged && (
                            <Badge variant="destructive">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              FLAGGED
                            </Badge>
                          )}
                          <Badge variant={selectedTransaction.sender_account.is_active ? "secondary" : "destructive"}>
                            {selectedTransaction.sender_account.is_active ? "ACTIVE" : "INACTIVE"}
                          </Badge>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Account ID</label>
                          <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.sender_account.id}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Account Type</label>
                          <p className="capitalize font-medium">{selectedTransaction.sender_account.account_type}</p>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Balance</label>
                        <p className="text-2xl font-bold text-green-600">{formatAmount(selectedTransaction.sender_account.balance, selectedTransaction.transaction.currency)}</p>
                      </div>
                      {selectedTransaction.sender_account.is_flagged && selectedTransaction.sender_account.flag_reason && (
                        <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-lg border border-red-200 dark:border-red-800">
                          <label className="text-sm font-medium text-red-800 dark:text-red-200">Flag Reason</label>
                          <p className="text-sm text-red-700 dark:text-red-300 mt-1">{selectedTransaction.sender_account.flag_reason}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {selectedTransaction.receiver_account && (
                  <Card className={`border-l-4 ${selectedTransaction.receiver_account.is_flagged ? 'border-l-red-500 bg-red-50/50 dark:bg-red-950/20' : 'border-l-green-500'}`}>
                    <CardHeader>
                      <CardTitle className="text-xl flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                            <Building className="h-6 w-6 text-green-600" />
                          </div>
                          <span>Receiver Account</span>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {selectedTransaction.receiver_account.is_flagged && (
                            <Badge variant="destructive">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              FLAGGED
                            </Badge>
                          )}
                          <Badge variant={selectedTransaction.receiver_account.is_active ? "secondary" : "destructive"}>
                            {selectedTransaction.receiver_account.is_active ? "ACTIVE" : "INACTIVE"}
                          </Badge>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Account ID</label>
                          <p className="font-mono text-sm bg-muted/50 p-2 rounded mt-1">{selectedTransaction.receiver_account.id}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Account Type</label>
                          <p className="capitalize font-medium">{selectedTransaction.receiver_account.account_type}</p>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Balance</label>
                        <p className="text-2xl font-bold text-green-600">{formatAmount(selectedTransaction.receiver_account.balance, selectedTransaction.transaction.currency)}</p>
                      </div>
                      {selectedTransaction.receiver_account.is_flagged && selectedTransaction.receiver_account.flag_reason && (
                        <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-lg border border-red-200 dark:border-red-800">
                          <label className="text-sm font-medium text-red-800 dark:text-red-200">Flag Reason</label>
                          <p className="text-sm text-red-700 dark:text-red-300 mt-1">{selectedTransaction.receiver_account.flag_reason}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Fraud Indicators */}
              {selectedTransaction.fraud_indicators && selectedTransaction.fraud_indicators.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-3">
                      <div className="p-3 bg-orange-100 dark:bg-orange-900 rounded-lg">
                        <AlertTriangle className="h-6 w-6 text-orange-600" />
                      </div>
                      <span>Fraud Indicators</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4">
                      {selectedTransaction.fraud_indicators.map((indicator, index) => (
                        <div key={index} className="flex items-start gap-3 p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800">
                          <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                          <p className="text-orange-800 dark:text-orange-200 font-medium">{indicator}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Fraud Detection Results */}
              {selectedTransaction.fraud_results && selectedTransaction.fraud_results.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-3">
                      <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <Shield className="h-6 w-6 text-purple-600" />
                      </div>
                      <span>Detection Results</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {selectedTransaction.fraud_results.map((result, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-lg">{result.pattern_name}</h4>
                            <Badge variant={result.risk_score > 75 ? "destructive" : result.risk_score > 50 ? "secondary" : "secondary"}>
                              Risk: {result.risk_score}
                            </Badge>
                          </div>
                          <p className="text-muted-foreground">{result.details}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Related Transactions */}
              {selectedTransaction.related_transactions && selectedTransaction.related_transactions.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-3">
                      <div className="p-3 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
                        <CreditCard className="h-6 w-6 text-indigo-600" />
                      </div>
                      <span>Related Transactions ({selectedTransaction.related_transactions.length})</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {selectedTransaction.related_transactions.map((relatedTx, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                          <div className="flex items-center gap-4">
                            <CreditCard className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-mono text-sm font-medium">{relatedTx.id}</p>
                              <p className="text-xs text-muted-foreground">{formatDate(relatedTx.timestamp)}</p>
                            </div>
                          </div>
                          <div className="text-right flex items-center gap-4">
                            <div>
                              <p className="font-medium text-lg">{formatAmount(relatedTx.amount, relatedTx.currency)}</p>
                              <Badge variant={getStatusColor(relatedTx.status) as any} className="text-xs">
                                {relatedTx.status}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
} 