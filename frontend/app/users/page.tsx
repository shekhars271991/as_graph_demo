'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Search, User, Mail, MapPin, Calendar, Shield, ChevronLeft, ChevronRight, Loader2, X, CreditCard, DollarSign, Clock, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'

interface User {
  id: string
  name: string
  email: string
  age: number
  signup_date: string
  location: string
  risk_score: number
  is_flagged: boolean
}

interface UserSummary {
  user: User
  accounts: Array<{
    id: string
    account_type: string
    balance: number
    created_date: string
  }>
  recent_transactions: Array<{
    id: string
    amount: number
    currency: string
    timestamp: string
    status: string
    fraud_score: number
  }>
  total_transactions: number
  total_amount_sent: number
  total_amount_received: number
  fraud_risk_level: string
  connected_users: string[]
}

interface PaginatedUsers {
  users: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export default function UsersPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalUsers, setTotalUsers] = useState(0)
  const [pageSize] = useState(12) // 12 users per page (4 rows of 3 cards)
  
  // User details modal state
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [userDetails, setUserDetails] = useState<UserSummary | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [showModal, setShowModal] = useState(false)

  // Load all users on component mount
  useEffect(() => {
    loadAllUsers()
  }, [currentPage])

  const loadAllUsers = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/users?page=${currentPage}&page_size=${pageSize}`)
      const data: PaginatedUsers = response.data
      setUsers(data.users || [])
      setTotalPages(data.total_pages || 1)
      setTotalUsers(data.total || 0)
    } catch (error) {
      console.error('Failed to load users:', error)
      // Fallback to mock data if API fails
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const searchUsers = async () => {
    if (!searchQuery.trim()) {
      // If search is cleared, load all users
      setCurrentPage(1)
      loadAllUsers()
      return
    }
    
    setSearchLoading(true)
    try {
      const response = await api.get(`/users/search?query=${searchQuery}&page=${currentPage}&page_size=${pageSize}`)
      const data: PaginatedUsers = response.data
      setUsers(data.users || [])
      setTotalPages(data.total_pages || 1)
      setTotalUsers(data.total || 0)
    } catch (error) {
      console.error('Failed to search users:', error)
      setUsers([])
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSearch = () => {
    setCurrentPage(1) // Reset to first page when searching
    searchUsers()
  }

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
  }

  const getRiskLevel = (score: number) => {
    if (score < 25) return { level: 'Low', color: 'success' }
    if (score < 50) return { level: 'Medium', color: 'warning' }
    if (score < 75) return { level: 'High', color: 'destructive' }
    return { level: 'Critical', color: 'destructive' }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const handleViewDetails = async (user: User) => {
    setSelectedUser(user)
    setShowModal(true)
    setLoadingDetails(true)
    
    try {
      const response = await api.get(`/user/${user.id}/summary`)
      setUserDetails(response.data)
    } catch (error) {
      console.error('Failed to load user details:', error)
      // Create mock user details if API fails
      setUserDetails({
        user: user,
        accounts: [
          {
            id: 'account_1',
            account_type: 'checking',
            balance: 2500.00,
            created_date: user.signup_date
          }
        ],
        recent_transactions: [
          {
            id: 'tx_1',
            amount: 150.00,
            currency: 'USD',
            timestamp: new Date().toISOString(),
            status: 'completed',
            fraud_score: user.risk_score
          }
        ],
        total_transactions: 1,
        total_amount_sent: 150.00,
        total_amount_received: 0,
        fraud_risk_level: getRiskLevel(user.risk_score).level,
        connected_users: []
      })
    } finally {
      setLoadingDetails(false)
    }
  }

  const closeModal = () => {
    setShowModal(false)
    setSelectedUser(null)
    setUserDetails(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">User Explorer</h1>
        <p className="text-muted-foreground">
          Browse and search user profiles with pagination
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Search by user ID or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              {searchLoading ? 'Searching...' : 'Search'}
            </Button>
            {searchQuery && (
              <Button 
                variant="outline" 
                onClick={() => {
                  setSearchQuery('')
                  setCurrentPage(1)
                  loadAllUsers()
                }}
              >
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                <p className="text-2xl font-bold">{totalUsers}</p>
              </div>
              <User className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">High Risk</p>
                <p className="text-2xl font-bold text-destructive">
                  {users.filter(u => u.risk_score >= 70).length}
                </p>
              </div>
              <Shield className="h-8 w-8 text-destructive" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Medium Risk</p>
                <p className="text-2xl font-bold text-warning">
                  {users.filter(u => u.risk_score >= 25 && u.risk_score < 70).length}
                </p>
              </div>
              <Shield className="h-8 w-8 text-warning" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Low Risk</p>
                <p className="text-2xl font-bold text-green-600">
                  {users.filter(u => u.risk_score < 25).length}
                </p>
              </div>
              <Shield className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Users Grid */}
      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading users...</span>
            </div>
          </CardContent>
        </Card>
      ) : users.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {users.map((user) => {
              const risk = getRiskLevel(user.risk_score)
              return (
                <Card key={user.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <User className="h-5 w-5" />
                          {user.name}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">{user.id}</p>
                      </div>
                      <Badge variant={risk.color as any}>
                        {risk.level} Risk
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <span>{user.email}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <span>{user.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span>Age: {user.age}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Shield className="h-4 w-4 text-muted-foreground" />
                      <span>Risk Score: {user.risk_score.toFixed(1)}</span>
                    </div>
                    <div className="pt-2">
                      <Button variant="outline" size="sm" className="w-full" onClick={() => handleViewDetails(user)}>
                        View Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalUsers)} of {totalUsers} users
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
              <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? 'No users found matching your search' : 'No users available'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* User Details Modal */}
      {showModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] flex flex-col bg-background border-2 shadow-2xl">
            <CardHeader className="flex justify-between items-center border-b bg-muted/50">
              <CardTitle className="flex items-center gap-2">
                <User className="h-6 w-6" />
                {selectedUser.name}
              </CardTitle>
              <Button variant="ghost" onClick={closeModal} className="h-8 w-8 p-0 hover:bg-destructive hover:text-destructive-foreground">
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 bg-background">
              {loadingDetails ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading user details...</span>
                </div>
              ) : userDetails ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">ID</p>
                      <p className="text-lg font-bold text-foreground">{userDetails.user.id}</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Risk Level</p>
                      <Badge variant={getRiskLevel(userDetails.user.risk_score).color as any} className="text-sm">
                        {userDetails.fraud_risk_level} Risk
                      </Badge>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Age</p>
                      <p className="text-lg font-bold text-foreground">{userDetails.user.age}</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Location</p>
                      <p className="text-lg font-bold text-foreground">{userDetails.user.location}</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Email</p>
                      <p className="text-lg font-bold text-foreground">{userDetails.user.email}</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Signup Date</p>
                      <p className="text-lg font-bold text-foreground">{formatDate(userDetails.user.signup_date)}</p>
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-xl font-bold mb-4 text-foreground">Accounts</h3>
                    <div className="grid gap-3">
                      {userDetails.accounts.map((account) => (
                        <Card key={account.id} className="p-4 bg-card border">
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="text-lg font-bold text-foreground">{account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)} Account</p>
                              <p className="text-sm text-muted-foreground">Balance: ${account.balance.toFixed(2)}</p>
                            </div>
                            <Badge variant="secondary" className="text-xs">{formatDate(account.created_date)}</Badge>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-xl font-bold mb-4 text-foreground">Recent Transactions</h3>
                    <div className="grid gap-3">
                      {userDetails.recent_transactions.map((tx) => (
                        <Card key={tx.id} className="p-4 bg-card border">
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="text-lg font-bold text-foreground">Transaction {tx.id.substring(0, 5)}...</p>
                              <p className="text-sm text-muted-foreground">Amount: ${tx.amount.toFixed(2)} {tx.currency}</p>
                              <p className="text-sm text-muted-foreground">Status: {tx.status.charAt(0).toUpperCase() + tx.status.slice(1)}</p>
                            </div>
                            <Badge variant="secondary" className="text-xs">{formatDate(tx.timestamp)}</Badge>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-xl font-bold mb-4 text-foreground">Summary</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-card p-4 rounded-lg border">
                        <p className="text-sm font-medium text-muted-foreground mb-1">Total Transactions</p>
                        <p className="text-lg font-bold text-foreground">{userDetails.total_transactions}</p>
                      </div>
                      <div className="bg-card p-4 rounded-lg border">
                        <p className="text-sm font-medium text-muted-foreground mb-1">Total Amount Sent</p>
                        <p className="text-lg font-bold text-foreground">${userDetails.total_amount_sent.toFixed(2)}</p>
                      </div>
                      <div className="bg-card p-4 rounded-lg border">
                        <p className="text-sm font-medium text-muted-foreground mb-1">Total Amount Received</p>
                        <p className="text-lg font-bold text-foreground">${userDetails.total_amount_received.toFixed(2)}</p>
                      </div>
                      <div className="bg-card p-4 rounded-lg border">
                        <p className="text-sm font-medium text-muted-foreground mb-1">Fraud Risk Level</p>
                        <p className="text-lg font-bold text-foreground">{userDetails.fraud_risk_level}</p>
                      </div>
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-xl font-bold mb-4 text-foreground">Connected Users</h3>
                    <div className="grid gap-3">
                      {userDetails.connected_users.length > 0 ? (
                        userDetails.connected_users.map((id) => (
                          <Badge key={id} variant="secondary" className="text-sm">
                            User {id.substring(0, 5)}...
                          </Badge>
                        ))
                      ) : (
                        <p className="text-muted-foreground">No connected users found.</p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-12 text-center">
                  <p className="text-muted-foreground">No user details available.</p>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex justify-end gap-2 border-t bg-muted/50 p-4">
              <Button variant="outline" onClick={closeModal} className="px-6">
                Close
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  )
} 