import { useEffect, useState } from 'react';
// Header removed
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, GitPullRequest, FileText, Plus, ExternalLink, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { User, RepoSummary, PRSummary, Issue } from '@/types/api';
import { PRCard } from '@/components/PRCard';
import { IssueCard } from '@/components/IssueCard';

import { useOutletContext } from 'react-router-dom';
import type { DashboardContextType } from '@/layouts/DashboardLayout';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, repos, setUser, setRepos } = useOutletContext<DashboardContextType>();
  // Local state for dashboard-specific things
  const [recentPRs, setRecentPRs] = useState<PRSummary[]>([]);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [savingRepos, setSavingRepos] = useState(false);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (user && repos.length > 0) {
      const initialSelection =
        user.managed_repos && user.managed_repos.length > 0
          ? user.managed_repos
          : repos.map((r) => r.repo_full_name);
      setSelectedRepos(initialSelection);
    }
  }, [user, repos]);

  useEffect(() => {
    if (repos.length === 0) return;
    const loadActivity = async () => {
      try {
        const activity = await api.getRecentActivity();
        setRecentPRs(activity.prs);
        setRecentIssues(activity.issues);
      } catch (error) {
        console.error('Activity load failed:', error);
      }
    };
    loadActivity();
  }, [repos]);

  const handleToggleRepo = (fullName: string) => {
    setSelectedRepos((prev) =>
      prev.includes(fullName) ? prev.filter((r) => r !== fullName) : [...prev, fullName],
    );
  };

  const handleSaveRepos = async () => {
    if (!user) return;
    setSavingRepos(true);
    try {
      const updatedUser = await api.updateManagedRepos(selectedRepos);
      setUser(updatedUser);
      const reposData = await api.getRepos();
      setRepos(reposData);
    } catch (e) { console.error(e); } finally { setSavingRepos(false); }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    window.location.reload();
  };



  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header removed, provided by Layout */}


      <main className="container max-w-5xl mx-auto px-4 py-8">
        {/* Welcome & Actions */}
        <div className="flex items-center justify-between mb-8 pb-6 border-b">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">My Active Work</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Welcome back, {user?.name || user?.login}. Here are the PRs and Issues requiring your attention.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button size="sm" onClick={() => navigate('/settings')}>
              <Plus className="mr-1.5 h-3.5 w-3.5" /> Manage Repositories
            </Button>
          </div>
        </div>

        {/* Active Work Content */}
        {recentPRs.length === 0 && recentIssues.length === 0 ? (
          <div className="text-center py-20 border rounded-lg bg-card border-dashed">
            <h3 className="text-lg font-medium mb-2">No active work found</h3>
            <p className="text-muted-foreground mb-6">You don't have any recent PRs or assigned issues.</p>
            <Button onClick={() => navigate('/settings')}>Manage Repositories</Button>
          </div>
        ) : (
          <div className="space-y-8">
            {/* PRs Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <GitPullRequest className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-medium">Pull Requests</h2>
              </div>

              <div className="border rounded-lg bg-card overflow-hidden divide-y">
                {recentPRs.length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No active pull requests.</div>
                ) : (
                  recentPRs.map((pr: any) => (
                    <div key={pr.pr_number} className="p-4 hover:bg-muted/50 transition-colors">
                      <PRCard
                        prNumber={pr.pr_number}
                        title={pr.title}
                        author={pr.author}
                        healthScore={pr.health_score}
                        repoOwner={pr.repo_owner}
                        repoName={pr.repo_name}
                        validationStatus={pr.validation_status}
                        compact={false}
                      />
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Issues Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-medium">Assigned Issues</h2>
              </div>

              <div className="border rounded-lg bg-card overflow-hidden divide-y">
                {recentIssues.length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No assigned issues.</div>
                ) : (
                  recentIssues.map((issue: any) => (
                    <div key={issue.issue_number} className="p-4 hover:bg-muted/50 transition-colors">
                      <IssueCard
                        issue={issue}
                        repoOwner={issue.repo_owner}
                        repoName={issue.repo_name}
                        compact={false}
                      />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main >
    </div >
  );
};

export default Dashboard;
