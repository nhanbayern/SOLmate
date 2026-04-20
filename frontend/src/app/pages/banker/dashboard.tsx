import { useNavigate } from "react-router";
import { useEffect, useState } from "react";
import BankerLayout from "../../components/banker-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { formatCurrency, formatPercentage, getRiskLabelColor } from "../../data/mockData";
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { TrendingUp, Users, AlertTriangle, DollarSign, Loader2 } from "lucide-react";
import { getStats, getLoans, getMerchants } from "../../lib/api";

const RISK_COLORS: Record<string, string> = {
  GOOD: "#10B981",
  VERY_GOOD: "#059669",
  MEDIUM: "#F59E0B",
  POOR: "#F97316",
  VERY_POOR: "#EF4444",
  UNKNOWN: "#9CA3AF",
};

export default function BankerDashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState<any>(null);
  const [loans, setLoans] = useState<any[]>([]);
  const [merchants, setMerchants] = useState<Map<string, any>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("bankerLoggedIn");
    if (!token) {
      navigate("/banker/login");
      return;
    }

    async function load() {
      try {
        setLoading(true);
        // GET /api/stats  +  GET /api/loans  +  GET /api/merchants  (parallel)
        const [statsRes, loansRes, merchantsRes] = await Promise.all([
          getStats(),
          getLoans(100, 0),
          getMerchants(),
        ]);

        setStats(statsRes?.data ?? statsRes ?? null);

        const loansData: any[] = loansRes?.data ?? [];
        setLoans(loansData);

        const mMap = new Map<string, any>();
        for (const m of (merchantsRes?.data ?? [])) {
          mMap.set(m.id, m);
        }
        setMerchants(mMap);
      } catch (err) {
        console.error("Dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [navigate]);

  // ── Derived metrics from live data ──────────────────────────────────────────
  const totalLoans = loans.length;
  const pendingLoans = loans.filter((l) => l.status === "PENDING").length;
  const approvedLoans = loans.filter((l) => l.status === "APPROVED").length;
  const rejectedLoans = loans.filter((l) => l.status === "REJECTED").length;

  const riskDist = loans.reduce<Record<string, number>>((acc, l) => {
    const label = l.risk_label || "UNKNOWN";
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});
  const riskPieData = Object.entries(riskDist).map(([name, value]) => ({ name, value }));

  const avgPD =
    loans.length > 0
      ? loans.reduce((sum, l) => sum + (l.pd_value ?? 0), 0) / loans.length
      : 0;

  const highRiskCount = loans.filter(
    (l) => l.risk_label === "POOR" || l.risk_label === "VERY_POOR"
  ).length;

  // Status bar data
  const statusData = [
    { name: "PENDING", value: pendingLoans, fill: "#F59E0B" },
    { name: "APPROVED", value: approvedLoans, fill: "#10B981" },
    { name: "REJECTED", value: rejectedLoans, fill: "#EF4444" },
  ];

  if (loading) {
    return (
      <BankerLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </BankerLayout>
    );
  }

  return (
    <BankerLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Credit Risk Dashboard</h1>
          <p className="text-muted-foreground">Tổng quan danh mục tín dụng và phân tích rủi ro</p>
        </div>

        {/* KPI Cards — từ GET /api/stats nếu có, fallback sang loans derived */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Loans</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_loans ?? totalLoans}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Default Prob</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatPercentage(stats?.avg_pd ?? avgPD)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">High Risk Loans</CardTitle>
              <Users className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.high_risk_count ?? highRiskCount}</div>
              <p className="text-xs text-muted-foreground mt-1">POOR + VERY_POOR</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Pending Review</CardTitle>
              <DollarSign className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.pending_loans ?? pendingLoans}</div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Risk Label Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={80}
                    dataKey="value"
                  >
                    {riskPieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={RISK_COLORS[entry.name] || "#9CA3AF"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Loan Status Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Recent Loan Requests Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Loan Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loan ID</TableHead>
                  <TableHead>Customer ID</TableHead>
                  <TableHead>Merchant</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>PD</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loans.slice(0, 20).map((loan) => {
                  const mer = merchants.get(loan.merchant_id);
                  return (
                    <TableRow key={loan.id}>
                      <TableCell className="font-mono text-xs">{loan.id}</TableCell>
                      <TableCell className="text-xs">{loan.customer_id}</TableCell>
                      <TableCell className="text-xs">{mer?.owner_name || mer?.name || loan.merchant_id}</TableCell>
                      <TableCell>{formatCurrency(loan.requested_amount ?? 0)}</TableCell>
                      <TableCell>
                        <Badge className={getRiskLabelColor(loan.risk_label || "UNKNOWN")}>
                          {loan.risk_label || "N/A"}
                        </Badge>
                      </TableCell>
                      <TableCell>{loan.pd_value != null ? formatPercentage(loan.pd_value) : "—"}</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            loan.status === "APPROVED"
                              ? "bg-green-100 text-green-800"
                              : loan.status === "REJECTED"
                              ? "bg-red-100 text-red-800"
                              : loan.status === "PENDING"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-gray-100 text-gray-800"
                          }
                        >
                          {loan.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/banker/loan-requests/${loan.id}`)}
                        >
                          Chi tiết
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {loans.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-6 text-muted-foreground">
                      Không có dữ liệu
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </BankerLayout>
  );
}
