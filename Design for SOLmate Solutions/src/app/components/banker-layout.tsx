import { Link, useLocation, useNavigate } from "react-router";
import { LayoutDashboard, TrendingUp, FileText, LogOut, Menu } from "lucide-react";
import { Button } from "./ui/button";
import { useState } from "react";
import { clearTokens } from "../lib/api";


interface BankerLayoutProps {
  children: React.ReactNode;
}

export default function BankerLayout({ children }: BankerLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    clearTokens();
    navigate("/banker/login");
  };


  const navItems = [
    { to: "/banker/dashboard", icon: LayoutDashboard, label: "Credit Risk Dashboard" },
    { to: "/banker/customer_analysis", icon: TrendingUp, label: "Customer Analysis" },
    { to: "/banker/loan-requests", icon: FileText, label: "Loan Requests & AI" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-border sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold text-primary">SOLmate SOLUTIONS</h1>
              <p className="text-xs text-muted-foreground">Banker Portal</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            Đăng xuất
          </Button>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-border transition-transform duration-200 mt-16 lg:mt-0`}
        >
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.to;
              return (
                <Link key={item.to} to={item.to}>
                  <div
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? "bg-primary text-white"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 lg:mt-0 mt-0">
          {children}
        </main>
      </div>
    </div>
  );
}
