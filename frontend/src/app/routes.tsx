import { createBrowserRouter } from "react-router";
import RoleSelection from "./pages/role-selection";
import BankerLogin from "./pages/banker/login";
import BankerDashboard from "./pages/banker/dashboard";
import BankerCustomerAnalysis from "./pages/banker/customerAnalysis";
import BankerLoanRequests from "./pages/banker/loan-requests";
import BankerLoanRequestDetail from "./pages/banker/loanRequestDetail";
import BankerCustomerProfile from "./pages/banker/customer-profile";
import CustomerLogin from "./pages/customer/login";
import CustomerProfile from "./pages/customer/profile";
import CustomerCreateLoan from "./pages/customer/create-loan";
import CustomerLoanList from "./pages/customer/loan-list";
import CustomerLoanDetail from "./pages/customer/loan-detail";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RoleSelection,
  },
  // Banker routes
  {
    path: "/banker/login",
    Component: BankerLogin,
  },
  {
    path: "/banker/dashboard",
    Component: BankerDashboard,
  },
  {
    path: "/banker/customer_analysis",
    Component: BankerCustomerAnalysis,
  },
  {
    path: "/banker/loan-requests",
    Component: BankerLoanRequests,
  },
  {
    path: "/banker/loan-requests/:requestId",
    Component: BankerLoanRequestDetail,
  },
  {
    path: "/banker/customer/:customerId",
    Component: BankerCustomerProfile,
  },
  // Customer routes
  {
    path: "/customer/login",
    Component: CustomerLogin,
  },
  {
    path: "/customer/profile",
    Component: CustomerProfile,
  },
  {
    path: "/customer/create-loan",
    Component: CustomerCreateLoan,
  },
  {
    path: "/customer/loans",
    Component: CustomerLoanList,
  },
  {
    path: "/customer/loans/:requestId",
    Component: CustomerLoanDetail,
  },
]);
