import { useNavigate } from "react-router";
import { useEffect, useState } from "react";
import BankerLayout from "../../components/banker-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import {
  formatCurrency,
  getLoanPurposeLabel,
  getRiskLabelColor,
  getStatusColor,
} from "../../data/mockData";
import { ArrowRight, Loader2 } from "lucide-react";
import { getLoans, getMerchants } from "../../lib/api";

export default function BankerLoanRequests() {
  const navigate = useNavigate();
  const [loans, setLoans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loggedIn = localStorage.getItem("bankerLoggedIn");
    if (!loggedIn) {
      navigate("/banker/login");
      return;
    }

    async function fetchData() {
      try {
        setLoading(true);
        // GET /api/loans?limit=10&offset=0  +  GET /api/merchants (parallel)
        const [loansRes, merchantsRes] = await Promise.all([
          getLoans(10, 0),
          getMerchants(),
        ]);

        const loansData: any[] = loansRes?.data ?? [];
        const merchantsData: any[] = merchantsRes?.data ?? [];

        const merchantMap = new Map(merchantsData.map((m: any) => [m.id, m]));

        const combined = loansData.map((req: any) => {
          const merchant = merchantMap.get(req.merchant_id);
          return {
            request: req,
            merchantName: merchant?.owner_name || merchant?.name || req.merchant_id,
          };
        });

        // Sort newest first (server may already sort, but ensure it)
        combined.sort((a: any, b: any) =>
          new Date(b.request.created_at).getTime() - new Date(a.request.created_at).getTime()
        );

        setLoans(combined);
      } catch (err) {
        console.error("[LoanRequests] fetch error:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [navigate]);

  return (
    <BankerLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Loan Requests & AI Recommendations</h1>
          <p className="text-muted-foreground">
            Hiển thị yêu cầu vay theo từng khách hàng. Nhấn vào từng request để mở trang chi tiết phân tích AI.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Loan Request Queue</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Loan ID</TableHead>
                    <TableHead>Merchant</TableHead>
                    <TableHead>Loại vay</TableHead>
                    <TableHead>Số tiền</TableHead>
                    <TableHead>AI Score</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loans.map(({ request, merchantName }) => (
                    <TableRow key={request.id} className="hover:bg-muted/50 cursor-pointer" onClick={() => navigate(`/banker/loan-requests/${request.id}`)}
                    >
                      <TableCell className="font-mono text-xs max-w-[180px] truncate">{request.id}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{merchantName}</p>
                          <p className="text-xs text-muted-foreground">{request.merchant_id}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{getLoanPurposeLabel(request.loan_type)}</TableCell>
                      <TableCell className="font-semibold">{formatCurrency(request.requested_amount ?? 0)}</TableCell>
                      <TableCell>{request.ai_score ?? "—"}</TableCell>
                      <TableCell>
                        <Badge className={getRiskLabelColor(request.risk_label || "UNKNOWN")}>
                          {request.risk_label || "N/A"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(request.status)}>{request.status}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/banker/loan-requests/${request.id}`); }}>
                          Chi tiết
                          <ArrowRight className="ml-1 h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {loans.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-6 text-muted-foreground">
                        Không có yêu cầu vay nào.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </BankerLayout>
  );
}
