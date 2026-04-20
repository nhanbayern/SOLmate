import { useNavigate, useParams, Link } from "react-router";
import { useEffect, useState } from "react";
import CustomerLayout from "../../components/customer-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { formatCurrency, getLoanPurposeLabel, getStatusColor } from "../../data/mockData";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  FileText,
  Brain,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { getLoanDetail, evaluateLoan, parseReportText } from "../../lib/api";
import { applyTermMapping } from "../../lib/termMapping";


/** Render inline **bold** markers as <strong> */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  if (parts.length === 1) return text;
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        return part;
      })}
    </>
  );
}

function renderMarkdown(text: string) {
  // Apply Vietnamese term mapping before rendering
  const mapped = applyTermMapping(text);
  return mapped.split("\n").map((line, i) => {
    const key = `line-${i}`;
    if (line.startsWith("###")) {
      return (
        <h4 key={key} className="font-semibold text-blue-900 mt-4 mb-2 text-base">
          {renderInline(line.replace(/^###\s*/, "").trim())}
        </h4>
      );
    }
    if (line.trim().startsWith("-")) {
      return (
        <li key={key} className="ml-4 list-disc text-sm text-blue-800 mb-1">
          {renderInline(line.replace(/^-\s*/, "").trim())}
        </li>
      );
    }
    if (line.trim()) {
      return (
        <p key={key} className="text-sm text-blue-800 mb-2">
          {renderInline(line)}
        </p>
      );
    }
    return <div key={key} className="h-2" />;
  });
}


const STATUS_LABELS: Record<string, string> = {
  PENDING: "Chờ xét duyệt",
  SUBMITTED: "Đã gửi",
  IN_REVIEW: "Đang xét duyệt",
  EVALUATED: "Đã đánh giá AI",
  APPROVED: "Đã phê duyệt",
  REJECTED: "Đã từ chối",
};

export default function CustomerLoanDetail() {
  const navigate = useNavigate();
  const { requestId } = useParams<{ requestId: string }>();

  const [loan, setLoan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("customerLoggedIn");
    if (!token) {
      navigate("/customer/login");
      return;
    }
    if (!requestId) return;

    async function load() {
      try {
        setLoading(true);
        // GET /api/loans/:id
        const res = await getLoanDetail(requestId!);
        console.log("[LoanDetail] raw response:", res);
        setLoan(res?.data ?? res);
      } catch (err) {
        console.error("[LoanDetail] load error:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [requestId, navigate]);

  const handleEvaluate = async () => {
    if (!loan) return;
    setEvalError("");
    try {
      setEvaluating(true);
      // POST /api/loans/evaluate
      const res = await evaluateLoan({
        loan_id: loan.id,
        merchant_id: loan.merchant_id,
        customer_id: loan.customer_id,
      });
      console.log("[LoanDetail] evaluate response:", res);
      // Merge updated fields back
      setLoan((prev: any) => ({
        ...prev,
        ai_score: res?.data?.score ?? res?.data?.ai_score ?? prev.ai_score,
        risk_label: res?.data?.risk_label ?? prev.risk_label,
        pd_value: res?.data?.pd_value ?? prev.pd_value,
        ai_agent_report: res?.data?.report_text ?? prev.ai_agent_report,
        status: "EVALUATED",
      }));
    } catch (err: any) {
      setEvalError(err.message || "Đánh giá AI thất bại");
    } finally {
      setEvaluating(false);
    }
  };

  // Parse only the customer-facing part of the report
  const reportUser = loan?.ai_agent_report
    ? parseReportText(loan.ai_agent_report).report_text_user
    : "";

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      case "REJECTED":
        return <XCircle className="w-6 h-6 text-red-600" />;
      case "EVALUATED":
      case "IN_REVIEW":
        return <Clock className="w-6 h-6 text-yellow-600" />;
      default:
        return <FileText className="w-6 h-6 text-blue-600" />;
    }
  };

  if (loading) {
    return (
      <CustomerLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </CustomerLayout>
    );
  }

  if (!loan) {
    return (
      <CustomerLayout>
        <div className="p-6 space-y-4">
          <Link to="/customer/loans" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Quay lại danh sách
          </Link>
          <Card>
            <CardContent className="py-10 text-center text-muted-foreground">
              Không tìm thấy yêu cầu vay <strong>{requestId}</strong>.
            </CardContent>
          </Card>
        </div>
      </CustomerLayout>
    );
  }

  return (
    <CustomerLayout>
      <div className="p-6 space-y-6">
        <Link to="/customer/loans" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Quay lại danh sách
        </Link>

        <div>
          <h1 className="text-3xl font-bold text-foreground">Chi tiết yêu cầu vay</h1>
          <p className="text-muted-foreground font-mono text-sm mt-1">{loan.id}</p>
        </div>

        {/* Status banner */}
        <Card className="border-2">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-muted rounded-full">
                {getStatusIcon(loan.status)}
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Trạng thái hiện tại</p>
                <Badge className={`${getStatusColor(loan.status)} text-base px-3 py-1 mt-1`}>
                  {STATUS_LABELS[loan.status] ?? loan.status}
                </Badge>
              </div>
              {loan.ai_score != null && (
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">AI Score</p>
                  <p className="text-3xl font-bold text-primary">{loan.ai_score}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Info grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Thông tin yêu cầu</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <span className="text-muted-foreground">Loại vay:</span>
                <p className="font-semibold">{getLoanPurposeLabel(loan.loan_type)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Số tiền đề nghị:</span>
                <p className="text-xl font-bold text-primary">{formatCurrency(loan.requested_amount ?? 0)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Merchant ID:</span>
                <p className="font-mono">{loan.merchant_id}</p>
              </div>
              {loan.risk_label && (
                <div>
                  <span className="text-muted-foreground">Đánh giá rủi ro AI:</span>
                  <p>
                    <Badge
                      className={
                        loan.risk_label === "VERY_GOOD" || loan.risk_label === "GOOD"
                          ? "bg-green-100 text-green-800 mt-1"
                          : loan.risk_label === "MEDIUM"
                          ? "bg-yellow-100 text-yellow-800 mt-1"
                          : "bg-red-100 text-red-800 mt-1"
                      }
                    >
                      {loan.risk_label}
                    </Badge>
                  </p>
                </div>
              )}
              {loan.pd_value != null && (
                <div>
                  <span className="text-muted-foreground">Xác suất rủi ro:</span>
                  <p className="font-semibold">{(loan.pd_value * 100).toFixed(1)}%</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Thông tin thời gian</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <span className="text-muted-foreground">Ngày tạo:</span>
                <p>{new Date(loan.created_at).toLocaleString("vi-VN")}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Cập nhật lần cuối:</span>
                <p>{new Date(loan.updated_at).toLocaleString("vi-VN")}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Customer Report section */}
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Brain className="w-5 h-5" />
              Khuyến nghị từ hệ thống AI
            </CardTitle>
            <Button
              onClick={handleEvaluate}
              disabled={evaluating}
              size="sm"
              variant="outline"
              className="border-blue-300 text-blue-700 hover:bg-blue-100"
            >
              {evaluating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              {reportUser ? "Đánh giá lại AI" : "Đánh giá AI"}
            </Button>
          </CardHeader>
          <CardContent>
            {evalError && (
              <p className="text-sm text-destructive mb-3">{evalError}</p>
            )}
            {reportUser ? (
              <div className="prose prose-sm max-w-none">
                {renderMarkdown(reportUser)}
              </div>
            ) : (
              <p className="text-sm text-blue-700 italic">
                Nhấn nút <strong>"Đánh giá AI"</strong> để hệ thống phân tích hồ sơ vay của bạn và đưa ra khuyến nghị.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </CustomerLayout>
  );
}
