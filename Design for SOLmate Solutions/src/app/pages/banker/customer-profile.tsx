import { useNavigate, useParams } from "react-router";
import { useEffect } from "react";
import BankerLayout from "../../components/banker-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { mockCustomerMetrics, formatCurrency, formatPercentage, getRiskLabelColor } from "../../data/mockData";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router";

export default function BankerCustomerProfile() {
  const navigate = useNavigate();
  const { customerId } = useParams();

  useEffect(() => {
    const loggedIn = localStorage.getItem("bankerLoggedIn");
    if (!loggedIn) {
      navigate("/banker/login");
    }
  }, [navigate]);

  const customer = mockCustomerMetrics.find(c => c.customer_id === customerId);

  if (!customer) {
    return (
      <BankerLayout>
        <div className="p-6">
          <p>Customer not found</p>
        </div>
      </BankerLayout>
    );
  }

  return (
    <BankerLayout>
      <div className="p-6 space-y-6">
        <Link to="/banker/dashboard" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        <div>
          <h1 className="text-3xl font-bold text-foreground">{customer.name}</h1>
          <p className="text-muted-foreground">Customer Profile - {customer.customer_id}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Thông tin cơ bản</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm text-muted-foreground">Customer ID:</span>
                <p className="font-mono">{customer.customer_id}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Merchant ID:</span>
                <p className="font-mono">{customer.merchant_id}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Age:</span>
                <p>{customer.age}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Industry:</span>
                <p>{customer.industry.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Business Type:</span>
                <p>{customer.business_type.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Location:</span>
                <p>{customer.location}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Years in Business:</span>
                <p>{customer.years_in_business.toFixed(1)} years</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Created At:</span>
                <p>{customer.created_at}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tình trạng tín dụng</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm text-muted-foreground">CIC Score:</span>
                <p className="text-2xl font-bold text-primary">{customer.CIC_SCORE.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Risk Label:</span>
                <div className="mt-1">
                  <Badge className={getRiskLabelColor(customer.label)}>
                    {customer.label}
                  </Badge>
                </div>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Default Probability:</span>
                <p className="text-xl font-semibold text-destructive">
                  {formatPercentage(customer.default_probability)}
                </p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Regime:</span>
                <div className="mt-1">
                  <Badge variant={customer.regime === 'NORMAL' ? 'secondary' : 'destructive'}>
                    {customer.regime}
                  </Badge>
                </div>
              </div>
              {customer.loan_type && (
                <div>
                  <span className="text-sm text-muted-foreground">Loan Type:</span>
                  <p>{customer.loan_type}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Financial Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm text-muted-foreground">Revenue (30 days):</span>
                <p className="font-semibold">{formatCurrency(customer.Revenue_mean_30d)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Revenue (90 days):</span>
                <p className="font-semibold">{formatCurrency(customer.Revenue_mean_90d)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Transaction Frequency:</span>
                <p>{customer.Txn_frequency.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Growth Score:</span>
                <p>{customer.Growth_score.toFixed(3)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">CV Score (Stability):</span>
                <p>{customer.CV_score.toFixed(3)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Spike Score:</span>
                <p>{customer.Spike_score.toFixed(3)}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </BankerLayout>
  );
}
