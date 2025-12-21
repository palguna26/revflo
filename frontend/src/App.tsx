import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import LoginCallback from "./pages/LoginCallback";
import Dashboard from "./pages/Dashboard";
import RepoPage from "./pages/RepoPage";
import IssueDetail from "./pages/IssueDetail";
import PRDetail from "./pages/PRDetail";
import RepoSettings from "./pages/RepoSettings";
import HealthAnalytics from "./pages/HealthAnalytics";
import RepoAudit from "./pages/RepoAudit";
import AddRepo from "./pages/AddRepo";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth/callback" element={<LoginCallback />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/repo/:owner/:repo" element={<RepoPage />} />
          <Route path="/repo/:owner/:repo/issues/:issueNumber" element={<IssueDetail />} />
          <Route path="/repo/:owner/:repo/prs/:prNumber" element={<PRDetail />} />
          <Route path="/repo/:owner/:repo/settings" element={<RepoSettings />} />
          <Route path="/repo/:owner/:repo/audit" element={<RepoAudit />} />
          <Route path="/repo/:owner/:repo/analytics" element={<HealthAnalytics />} />
          <Route path="/add-repo" element={<AddRepo />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
