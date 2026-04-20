import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import BankerLayout from "../../components/banker-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { mockLoanSamplesCsvRaw } from "../../data/mockData";
import { Users, SlidersHorizontal } from "lucide-react";

type AgeBucket = "<25" | "25-34" | "35-44" | "45-54" | "55+";

interface CustomerAnalyticsRow {
  customer_id: string;
  age: number;
  location: string;
  created_at: string;
  industry: string;
  business_type: string;
  loan_type: string;
  Revenue_mean_30d: number;
  Txn_frequency: number;
  years_in_business: number;
}

const SAMPLE_SIZE = 8000;
const ageBucketOrder: AgeBucket[] = ["<25", "25-34", "35-44", "45-54", "55+"];
const pieColors = ["#0F766E", "#2563EB", "#B45309", "#7C3AED", "#DC2626", "#059669", "#EA580C", "#4F46E5"];

function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let currentField = "";
  let insideQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      const nextCharacter = line[index + 1];
      if (insideQuotes && nextCharacter === '"') {
        currentField += '"';
        index += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
      continue;
    }

    if (character === "," && !insideQuotes) {
      fields.push(currentField);
      currentField = "";
      continue;
    }

    currentField += character;
  }

  fields.push(currentField);
  return fields.map((field) => field.trim());
}

function parseCsvRecords(csvText: string): Record<string, string>[] {
  const normalizedText = csvText.replace(/^\uFEFF/, "").trim();
  if (!normalizedText) {
    return [];
  }

  const [headerLine, ...dataLines] = normalizedText.split(/\r?\n/);
  const headers = parseCsvLine(headerLine);

  return dataLines
    .filter((line) => line.trim().length > 0)
    .map((line) => {
      const values = parseCsvLine(line);
      return headers.reduce<Record<string, string>>((record, header, index) => {
        record[header] = values[index] ?? "";
        return record;
      }, {});
    });
}

function toNumber(value: string | undefined): number {
  const parsedValue = Number.parseFloat(value ?? "0");
  return Number.isFinite(parsedValue) ? parsedValue : 0;
}

function normalizeValue(value: string | undefined): string {
  return (value ?? "").trim() || "Unknown";
}

function parseCustomerRows(csvText: string): CustomerAnalyticsRow[] {
  return parseCsvRecords(csvText).map((record) => ({
    customer_id: normalizeValue(record.customer_id),
    age: toNumber(record.age),
    location: normalizeValue(record.location),
    created_at: normalizeValue(record.created_at),
    industry: normalizeValue(record.industry),
    business_type: normalizeValue(record.business_type),
    loan_type: normalizeValue(record.loan_type),
    Revenue_mean_30d: toNumber(record.Revenue_mean_30d),
    Txn_frequency: toNumber(record.Txn_frequency),
    years_in_business: toNumber(record.years_in_business),
  }));
}

function sampleRows<T>(rows: T[], size: number): T[] {
  if (rows.length <= size) {
    return rows;
  }

  const copiedRows = [...rows];
  for (let index = copiedRows.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [copiedRows[index], copiedRows[randomIndex]] = [copiedRows[randomIndex], copiedRows[index]];
  }

  return copiedRows.slice(0, size);
}

function getAgeBucket(age: number): AgeBucket {
  if (age < 25) {
    return "<25";
  }
  if (age <= 34) {
    return "25-34";
  }
  if (age <= 44) {
    return "35-44";
  }
  if (age <= 54) {
    return "45-54";
  }
  return "55+";
}

function getCreatedYear(dateText: string): string {
  const parsedDate = new Date(dateText);
  if (!Number.isNaN(parsedDate.getTime())) {
    return String(parsedDate.getFullYear());
  }

  const directYear = dateText.slice(0, 4);
  return /^\d{4}$/.test(directYear) ? directYear : "Unknown";
}

function formatMillion(value: number): string {
  return `${value.toFixed(2)}M`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("vi-VN").format(value);
}

function groupedAverage(rows: CustomerAnalyticsRow[], keySelector: (row: CustomerAnalyticsRow) => string, valueSelector: (row: CustomerAnalyticsRow) => number) {
  const groupMap = new Map<string, { total: number; count: number }>();
  for (const row of rows) {
    const key = keySelector(row);
    const existing = groupMap.get(key) ?? { total: 0, count: 0 };
    existing.total += valueSelector(row);
    existing.count += 1;
    groupMap.set(key, existing);
  }

  return Array.from(groupMap.entries()).map(([key, aggregate]) => ({
    key,
    value: aggregate.count > 0 ? aggregate.total / aggregate.count : 0,
  }));
}

function groupedCount(rows: CustomerAnalyticsRow[], keySelector: (row: CustomerAnalyticsRow) => string) {
  const groupMap = new Map<string, number>();
  for (const row of rows) {
    const key = keySelector(row);
    groupMap.set(key, (groupMap.get(key) ?? 0) + 1);
  }

  return Array.from(groupMap.entries()).map(([key, value]) => ({ key, value }));
}

export default function BankerTransactions() {
  const navigate = useNavigate();

  const [ageBucketFilter, setAgeBucketFilter] = useState("all");
  const [locationFilter, setLocationFilter] = useState("all");
  const [yearFilter, setYearFilter] = useState("all");
  const [industryFilter, setIndustryFilter] = useState("all");
  const [businessTypeFilter, setBusinessTypeFilter] = useState("all");
  const [loanTypeFilter, setLoanTypeFilter] = useState("all");

  useEffect(() => {
    const loggedIn = localStorage.getItem("bankerLoggedIn");
    if (!loggedIn) {
      navigate("/banker/login");
    }
  }, [navigate]);

  const sampledRows = useMemo(() => {
    const parsedRows = parseCustomerRows(mockLoanSamplesCsvRaw);
    return sampleRows(parsedRows, SAMPLE_SIZE);
  }, []);

  const options = useMemo(() => {
    const ageBuckets = Array.from(new Set(sampledRows.map((row) => getAgeBucket(row.age))));
    const locations = Array.from(new Set(sampledRows.map((row) => row.location))).sort((left, right) => left.localeCompare(right));
    const years = Array.from(new Set(sampledRows.map((row) => getCreatedYear(row.created_at)))).sort((left, right) => left.localeCompare(right));
    const industries = Array.from(new Set(sampledRows.map((row) => row.industry))).sort((left, right) => left.localeCompare(right));
    const businessTypes = Array.from(new Set(sampledRows.map((row) => row.business_type))).sort((left, right) => left.localeCompare(right));
    const loanTypes = Array.from(new Set(sampledRows.map((row) => row.loan_type))).sort((left, right) => left.localeCompare(right));

    return {
      ageBuckets: ageBucketOrder.filter((bucket) => ageBuckets.includes(bucket)),
      locations,
      years,
      industries,
      businessTypes,
      loanTypes,
    };
  }, [sampledRows]);

  const filteredRows = useMemo(() => {
    return sampledRows.filter((row) => {
      const rowAgeBucket = getAgeBucket(row.age);
      const rowYear = getCreatedYear(row.created_at);

      if (ageBucketFilter !== "all" && rowAgeBucket !== ageBucketFilter) {
        return false;
      }
      if (locationFilter !== "all" && row.location !== locationFilter) {
        return false;
      }
      if (yearFilter !== "all" && rowYear !== yearFilter) {
        return false;
      }
      if (industryFilter !== "all" && row.industry !== industryFilter) {
        return false;
      }
      if (businessTypeFilter !== "all" && row.business_type !== businessTypeFilter) {
        return false;
      }
      if (loanTypeFilter !== "all" && row.loan_type !== loanTypeFilter) {
        return false;
      }

      return true;
    });
  }, [sampledRows, ageBucketFilter, locationFilter, yearFilter, industryFilter, businessTypeFilter, loanTypeFilter]);

  const totalRevenueMillion = useMemo(
    () => filteredRows.reduce((sum, row) => sum + row.Revenue_mean_30d, 0) / 1_000_000,
    [filteredRows]
  );

  const totalCustomers = filteredRows.length;

  const avgTxnFrequency = useMemo(() => {
    if (filteredRows.length === 0) {
      return 0;
    }
    return filteredRows.reduce((sum, row) => sum + row.Txn_frequency, 0) / filteredRows.length;
  }, [filteredRows]);

  const ageDistribution = useMemo(() => {
    const counts = groupedCount(filteredRows, (row) => getAgeBucket(row.age));
    return ageBucketOrder.map((bucket) => ({
      ageBucket: bucket,
      customers: counts.find((entry) => entry.key === bucket)?.value ?? 0,
    }));
  }, [filteredRows]);

  const revenueByAge = useMemo(() => {
    const averages = groupedAverage(filteredRows, (row) => getAgeBucket(row.age), (row) => row.Revenue_mean_30d);
    return ageBucketOrder.map((bucket) => ({
      ageBucket: bucket,
      revenueMillion: (averages.find((entry) => entry.key === bucket)?.value ?? 0) / 1_000_000,
    }));
  }, [filteredRows]);

  const txnFrequencyByAge = useMemo(() => {
    const averages = groupedAverage(filteredRows, (row) => getAgeBucket(row.age), (row) => row.Txn_frequency);
    return ageBucketOrder.map((bucket) => ({
      ageBucket: bucket,
      txnFrequency: averages.find((entry) => entry.key === bucket)?.value ?? 0,
    }));
  }, [filteredRows]);

  const customersByLocation = useMemo(() => {
    return groupedCount(filteredRows, (row) => row.location)
      .map((entry) => ({ location: entry.key, customers: entry.value }))
      .sort((left, right) => right.customers - left.customers);
  }, [filteredRows]);

  const revenueByLocation = useMemo(() => {
    const sums = new Map<string, number>();
    for (const row of filteredRows) {
      sums.set(row.location, (sums.get(row.location) ?? 0) + row.Revenue_mean_30d);
    }
    return Array.from(sums.entries())
      .map(([location, revenue]) => ({ location, revenueMillion: revenue / 1_000_000 }))
      .sort((left, right) => right.revenueMillion - left.revenueMillion);
  }, [filteredRows]);

  const businessMaturityByLocation = useMemo(() => {
    return groupedAverage(filteredRows, (row) => row.location, (row) => row.years_in_business)
      .map((entry) => ({ location: entry.key, avgYears: entry.value }))
      .sort((left, right) => right.avgYears - left.avgYears);
  }, [filteredRows]);

  const customerGrowthByYear = useMemo(() => {
    return groupedCount(filteredRows, (row) => getCreatedYear(row.created_at))
      .map((entry) => ({ year: entry.key, customers: entry.value }))
      .filter((entry) => entry.year !== "Unknown")
      .sort((left, right) => left.year.localeCompare(right.year));
  }, [filteredRows]);

  const revenueTrendByYear = useMemo(() => {
    return groupedAverage(filteredRows, (row) => getCreatedYear(row.created_at), (row) => row.Revenue_mean_30d)
      .map((entry) => ({ year: entry.key, revenueMillion: entry.value / 1_000_000 }))
      .filter((entry) => entry.year !== "Unknown")
      .sort((left, right) => left.year.localeCompare(right.year));
  }, [filteredRows]);

  const customersByIndustry = useMemo(() => {
    return groupedCount(filteredRows, (row) => row.industry)
      .map((entry) => ({ industry: entry.key, customers: entry.value }))
      .sort((left, right) => right.customers - left.customers);
  }, [filteredRows]);

  const customersByBusinessType = useMemo(() => {
    return groupedCount(filteredRows, (row) => row.business_type)
      .map((entry) => ({ businessType: entry.key, customers: entry.value }))
      .sort((left, right) => right.customers - left.customers);
  }, [filteredRows]);

  const revenueByIndustryAndBusinessType = useMemo(() => {
    const allBusinessTypes = Array.from(new Set(filteredRows.map((row) => row.business_type))).sort((a, b) => a.localeCompare(b));

    const grouped = new Map<string, Map<string, { total: number; count: number }>>();

    for (const row of filteredRows) {
      const industryMap = grouped.get(row.industry) ?? new Map<string, { total: number; count: number }>();
      const aggregate = industryMap.get(row.business_type) ?? { total: 0, count: 0 };
      aggregate.total += row.Revenue_mean_30d;
      aggregate.count += 1;
      industryMap.set(row.business_type, aggregate);
      grouped.set(row.industry, industryMap);
    }

    return Array.from(grouped.entries())
      .map(([industry, businessTypeMap]) => {
        const dataPoint: Record<string, number | string> = { industry };
        for (const businessType of allBusinessTypes) {
          const aggregate = businessTypeMap.get(businessType);
          dataPoint[businessType] = aggregate ? aggregate.total / aggregate.count / 1_000_000 : 0;
        }
        return dataPoint;
      })
      .sort((left, right) => String(left.industry).localeCompare(String(right.industry)));
  }, [filteredRows]);

  const businessTypesForGroupedChart = useMemo(() => {
    return Array.from(new Set(filteredRows.map((row) => row.business_type))).sort((left, right) => left.localeCompare(right));
  }, [filteredRows]);

  const loanTypeDistribution = useMemo(() => {
    return groupedCount(filteredRows, (row) => row.loan_type)
      .map((entry) => ({ loanType: entry.key, customers: entry.value }))
      .sort((left, right) => right.customers - left.customers);
  }, [filteredRows]);

  return (
    <BankerLayout>
      <div className="p-6 space-y-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Customer Segmentation & Behavior Analytics</h1>
            <p className="text-muted-foreground">Dashboard Category: Customer Analytics | Grain: customer_id</p>
          </div>
          <Badge className="w-fit bg-primary/15 text-primary">
            Random sample: {formatNumber(sampledRows.length)} / {SAMPLE_SIZE}
          </Badge>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              Global Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">age_bucket</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={ageBucketFilter} onChange={(event) => setAgeBucketFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.ageBuckets.map((bucket) => (
                    <option key={bucket} value={bucket}>{bucket}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">location</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={locationFilter} onChange={(event) => setLocationFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.locations.map((location) => (
                    <option key={location} value={location}>{location}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">year(created_at)</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.years.map((year) => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">industry</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={industryFilter} onChange={(event) => setIndustryFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.industries.map((industry) => (
                    <option key={industry} value={industry}>{industry}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">business_type</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={businessTypeFilter} onChange={(event) => setBusinessTypeFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.businessTypes.map((businessType) => (
                    <option key={businessType} value={businessType}>{businessType}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">loan_type</label>
                <select className="h-10 w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm" value={loanTypeFilter} onChange={(event) => setLoanTypeFilter(event.target.value)}>
                  <option value="all">All</option>
                  {options.loanTypes.map((loanType) => (
                    <option key={loanType} value={loanType}>{loanType}</option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Filtered Customers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                {formatNumber(totalCustomers)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Total Revenue Mean 30d</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatMillion(totalRevenueMillion)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Average Txn Frequency</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgTxnFrequency.toFixed(2)}</div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Age Distribution</CardTitle>
              <p className="text-xs text-muted-foreground">Demographics</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={ageDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ageBucket" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="customers" fill="#2563EB" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revenue by Age Group</CardTitle>
              <p className="text-xs text-muted-foreground">Customer Value</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={revenueByAge}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ageBucket" />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Bar dataKey="revenueMillion" fill="#0F766E" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Txn Frequency by Age</CardTitle>
              <p className="text-xs text-muted-foreground">Customer Behavior</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={txnFrequencyByAge}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ageBucket" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="txnFrequency" fill="#B45309" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Customer Distribution by Location</CardTitle>
              <p className="text-xs text-muted-foreground">Geography</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={customersByLocation}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="location" interval={0} angle={-25} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="customers" fill="#4F46E5" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revenue by Location</CardTitle>
              <p className="text-xs text-muted-foreground">Geography</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={revenueByLocation}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="location" interval={0} angle={-25} textAnchor="end" height={80} />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Bar dataKey="revenueMillion" fill="#DC2626" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Business Maturity by Location</CardTitle>
              <p className="text-xs text-muted-foreground">Geography</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={businessMaturityByLocation}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="location" interval={0} angle={-25} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} years`} />
                  <Bar dataKey="avgYears" fill="#059669" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Customer Growth by Year</CardTitle>
              <p className="text-xs text-muted-foreground">Time Series</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={customerGrowthByYear}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="customers" stroke="#2563EB" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revenue Trend</CardTitle>
              <p className="text-xs text-muted-foreground">Time Series</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={revenueTrendByYear}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Line type="monotone" dataKey="revenueMillion" stroke="#0F766E" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Customers by Industry</CardTitle>
              <p className="text-xs text-muted-foreground">Industry</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={customersByIndustry}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="industry" interval={0} angle={-25} textAnchor="end" height={90} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="customers" fill="#EA580C" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Customers by Business Type</CardTitle>
              <p className="text-xs text-muted-foreground">Industry</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={customersByBusinessType} dataKey="customers" nameKey="businessType" cx="50%" cy="50%" outerRadius={90} label>
                    {customersByBusinessType.map((entry, index) => (
                      <Cell key={`${entry.businessType}-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revenue by Industry & Business Type</CardTitle>
              <p className="text-xs text-muted-foreground">Industry</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={revenueByIndustryAndBusinessType}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="industry" interval={0} angle={-25} textAnchor="end" height={90} />
                  <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}M`} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} million VND`} />
                  <Legend />
                  {businessTypesForGroupedChart.map((businessType, index) => (
                    <Bar key={businessType} dataKey={businessType} fill={pieColors[index % pieColors.length]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Loan Type Distribution</CardTitle>
              <p className="text-xs text-muted-foreground">Loan Portfolio</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={loanTypeDistribution} dataKey="customers" nameKey="loanType" cx="50%" cy="50%" outerRadius={90} label>
                    {loanTypeDistribution.map((entry, index) => (
                      <Cell key={`${entry.loanType}-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>
    </BankerLayout>
  );
}
