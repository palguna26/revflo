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

      <main className="container max-w-7xl mx-auto px-4 py-8">
        {/* Welcome */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 pb-6 border-b">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Welcome back, {user?.name || user?.login}. Here's what's happening across your projects.
            </p>
          </div>
          <div className="flex items-center gap-2 mt-4 md:mt-0">
            {repos.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleSaveRepos} disabled={savingRepos} className="h-8">
                {savingRepos ? 'Saving...' : 'Save View'}
              </Button>
            )}
            <Button size="sm" className="h-8 shadow-none" onClick={() => navigate('/add-repo')}>
              <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Repository
            </Button>
          </div>
        </div>

        {/* Repositories */}
        {repos.length === 0 ? (
          <div className="text-center py-20 border rounded-lg bg-card border-dashed">
            <h3 className="text-lg font-medium mb-2">No repositories connected</h3>
            <p className="text-muted-foreground mb-6">Connect a GitHub repository to start analyzing code.</p>
            <Button onClick={() => navigate('/add-repo')}>Connect Repository</Button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-10">
            {repos.map((repo) => {
              const isSelected = selectedRepos.includes(repo.repo_full_name);
              return (
                <Card
                  key={repo.repo_full_name}
                  className={`group cursor-pointer transition-colors hover:border-primary/50 relative ${!isSelected ? 'opacity-60 grayscale' : ''}`}
                  onClick={() => navigate(`/repo/${repo.owner}/${repo.name}`)}
                >
                  <div className="absolute top-3 right-3 z-10" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleRepo(repo.repo_full_name)}
                      className="accent-primary h-4 w-4 rounded border-gray-300"
                    />
                  </div>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between">
                      <span className="font-mono text-sm font-medium truncate" title={repo.repo_full_name}>
                        {repo.repo_full_name}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-end justify-between">
                      <div>
                        <div className="text-3xl font-bold tracking-tight">{repo.health_score}</div>
                        <div className="text-xs text-muted-foreground mt-1">Health Score</div>
                      </div>
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <GitPullRequest className="h-3.5 w-3.5" />
                          {repo.pr_count}
                        </div>
                        <div className="flex items-center gap-1">
                          <FileText className="h-3.5 w-3.5" />
                          {repo.issue_count}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Recent Activity */}
        <div className="grid lg:grid-cols-2 gap-8">
          <div className="border rounded-lg bg-card overflow-hidden">
            <div className="px-6 py-4 border-b bg-muted/30 flex items-center justify-between">
              <h3 className="font-medium text-sm">Recent Pull Requests</h3>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleRefresh}>
                <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
            <div className="p-0">
              {recentPRs.length === 0 ? (
                <div className="p-8 text-center text-sm text-muted-foreground">No recent activity</div>
              ) : (
                <div className="divide-y">
                  {recentPRs.map((pr: any) => (
                    <div key={pr.pr_number} className="p-4 hover:bg-muted/50 transition-colors">
                      <PRCard
                        prNumber={pr.pr_number}
                        title={pr.title}
                        author={pr.author}
                        healthScore={pr.health_score}
                        repoOwner={pr.repo_owner}
                        repoName={pr.repo_name}
                        validationStatus={pr.validation_status}
                        compact={true}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="border rounded-lg bg-card overflow-hidden">
            <div className="px-6 py-4 border-b bg-muted/30">
              <h3 className="font-medium text-sm">Open Issues</h3>
            </div>
            <div className="p-0">
              {recentIssues.length === 0 ? (
                <div className="p-8 text-center text-sm text-muted-foreground">No open issues</div>
              ) : (
                <div className="divide-y">
                  {recentIssues.map((issue: any) => (
                    <div key={issue.issue_number} className="p-4 hover:bg-muted/50 transition-colors">
                      <IssueCard
                        issue={issue}
                        repoOwner={issue.repo_owner}
                        repoName={issue.repo_name}
                        compact={true}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
};

export default Dashboard;
