import React from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useEffect, useMemo, useState } from "react";

import BankerLayout from "../../components/banker-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import * as Tabs from "@radix-ui/react-tabs";
import { getLoanDetail, getMerchantDetail, getTransactions, evaluateLoan, parseReportText } from "../../lib/api";
import { applyTermMapping } from "../../lib/termMapping";
import Papa from "papaparse";

import {
  formatCurrency,
  formatPercentage,
  getLoanPurposeLabel,
  getRiskLabelColor,
  getStatusColor,
} from "../../data/mockData";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowLeft, Brain, CalendarDays, DollarSign, ShoppingCart, TrendingUp, Loader2 } from "lucide-react";

type TransactionPoint = any;

function parseTransactionDate(transaction: TransactionPoint): Date | null {
  const isoDate = transaction.transaction_time ? new Date(transaction.transaction_time) : (transaction.created_at ? new Date(transaction.created_at) : null);
  if (isoDate && !Number.isNaN(isoDate.getTime())) {
    return isoDate;
  }

  const rawDate = transaction.Date?.trim();
  if (!rawDate) return null;

  const parts = rawDate.includes("-") ? rawDate.split("-") : rawDate.split("/");
  if (parts.length !== 3) {
    const fallbackDate = new Date(rawDate);
    return Number.isNaN(fallbackDate.getTime()) ? null : fallbackDate;
  }

  const [dayPart, monthPart, yearPart] = parts.map((part: string) => Number.parseInt(part, 10));
  if ([dayPart, monthPart, yearPart].some((value: number) => Number.isNaN(value))) {
    return null;
  }

  const fullYear = yearPart < 100 ? 2000 + yearPart : yearPart;
  const parsedDate = new Date(fullYear, monthPart - 1, dayPart);
  return Number.isNaN(parsedDate.getTime()) ? null : parsedDate;
}

function toDateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function toMonthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function startOfWeek(date: Date): Date {
  const result = new Date(date);
  const day = result.getDay();
  const offset = day === 0 ? -6 : 1 - day;
  result.setDate(result.getDate() + offset);
  result.setHours(0, 0, 0, 0);
  return result;
}

function toReadableDate(dateText: string | undefined): string {
  if (!dateText) return "";
  const parsedDate = new Date(dateText);
  if (Number.isNaN(parsedDate.getTime())) {
    return dateText;
  }

  return parsedDate.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Render inline **bold** markers inside a text segment */
function renderInline(text: string, key: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  if (parts.length === 1) return text;
  return (
    <span key={key}>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        return part;
      })}
    </span>
  );
}

function renderRecommendationText(text: string): JSX.Element[] {
  // Apply Vietnamese term mapping before rendering
  const mapped = applyTermMapping(text);
  return mapped.split("\n").map((line, index) => {
    const key = `line-${index}`;

    if (line.startsWith("###")) {
      const heading = line.replace(/^###\s*/, "").trim();
      return (
        <h4 key={key} className="font-semibold text-foreground mt-4 mb-2">
          {renderInline(heading, key)}
        </h4>
      );
    }

    if (line.trim().startsWith("-")) {
      const content = line.replace(/^-\s*/, "").trim();
      return (
        <li key={key} className="text-sm text-muted-foreground ml-4 list-disc mb-1">
          {renderInline(content, key)}
        </li>
      );
    }

    if (line.trim()) {
      return (
        <p key={key} className="text-sm text-muted-foreground mb-2">
          {renderInline(line, key)}
        </p>
      );
    }

    return <div key={key} className="h-2" />;
  });
}

export default function BankerLoanRequestDetail() {
  const navigate = useNavigate();
  const { requestId } = useParams();

  const [request, setRequest] = useState<any>(null);
  const [customer, setCustomer] = useState<any>(null);
  const [customerTransactions, setCustomerTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    const loggedIn = localStorage.getItem("bankerLoggedIn");
    if (!loggedIn) {
      navigate("/banker/login");
      return;
    }

    async function loadData() {
      try {
        setLoading(true);
        if (!requestId) return;

        // GET /api/loans/:id
        const reqData = await getLoanDetail(requestId);
        console.log("[LoanDetail] loan response:", reqData);
        if (reqData?.data) {
          setRequest(reqData.data);

          // GET /api/merchants/:id
          const merData = await getMerchantDetail(reqData.data.merchant_id);
          setCustomer(merData?.data ?? null);

          // Fetch transactions from CSV directly
          Papa.parse("/random_transaction_10_firms.csv", {
            download: true,
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: (results) => {
              const filtered = results.data.filter(
                (row: any) => row.merchant_id === reqData.data.merchant_id
              );

              const normalized = filtered.map((row: any) => {
                const { created_at, ...rest } = row;
                return {
                  ...rest,
                  amount: row.Amount || row.amount || row["Tổng giá"] || row["T?ng gi"] || 0,
                  Date: row.Date || row["Ngày"] || row["Ngy"],
                };
              });

              setCustomerTransactions(normalized);
              setLoading(false);
            },
            error: (err) => {
              console.error("Error parsing CSV:", err);
              setLoading(false);
            }
          });
          
          return; // Don't set loading to false yet
        }
      } catch (err) {
        console.error("[LoanDetail] load error:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [requestId, navigate]);

  const handleEvaluate = async () => {
    if (!request) return;
    try {
      setEvaluating(true);
      // POST /api/loans/evaluate
      const res = await evaluateLoan({
        loan_id: request.id,
        merchant_id: request.merchant_id,
        customer_id: request.customer_id,
      });
      // Update local request data with the evaluation results
      setRequest((prev: any) => ({
        ...prev,
        ai_score: res.data.score,
        risk_label: res.data.risk_label,
        pd_value: res.data.pd_value,
        ai_agent_report: res.data.report_text
      }));
    } catch (err) {
      console.error("Error evaluating:", err);
      alert("Đánh giá AI thất bại.");
    } finally {
      setEvaluating(false);
    }
  };

  const parsedRecommendation = useMemo(() => {
    if (!request || !request.ai_agent_report) return null;
    return parseReportText(request.ai_agent_report);
  }, [request]);

  const transactionsWithDates = useMemo(() => {
    return customerTransactions
      .map((transaction) => ({ transaction, parsedDate: parseTransactionDate(transaction) }))
      .filter((entry): entry is { transaction: TransactionPoint; parsedDate: Date } => Boolean(entry.parsedDate));
  }, [customerTransactions]);

  const latestTransactionDate = useMemo(() => {
    if (transactionsWithDates.length === 0) return null;

    return transactionsWithDates.reduce((latest, entry) => {
      return entry.parsedDate > latest ? entry.parsedDate : latest;
    }, transactionsWithDates[0].parsedDate);
  }, [transactionsWithDates]);

  const cutoffDate = useMemo(() => {
    if (!latestTransactionDate) return null;

    const result = new Date(latestTransactionDate);
    result.setDate(result.getDate() - 149);
    result.setHours(0, 0, 0, 0);
    return result;
  }, [latestTransactionDate]);

  const filteredTransactions = useMemo(() => {
    if (!cutoffDate) return customerTransactions;

    return transactionsWithDates
      .filter((entry) => entry.parsedDate >= cutoffDate)
      .map((entry) => entry.transaction)
      .sort((left, right) => {
        const leftDate = parseTransactionDate(left)?.getTime() ?? 0;
        const rightDate = parseTransactionDate(right)?.getTime() ?? 0;
        return rightDate - leftDate;
      });
  }, [customerTransactions, cutoffDate, transactionsWithDates]);

  const totalRevenue = useMemo(
    () => filteredTransactions.reduce((sum, transaction) => sum + (transaction.amount || transaction["Tổng giá"] || 0), 0),
    [filteredTransactions]
  );
  const totalTransactions = filteredTransactions.length;
  const avgTransactionValue = totalTransactions > 0 ? totalRevenue / totalTransactions : 0;

  const revenueSeries = useMemo(() => {
    const groupedByDay = filteredTransactions.reduce<Record<string, number>>((accumulator, transaction) => {
      const transactionDate = parseTransactionDate(transaction);
      if (!transactionDate) return accumulator;

      const key = toDateKey(transactionDate);
      accumulator[key] = (accumulator[key] || 0) + (transaction.amount || transaction["Tổng giá"] || 0);
      return accumulator;
    }, {});

    return Object.entries(groupedByDay)
      .sort(([leftDate], [rightDate]) => leftDate.localeCompare(rightDate))
      .map(([date, revenue]) => ({
        date: new Date(date).toLocaleDateString("vi-VN", { month: "short", day: "2-digit" }),
        revenueMillion: revenue / 1_000_000,
      }));
  }, [filteredTransactions]);

  const weeklyRevenue = useMemo(() => {
    const groupedByWeek = filteredTransactions.reduce<Record<string, number>>((accumulator, transaction) => {
      const transactionDate = parseTransactionDate(transaction);
      if (!transactionDate) return accumulator;

      const weekKey = toDateKey(startOfWeek(transactionDate));
      accumulator[weekKey] = (accumulator[weekKey] || 0) + (transaction.amount || transaction["Tổng giá"] || 0);
      return accumulator;
    }, {});

    return Object.entries(groupedByWeek)
      .sort(([leftDate], [rightDate]) => leftDate.localeCompare(rightDate))
      .map(([weekStart, revenue]) => ({
        week: new Date(weekStart).toLocaleDateString("vi-VN", { month: "short", day: "2-digit" }),
        revenueMillion: revenue / 1_000_000,
      }));
  }, [filteredTransactions]);

  const monthlyRevenue = useMemo(() => {
    const groupedByMonth = filteredTransactions.reduce<Record<string, number>>((accumulator, transaction) => {
      const transactionDate = parseTransactionDate(transaction);
      if (!transactionDate) return accumulator;

      const monthKey = toMonthKey(transactionDate);
      accumulator[monthKey] = (accumulator[monthKey] || 0) + (transaction.amount || transaction["Tổng giá"] || 0);
      return accumulator;
    }, {});

    return Object.entries(groupedByMonth)
      .sort(([leftMonth], [rightMonth]) => leftMonth.localeCompare(rightMonth))
      .slice(-5)
      .map(([month, revenue]) => ({
        month: new Date(`${month}-01`).toLocaleDateString("vi-VN", { month: "short", year: "numeric" }),
        revenueMillion: revenue / 1_000_000,
      }));
  }, [filteredTransactions]);

  if (loading) {
    return (
      <BankerLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </BankerLayout>
    );
  }

  if (!request || !customer) {
    return (
      <BankerLayout>
        <div className="p-6 space-y-4">
          <Link to="/banker/loan-requests" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Loan Requests
          </Link>
          <Card>
            <CardContent className="py-10 text-center text-muted-foreground">
              Không tìm thấy yêu cầu vay tương ứng.
            </CardContent>
          </Card>
        </div>
      </BankerLayout>
    );
  }

  return (
    <BankerLayout>
      <div className="p-6 space-y-6">
        <Link to="/banker/loan-requests" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Loan Requests
        </Link>

        <div className="space-y-2">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Loan Request Detail</h1>
              <p className="text-muted-foreground">
                {request.id} - {customer.name} ({request.customer_id})
              </p>
            </div>
            <Badge className={getStatusColor(request.status)}>{request.status}</Badge>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-sm text-muted-foreground">
            <CalendarDays className="h-4 w-4" />
            {cutoffDate ? `Revenue window from ${cutoffDate.toLocaleDateString("vi-VN")}` : "No transaction window"}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Customer Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><span className="text-muted-foreground">Name:</span> {customer.name || customer.owner_name}</p>
              <p><span className="text-muted-foreground">Customer ID:</span> {request.customer_id}</p>
              <p><span className="text-muted-foreground">Merchant ID:</span> {request.merchant_id}</p>
              <p><span className="text-muted-foreground">Industry:</span> {customer.industry?.replace(/_/g, " ")}</p>
              <p><span className="text-muted-foreground">Business Type:</span> {customer.business_type?.replace(/_/g, " ")}</p>
              <p><span className="text-muted-foreground">Years in Business:</span> {customer.years_in_business?.toFixed(1)}</p>
              <p>
                <span className="text-muted-foreground">Risk Label:</span>
                {request.risk_label ? (
                  <Badge className={`ml-2 ${getRiskLabelColor(request.risk_label)}`}>{request.risk_label}</Badge>
                ) : (
                  <span className="ml-2">Chưa đánh giá</span>
                )}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Loan Request Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><span className="text-muted-foreground">Request ID:</span> {request.id}</p>
              <p><span className="text-muted-foreground">Purpose:</span> {getLoanPurposeLabel(request.loan_type)}</p>
              <p><span className="text-muted-foreground">Requested Amount:</span> {formatCurrency(request.requested_amount)}</p>
              <p><span className="text-muted-foreground">AI Score:</span> {request.ai_score ?? "N/A"}</p>
              <p><span className="text-muted-foreground">PD Value:</span> {request.pd_value != null ? formatPercentage(request.pd_value) : "N/A"}</p>
              <p><span className="text-muted-foreground">Created At:</span> {toReadableDate(request.created_at)}</p>
              <p><span className="text-muted-foreground">Updated At:</span> {toReadableDate(request.updated_at)}</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalRevenue)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Transactions</CardTitle>
              <ShoppingCart className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalTransactions}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Transaction Value</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(avgTransactionValue)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Filter Window</CardTitle>
              <CalendarDays className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">150 days</div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueSeries}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Line type="monotone" dataKey="revenueMillion" stroke="#0046FF" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Weekly Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weeklyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Bar dataKey="revenueMillion" fill="#0F766E" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Revenue - Last 5 Months</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Bar dataKey="revenueMillion" fill="#B45309" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              AI Recommendation
            </CardTitle>
            {request.status === "PENDING" && (
              <Button onClick={handleEvaluate} disabled={evaluating}>
                {evaluating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {request.ai_agent_report ? "Re-Evaluate AI" : "Evaluate AI"}
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {parsedRecommendation && parsedRecommendation.report_text_bank ? (
              <Tabs.Root defaultValue="bank" className="w-full">
                <Tabs.List className="grid w-full grid-cols-2 mb-4">
                  <Tabs.Trigger
                    value="bank"
                    className="px-3 py-2 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary"
                  >
                    Bank View
                  </Tabs.Trigger>
                  <Tabs.Trigger
                    value="user"
                    className="px-3 py-2 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary"
                  >
                    User View
                  </Tabs.Trigger>
                </Tabs.List>

                <Tabs.Content value="bank" className="space-y-1">
                  {renderRecommendationText(parsedRecommendation.report_text_bank)}
                </Tabs.Content>

                <Tabs.Content value="user" className="space-y-1">
                  {renderRecommendationText(parsedRecommendation.report_text_user)}
                </Tabs.Content>
              </Tabs.Root>
            ) : (
              <p className="text-sm text-muted-foreground">Chưa có dữ liệu AI recommendation cho khách hàng này.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </BankerLayout>
  );
}
