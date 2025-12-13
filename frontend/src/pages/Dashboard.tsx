import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { AIRecommendationsFeed } from '@/components/AIRecommendationsFeed';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, GitPullRequest, FileText, ExternalLink } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
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

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, reposData] = await Promise.all([api.getMe(), api.getRepos()]);
        setUser(userData);
        setRepos(reposData);
        // If user has explicit managed_repos, honor that; otherwise default to all repos
        const initialSelection =
          userData.managed_repos && userData.managed_repos.length > 0
            ? userData.managed_repos
            : reposData.map((r) => r.repo_full_name);
        setSelectedRepos(initialSelection);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Load recent activity for the first repo
  // Load recent activity (global)
  useEffect(() => {
    const loadActivity = async () => {
      // If we have no repos, no point loading activity
      if (repos.length === 0) return;

      try {
        const activity = await api.getRecentActivity();
        setRecentPRs(activity.prs);
        setRecentIssues(activity.issues);
      } catch (error) {
        console.error('Failed to load recent activity:', error);
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
      // Reload repos based on new managed_repos
      const reposData = await api.getRepos();
      setRepos(reposData);
    } catch (error) {
      console.error('Failed to save managed repositories:', error);
    } finally {
      setSavingRepos(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header loading={true} />
        <main className="container px-4 py-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header user={user || undefined} repos={repos} />

      <main className="container px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.name || user?.login}!</h1>
            <p className="text-muted-foreground">
              Manage your repositories and track code quality across your projects.
            </p>
          </div>
          <div className="lg:col-span-1">
            <AIRecommendationsFeed />
          </div>
        </div>

        {/* Repository Grid */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4 gap-4">
            <div>
              <h2 className="text-2xl font-bold">Your Repositories</h2>
              {user && user.managed_repos.length === 0 && repos.length > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  Select which repositories you want RevFlo to manage, then click "Save Selection".
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {repos.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveRepos}
                  disabled={savingRepos}
                >
                  {savingRepos ? 'Saving...' : 'Save Selection'}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/add-repo')}
              >
                Add Repo
              </Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.reload()}>
                Refresh
              </Button>
            </div>
          </div>

          {repos.length === 0 ? (
            <Card className="glass-card p-12 text-center">
              <p className="text-muted-foreground mb-4">No repositories found.</p>
              <Button asChild>
                <a href="https://github.com/apps/quantum-review/installations/new" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Install RevFlo
                </a>
              </Button>
            </Card>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {repos.map((repo) => (
                <Card
                  key={repo.repo_full_name}
                  className="glass-card h-full transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer relative"
                  onClick={() => navigate(`/repo/${repo.owner}/${repo.name}`)}

                >
                  <div className="absolute top-3 right-3 z-10" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedRepos.includes(repo.repo_full_name)}
                      onChange={() => handleToggleRepo(repo.repo_full_name)}
                      className="scale-110 transform origin-center cursor-pointer"
                    />
                  </div>
                  <CardHeader>
                    <CardTitle className="flex items-start justify-between gap-4">
                      <span className="font-mono text-base truncate">{repo.repo_full_name}</span>
                      {!repo.is_installed && (
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          Not Installed
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <div className="space-y-4">
                      {/* Health Score */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-primary" />
                          <span className="text-sm text-muted-foreground">Health Score</span>
                        </div>
                        <span className="text-2xl font-bold text-primary">{repo.health_score}</span>
                      </div>

                      {/* Stats */}
                      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                        <div>
                          <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                            <GitPullRequest className="h-4 w-4" />
                            <span className="text-xs">Pull Requests</span>
                          </div>
                          <p className="text-2xl font-bold">{repo.pr_count}</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                            <FileText className="h-4 w-4" />
                            <span className="text-xs">Issues</span>
                          </div>
                          <p className="text-2xl font-bold">{repo.issue_count}</p>
                        </div>
                      </div>

                      {repo.last_activity && (
                        <p className="text-xs text-muted-foreground">
                          Last activity: {repo.last_activity}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Recent Activity */}
        {repos.length > 0 && (
          <section className="grid lg:grid-cols-2 gap-8">
            {/* Open PRs */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Recent Pull Requests</h2>
              <div className="space-y-4">
                {recentPRs.length === 0 ? (
                  <Card className="glass-card p-8 text-center">
                    <p className="text-muted-foreground">No recent pull requests</p>
                  </Card>
                ) : (
                  recentPRs.map((pr: any) => (
                    <PRCard
                      key={pr.pr_number}
                      prNumber={pr.pr_number}
                      title={pr.title}
                      author={pr.author}
                      healthScore={pr.health_score}
                      repoOwner={pr.repo_owner}
                      repoName={pr.repo_name}
                      validationStatus={pr.validation_status}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Pending Issues */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Pending Issues</h2>
              <div className="space-y-4">
                {recentIssues.length === 0 ? (
                  <Card className="glass-card p-8 text-center">
                    <p className="text-muted-foreground">No pending issues</p>
                  </Card>
                ) : (
                  recentIssues.map((issue: any) => (
                    <IssueCard
                      key={issue.issue_number}
                      issue={issue}
                      repoOwner={issue.repo_owner}
                      repoName={issue.repo_name}
                    />
                  ))
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
