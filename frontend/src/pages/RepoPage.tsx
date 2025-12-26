import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
// Header removed
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ExternalLink, TrendingUp, Settings as SettingsIcon, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { IssueCard } from '@/components/IssueCard';
import { PRCard } from '@/components/PRCard';
import { AuditPanel } from '@/components/AuditPanel';
import type { User, RepoSummary, Issue, PRSummary } from '@/types/api';

const RepoPage = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  // user and repos are in context but RepoPage mostly needs its own specific data
  // const { user } = useOutletContext<DashboardContextType>(); 

  const [repoData, setRepoData] = useState<RepoSummary | null>(null);
  // const [repos, setRepos] = useState<RepoSummary[]>([]); // Removed
  const [issues, setIssues] = useState<Issue[]>([]);
  const [pullRequests, setPullRequests] = useState<PRSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    if (!owner || !repo) return;

    try {
      const [repoDetails, issuesData, prsData] = await Promise.all([
        api.getRepo(owner, repo),
        api.getIssues(owner, repo),
        api.getPullRequests(owner, repo),
      ]);

      setRepoData(repoDetails);
      setIssues(issuesData);
      setPullRequests(prsData);
    } catch (error) {
      console.error('Failed to load repo data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Sync issues from GitHub
      await api.syncIssues(owner!, repo!);
      // Reload local data
      await loadData();

      // Show success toast if available
      if (typeof window !== 'undefined' && (window as any).toast) {
        (window as any).toast({
          title: 'Data Synced',
          description: 'Repository data has been refreshed from GitHub.',
        });
      }
    } catch (error) {
      console.error('Refresh failed:', error);
      if (typeof window !== 'undefined' && (window as any).toast) {
        (window as any).toast({
          title: 'Sync Failed',
          description: 'Failed to sync data from GitHub.',
          variant: 'destructive',
        });
      }
    }
  };

  useEffect(() => {
    loadData();
  }, [owner, repo]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header from Layout takes care of loading skeleton if global loading, 
            but this is local loading state. We just show the main content loading. */}
        <main className="container px-4 py-8">
          {/* Repo Header Skeleton */}
          <div className="mb-8">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <Skeleton className="h-10 w-64 mb-2" />
                <div className="flex items-center gap-4">
                  <Skeleton className="h-6 w-32" />
                </div>
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-9 w-32" />
                <Skeleton className="h-9 w-40" />
              </div>
            </div>
            <div className="flex gap-4">
              <Skeleton className="h-4 w-64" />
            </div>
          </div>

          {/* Tabs Skeleton */}
          <div className="space-y-6">
            <div className="flex gap-2 mb-6">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-24" />
            </div>

            {/* Content Skeleton */}
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-32 w-full rounded-xl" />
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!repoData || !owner || !repo) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header removed */}
        <main className="container px-4 py-8">
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">Repository not found</p>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header removed */}

      <main className="container px-4 py-8">
        {/* Repo Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-bold font-mono mb-2">{repoData.repo_full_name}</h1>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <span className="text-2xl font-bold text-primary">{repoData.health_score}</span>
                  <span className="text-sm text-muted-foreground">Health Score</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button asChild variant="outline">
                <a
                  href={`https://github.com/${owner}/${repo}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View on GitHub
                </a>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh Data
              </Button>

              {!repoData.is_installed && (
                <Button asChild>
                  <a href={`/api/repos/${owner}/${repo}/install`}>
                    Install RevFlo
                  </a>
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{pullRequests.length} Pull Requests</span>
            <span>•</span>
            <span>{issues.length} Issues</span>
            {repoData.last_activity && (
              <>
                <span>•</span>
                <span>Last activity: {repoData.last_activity}</span>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="issues" className="space-y-6">
          <TabsList>
            <TabsTrigger value="issues">Issues</TabsTrigger>
            <TabsTrigger value="prs">Pull Requests</TabsTrigger>
            <TabsTrigger value="audit">Audit</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="issues" className="space-y-4">
            {issues.length === 0 ? (
              <Card className="glass-card p-12 text-center">
                <p className="text-muted-foreground">No issues found</p>
              </Card>
            ) : (
              issues.map((issue) => (
                <IssueCard
                  key={issue.issue_number}
                  issue={issue}
                  repoOwner={owner}
                  repoName={repo}
                />
              ))
            )}
          </TabsContent>

          <TabsContent value="prs" className="space-y-4">
            {pullRequests.length === 0 ? (
              <Card className="glass-card p-12 text-center">
                <p className="text-muted-foreground">No pull requests found</p>
              </Card>
            ) : (
              pullRequests.map((pr) => (
                <PRCard
                  key={pr.pr_number}
                  prNumber={pr.pr_number}
                  title={pr.title}
                  author={pr.author}
                  healthScore={pr.health_score}
                  repoOwner={owner}
                  repoName={repo}
                  validationStatus={pr.validation_status}
                />
              ))
            )}
          </TabsContent>

          <TabsContent value="audit">
            <AuditPanel
              repoFullName={`${owner}/${repo}`}
              healthScore={repoData.health_score}
            />
          </TabsContent>

          <TabsContent value="settings">
            <Card className="glass-card p-8">
              <div className="flex items-start gap-4 mb-6">
                <SettingsIcon className="h-6 w-6 text-primary mt-1" />
                <div>
                  <h3 className="text-xl font-semibold mb-2">Repository Settings</h3>
                  <p className="text-muted-foreground mb-4">
                    Configure RevFlo settings for this repository.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Settings panel coming soon. Configure webhook preferences, checklist templates,
                  and validation rules.
                </p>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default RepoPage;
