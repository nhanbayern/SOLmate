import { useState } from "react";
import { useNavigate, Link } from "react-router";
import { User, ArrowLeft, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { authLogin, saveToken, extractLoginResult } from "../../lib/api";


export default function CustomerLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!username || !password) {
      setError("Vui lòng nhập đầy đủ thông tin");
      return;
    }

    try {
      setLoading(true);
      console.log("[CustomerLogin] Attempting login for username:", username);
      // POST /api/auth/login
      const res = await authLogin(username, password);
      const { token, role, data } = extractLoginResult(res);

      if (!token) {
        setError("Đăng nhập thất bại: không nhận được token");
        return;
      }

      // Save token + cache profile data (from login response) → profile page reads instantly
      saveToken(token, role, data);
      console.log("[CustomerLogin] Login success, role:", role, "data:", data);
      navigate("/customer/profile");
    } catch (err: any) {
      setError(err.message || "Sai thông tin đăng nhập");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Link to="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary mb-6">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Quay lại
        </Link>

        <Card className="border-2">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-4">
              <User className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl">Đăng nhập Customer</CardTitle>
            <CardDescription>SOLmate SOLUTIONS</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm">Username</label>
                <Input
                  id="username"
                  placeholder="Nhập username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm">Mật khẩu</label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" size="lg" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Đăng nhập
              </Button>
            </form>
            <div className="mt-4 text-center">
              <p className="text-xs text-muted-foreground">
                Dùng tài khoản đã đăng ký trong hệ thống
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
