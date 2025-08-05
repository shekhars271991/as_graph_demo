'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  User, 
  Mail, 
  MapPin, 
  Calendar, 
  Shield, 
  Loader2, 
  ArrowLeft, 
  CreditCard, 
  DollarSign, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  Phone,
  Building,
  ExternalLink,
  Smartphone,
  Monitor,
  Tablet,
  Users
} from 'lucide-react'
import { api } from '@/lib/api'
import Link from 'next/link'
import { useParams } from 'next/navigation'

interface User {
  id: string
  name: string
  email: string
  age: number
  signup_date: string
  location: string
  risk_score: number
  is_flagged: boolean
  phone?: string
  occupation?: string
}

interface Account {
  id: string
  account_type: string
  balance: number
  created_date: string
  fraud_flag?: boolean
}

interface Transaction {
  id: string
  amount: number
  currency: string
  timestamp: string
  status: string
  fraud_score: number
  fraud_status?: string
  fraud_reason?: string
  transaction_type?: string

  location?: string
  is_fraud?: boolean
  fraud_type?: string
}

interface Device {
  id: string
  type: string
  os: string
  browser: string
  fraud_flag?: boolean
}

interface ConnectedDeviceUser {
  user_id: string
  name: string
  email: string
  risk_score: number
  shared_devices: Device[]
  shared_device_count: number
}

interface UserSummary {
  user: User
  accounts: Account[]
  recent_transactions: Transaction[]
  total_transactions: number
  total_amount_sent: number
  total_amount_received: number
  fraud_risk_level: string
  connected_users: string[]
  devices?: Device[]
}

export default function UserDetailPage() {
  const params = useParams()
  const userId = params.id as string
  
  const [userDetails, setUserDetails] = useState<UserSummary | null>(null)
  const [connectedDeviceUsers, setConnectedDeviceUsers] = useState<ConnectedDeviceUser[]>([])
  const [loading, setLoading] = useState(true)
  const [connectionsLoading, setConnectionsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (userId) {
      loadUserDetails()
    }
  }, [userId])

  const loadUserDetails = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.get(`/user/${userId}/summary`)
      setUserDetails(response.data)
    } catch (error) {
      console.error('Failed to load user details:', error)
      setError('Failed to load user details. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const loadConnectedDeviceUsers = async () => {
    if (!userId || connectedDeviceUsers.length > 0) return // Don't reload if already loaded
    
    setConnectionsLoading(true)
    try {
      const response = await api.get(`/user/${userId}/connected-devices`)
      setConnectedDeviceUsers(response.data.connected_users || [])
    } catch (error) {
      console.error('Failed to load connected device users:', error)
    } finally {
      setConnectionsLoading(false)
    }
  }

  const getRiskLevel = (score: number) => {
    if (score < 25) return { level: 'Low', color: 'success' }
    if (score < 50) return { level: 'Medium', color: 'warning' }
    if (score < 75) return { level: 'High', color: 'destructive' }
    return { level: 'Critical', color: 'destructive' }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount)
  }

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType.toLowerCase()) {
      case 'mobile':
        return <Smartphone className="h-4 w-4" />
      case 'desktop':
        return <Monitor className="h-4 w-4" />
      case 'tablet':
        return <Tablet className="h-4 w-4" />
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    if (value === 'connections') {
      loadConnectedDeviceUsers()
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/users">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Users
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading user details...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !userDetails) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/users">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Users
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <p className="text-destructive font-medium">{error || 'User not found'}</p>
              <Button onClick={loadUserDetails} className="mt-4">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const risk = getRiskLevel(userDetails.user.risk_score)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/users">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Users
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{userDetails.user.name}</h1>
            <p className="text-muted-foreground">User ID: {userDetails.user.id}</p>
          </div>
        </div>
        <Badge variant={risk.color as any} className="text-lg px-4 py-2">
          {risk.level} Risk ({userDetails.user.risk_score.toFixed(1)})
        </Badge>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Transactions</p>
                <p className="text-2xl font-bold">{userDetails.total_transactions}</p>
              </div>
              <Activity className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Amount Sent</p>
                <p className="text-2xl font-bold text-destructive">
                  {formatCurrency(userDetails.total_amount_sent)}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-destructive" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Amount Received</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(userDetails.total_amount_received)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Accounts</p>
                <p className="text-2xl font-bold">{userDetails.accounts.length}</p>
              </div>
              <CreditCard className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="accounts">Accounts</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Personal Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Full Name</p>
                    <p className="text-lg font-semibold">{userDetails.user.name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Age</p>
                    <p className="text-lg font-semibold">{userDetails.user.age} years</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Email</p>
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <p className="text-lg font-semibold">{userDetails.user.email}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Phone</p>
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <p className="text-lg font-semibold">{userDetails.user.phone || 'N/A'}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Location</p>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <p className="text-lg font-semibold">{userDetails.user.location}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Occupation</p>
                    <div className="flex items-center gap-2">
                      <Building className="h-4 w-4 text-muted-foreground" />
                      <p className="text-lg font-semibold">{userDetails.user.occupation || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Risk Score</p>
                    <div className="flex items-center gap-2">
                      <div className="text-2xl font-bold">{userDetails.user.risk_score.toFixed(1)}</div>
                      <Badge variant={risk.color as any}>{risk.level}</Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Signup Date</p>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <p className="text-lg font-semibold">{formatDate(userDetails.user.signup_date)}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Account Status</p>
                    <div className="flex items-center gap-2">
                                             {userDetails.user.is_flagged ? (
                         <>
                           <AlertTriangle className="h-4 w-4 text-destructive" />
                           <Badge variant="destructive">Flagged</Badge>
                         </>
                       ) : (
                         <>
                           <CheckCircle className="h-4 w-4 text-green-600" />
                           <Badge variant="default">Active</Badge>
                         </>
                       )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Accounts Tab */}
        <TabsContent value="accounts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                User Accounts ({userDetails.accounts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {userDetails.accounts.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {userDetails.accounts.map((account) => (
                    <Card key={account.id} className="p-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-semibold capitalize">{account.account_type} Account</p>
                              {account.fraud_flag && (
                                <Badge variant="destructive" className="text-xs flex items-center gap-1">
                                  <AlertTriangle className="h-3 w-3" />
                                  FRAUD
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">ID: {account.id}</p>
                          </div>
                          <CreditCard className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Balance</p>
                          <p className={`text-2xl font-bold ${account.balance < 0 ? 'text-destructive' : 'text-green-600'}`}>
                            {formatCurrency(account.balance)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Created</p>
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <p className="text-sm">{formatDate(account.created_date)}</p>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No accounts found for this user.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Recent Transactions ({userDetails.recent_transactions.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {userDetails.recent_transactions.length > 0 ? (
                <div className="space-y-4">
                  {userDetails.recent_transactions.map((transaction) => (
                    <Card key={transaction.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-semibold">
                                  {transaction.transaction_type ? 
                                    `${transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)} Transaction` : 
                                    'Transfer Transaction'}
                                </p>
                                <Badge variant="secondary" className="text-xs font-mono">
                                  {transaction.id.substring(0, 8)}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground font-mono" title={transaction.id}>
                                ID: {transaction.id}
                              </p>
                              {transaction.location && (
                                <p className="text-sm text-muted-foreground">
                                  <MapPin className="h-3 w-3 inline mr-1" />
                                  {transaction.location}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right space-y-1">
                          <div className="flex items-center gap-2">
                            <p className={`text-lg font-bold ${transaction.amount < 0 ? 'text-destructive' : 'text-green-600'}`}>
                              {formatCurrency(Math.abs(transaction.amount))}
                            </p>
                            {transaction.amount < 0 ? (
                              <TrendingDown className="h-4 w-4 text-destructive" />
                            ) : (
                              <TrendingUp className="h-4 w-4 text-green-600" />
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant={transaction.status === 'completed' ? 'default' : 'secondary'}
                              className="text-xs"
                            >
                              {transaction.status === 'completed' ? (
                                <CheckCircle className="h-3 w-3 mr-1" />
                              ) : (
                                <Clock className="h-3 w-3 mr-1" />
                              )}
                              {transaction.status}
                            </Badge>
                            {transaction.is_fraud && (
                              <Badge variant="destructive" className="text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Fraud
                              </Badge>
                            )}
                          </div>
                                                     <div className="flex items-center gap-2">
                             <Badge variant="secondary" className="text-xs">
                               Score: {(transaction.fraud_score || 0).toFixed(1)}
                             </Badge>
                            <p className="text-xs text-muted-foreground">
                              {formatDateTime(transaction.timestamp)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No transactions found for this user.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Devices Tab */}
        <TabsContent value="devices" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                User Devices ({userDetails.devices?.length || 0})
              </CardTitle>
              <CardDescription>
                Devices associated with this user account
              </CardDescription>
            </CardHeader>
            <CardContent>
              {userDetails.devices && userDetails.devices.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
                  {userDetails.devices.map((device) => (
                                         <Card key={device.id} className="p-4 hover:shadow-md transition-shadow">
                       <div className="space-y-3">
                         <div className="flex items-start justify-between">
                           <div className="flex items-center gap-3">
                             {getDeviceIcon(device.type)}
                             <div>
                               <div className="flex items-center gap-2">
                                 <p className="font-semibold capitalize">{device.type}</p>
                                 {device.fraud_flag && (
                                   <Badge variant="destructive" className="text-xs flex items-center gap-1">
                                     <AlertTriangle className="h-3 w-3" />
                                     FRAUD
                                   </Badge>
                                 )}
                               </div>
                               <p className="text-sm text-muted-foreground">{device.os}</p>
                               <p className="text-xs text-muted-foreground">{device.browser}</p>
                             </div>
                           </div>
                           <Badge variant="secondary" className="text-xs">
                             {device.id}
                           </Badge>
                         </div>
                       </div>
                     </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Smartphone className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No devices found for this user.</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    This user doesn't have any registered devices.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-6">
          {/* Device Connections Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Device Connections
              </CardTitle>
              <CardDescription>
                Users who share devices with this user
              </CardDescription>
            </CardHeader>
            <CardContent>
              {connectionsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Loading device connections...</span>
                  </div>
                </div>
              ) : connectedDeviceUsers.length > 0 ? (
                <div className="space-y-4">
                  {connectedDeviceUsers.map((connectedUser) => (
                    <Card key={connectedUser.user_id} className="p-4 hover:shadow-md transition-all duration-200 cursor-pointer group" 
                          onClick={() => window.open(`/users/${connectedUser.user_id}`, '_blank')}>
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="relative">
                              <User className="h-10 w-10 text-muted-foreground group-hover:text-primary transition-colors" />
                              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-primary rounded-full flex items-center justify-center">
                                <Smartphone className="h-2.5 w-2.5 text-white" />
                              </div>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-semibold text-lg group-hover:text-primary transition-colors">
                                  {connectedUser.name}
                                </p>
                                <Badge 
                                  variant={connectedUser.risk_score > 50 ? 'destructive' : connectedUser.risk_score > 25 ? 'default' : 'secondary'}
                                  className="text-xs"
                                >
                                  Risk: {connectedUser.risk_score.toFixed(1)}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{connectedUser.email}</p>
                              <p className="text-xs text-muted-foreground">ID: {connectedUser.user_id}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <ExternalLink className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">View Profile</span>
                          </div>
                        </div>
                        
                        <div className="border-t pt-3">
                          <div className="flex items-center gap-2 mb-3">
                            <Smartphone className="h-4 w-4 text-muted-foreground" />
                            <p className="text-sm font-medium text-muted-foreground">
                              Shared Devices ({connectedUser.shared_device_count})
                            </p>
                          </div>
                                                     <div className="space-y-2">
                             {connectedUser.shared_devices.map((device) => (
                               <div key={device.id} className="flex items-center gap-2 p-2 bg-muted/50 rounded-md border">
                                 {getDeviceIcon(device.type)}
                                 <div className="flex-1 min-w-0">
                                   <p className="text-sm font-medium truncate">{device.type} - {device.os}</p>
                                   <p className="text-xs text-muted-foreground truncate">{device.browser}</p>
                                 </div>
                                 <Badge variant="secondary" className="text-xs shrink-0">
                                   {device.id}
                                 </Badge>
                               </div>
                             ))}
                           </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Smartphone className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No device connections found.</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    This user doesn't share any devices with other users.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Future Connection Types - Placeholder */}
          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Other Connections
              </CardTitle>
              <CardDescription>
                Additional connection types will be available soon
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-6">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Coming Soon</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Transaction connections, location-based connections, and more will be available here.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 