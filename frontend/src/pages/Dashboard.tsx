import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { User, RepoSummary, PRSummary, Issue } from '@/types/api';
import { PRCard } from '@/components/PRCard';
import { IssueCard } from '@/components/IssueCard';
import { RepoCard } from '@/components/RepoCard';
import { ManageReposDialog } from '@/components/ManageReposDialog';

import { useOutletContext } from 'react-router-dom';
import type { DashboardContextType } from '@/layouts/DashboardLayout';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, repos, setUser, setRepos } = useOutletContext<DashboardContextType>();

  const [recentPRs, setRecentPRs] = useState<PRSummary[]>([]);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);

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

  const handleAddRepo = async (repoFullName: string) => {
    try {
      await api.addRepo(repoFullName);
      const updatedRepos = await api.getRepos();
      setRepos(updatedRepos);
    } catch (error) {
      console.error('Failed to add repo:', error);
    }
  };

  const handleRemoveRepo = async (repoFullName: string) => {
    try {
      await api.removeRepo(repoFullName);
      const updatedRepos = await api.getRepos();
      setRepos(updatedRepos);
    } catch (error) {
      console.error('Failed to remove repo:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="container max-w-6xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8 pb-6 border-b">
          <h1 className="text-3xl font-semibold tracking-tight mb-2">
            Welcome back, {user?.name || user?.login}!
          </h1>
          <p className="text-muted-foreground">
            Manage your repositories and track code quality across your projects.
          </p>
        </div>

        {/* Repositories Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold tracking-tight">Your Repositories</h2>
            <ManageReposDialog
              repos={repos}
              onAddRepo={handleAddRepo}
              onRemoveRepo={handleRemoveRepo}
            />
          </div>

          {repos.length === 0 ? (
            <div className="glass-card rounded-xl p-12 text-center">
              <p className="text-muted-foreground mb-6">No repositories found.</p>
              <Button asChild>
                <a
                  href="https://github.com/apps/revflo/installations/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  Install RevFlo
                </a>
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {repos.map((repo) => (
                <RepoCard
                  key={repo.repo_full_name}
                  repo={repo}
                  onClick={() => navigate(`/repo/${repo.owner}/${repo.name}`)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity Section - Only show if repos exist */}
        {repos.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Recent Pull Requests */}
            <div>
              <h2 className="text-xl font-semibold tracking-tight mb-4">Recent Pull Requests</h2>
              <div className="space-y-3">
                {recentPRs.length === 0 ? (
                  <Card className="glass-card p-8 text-center">
                    <p className="text-sm text-muted-foreground">No recent pull requests</p>
                  </Card>
                ) : (
                  recentPRs.map((pr: any) => (
                    <PRCard
                      key={`${pr.repo_owner}/${pr.repo_name}/${pr.pr_number}`}
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
              <h2 className="text-xl font-semibold tracking-tight mb-4">Pending Issues</h2>
              <div className="space-y-3">
                {recentIssues.length === 0 ? (
                  <Card className="glass-card p-8 text-center">
                    <p className="text-sm text-muted-foreground">No pending issues</p>
                  </Card>
                ) : (
                  recentIssues.map((issue: any) => (
                    <IssueCard
                      key={`${issue.repo_owner}/${issue.repo_name}/${issue.issue_number}`}
                      issue={issue}
                      repoOwner={issue.repo_owner}
                      repoName={issue.repo_name}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
