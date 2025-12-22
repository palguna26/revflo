import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
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

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [recentPRs, setRecentPRs] = useState<PRSummary[]>([]);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [savingRepos, setSavingRepos] = useState(false);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        if (token) {
          localStorage.setItem('qr_token', token);
          window.history.replaceState({}, document.title, window.location.pathname);
        }

        const [userData, reposData] = await Promise.all([api.getMe(), api.getRepos()]);
        setUser(userData);
        setRepos(reposData);

        const initialSelection =
          userData.managed_repos && userData.managed_repos.length > 0
            ? userData.managed_repos
            : reposData.map((r) => r.repo_full_name);
        setSelectedRepos(initialSelection);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

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

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header loading={true} />
        <main className="container max-w-7xl mx-auto px-4 py-8">
          <Skeleton className="h-12 w-48 mb-6" />
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-32" />)}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header user={user || undefined} repos={repos} />

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
            <Button size="sm" onClick={() => navigate('/add-repo')}>
              <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Repository
            </Button>
          </div>
        </div>

        {/* Active Work Content */}
        {recentPRs.length === 0 && recentIssues.length === 0 ? (
          <div className="text-center py-20 border rounded-lg bg-card border-dashed">
            <h3 className="text-lg font-medium mb-2">No active work found</h3>
            <p className="text-muted-foreground mb-6">You don't have any recent PRs or assigned issues.</p>
            <Button onClick={() => navigate('/add-repo')}>Connect a Repository</Button>
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
