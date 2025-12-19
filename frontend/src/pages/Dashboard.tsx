import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  TrendingUp, GitPullRequest, FileText, Plus, ExternalLink, RefreshCw,
  Activity, ArrowRight, Star, Clock, AlertCircle, CheckCircle2, Search, LayoutGrid, List as ListIcon
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { User, RepoSummary, PRSummary, Issue } from '@/types/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [recentPRs, setRecentPRs] = useState<PRSummary[]>([]);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

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

  const handleRefresh = () => {
    setIsRefreshing(true);
    window.location.reload();
  };

  const getTimeGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 pb-20">
      <Header />

      {/* Welcome Hero */}
      <div className="border-b bg-card/30 backdrop-blur-sm sticky top-16 z-30">
        <div className="container mx-auto max-w-7xl px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
                <span>{getTimeGreeting()},</span>
                <span className="text-primary bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">
                  {user?.name || user?.login || 'Engineer'}
                </span>
              </h1>
              <p className="text-muted-foreground text-sm font-medium">
                You have <span className="text-foreground font-semibold">{recentPRs.length} active PRs</span> requiring attention today.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-2 shadow-sm border-dashed"
                onClick={handleRefresh}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                Sync Data
              </Button>
              <div className="h-4 w-px bg-border mx-1" />
              <div className="bg-muted p-1 rounded-lg flex items-center gap-1">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="icon" className="h-7 w-7 rounded-sm"
                  onClick={() => setViewMode('grid')}
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="icon" className="h-7 w-7 rounded-sm"
                  onClick={() => setViewMode('list')}
                >
                  <ListIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="container mx-auto max-w-7xl px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-10">

        {/* Left Col: Repositories */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-foreground/90 flex items-center gap-2">
              <Star className="h-4 w-4 text-orange-400 fill-orange-400/20" /> Your Repositories
            </h2>
            <Button variant="link" className="text-xs h-auto p-0 text-muted-foreground hover:text-primary">
              Manage Selection
            </Button>
          </div>

          {repos.length === 0 ? (
            <EmptyState />
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {repos.map((repo) => (
                <RepoCard key={repo.id || repo.repo_full_name} repo={repo} navigate={navigate} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border bg-card/50 shadow-sm divide-y">
              {repos.map((repo) => (
                <RepoListItem key={repo.id || repo.repo_full_name} repo={repo} navigate={navigate} />
              ))}
            </div>
          )}
        </div>

        {/* Right Col: Activity Feed */}
        <div className="lg:col-span-4 space-y-6">
          <h2 className="text-lg font-semibold tracking-tight text-foreground/90 flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-500" /> Recent Activity
          </h2>
          <Card className="h-auto border-border/60 shadow-sm bg-card/60">
            <CardContent className="p-0">
              <ScrollArea className="h-[500px] w-full p-4">
                {recentPRs.length === 0 && recentIssues.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground text-sm">No recent activity detected.</div>
                ) : (
                  <div className="space-y-6">
                    {/* PRs */}
                    {recentPRs.length > 0 && (
                      <div className="space-y-3">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-2 border-l-2 border-primary/20">Active PRs</h3>
                        <div className="space-y-3">
                          {recentPRs.map(pr => <ActivityItem key={pr.id || pr.pr_number} type="pr" data={pr} navigate={navigate} />)}
                        </div>
                      </div>
                    )}

                    {/* Issues */}
                    {recentIssues.length > 0 && (
                      <div className="space-y-3">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-2 border-l-2 border-orange-500/20">New Issues</h3>
                        <div className="space-y-3">
                          {recentIssues.map(issue => <ActivityItem key={issue.id || issue.issue_number} type="issue" data={issue} navigate={navigate} />)}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

// --- Sub Components ---

function RepoCard({ repo, navigate }: { repo: RepoSummary, navigate: any }) {
  // Use available identifier
  const repoId = repo.id;

  return (
    <Card className="group relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 border-border/60 bg-gradient-to-b from-card to-card/50">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/0 to-transparent group-hover:via-primary/50 transition-all duration-500" />

      <CardHeader className="pb-3 pt-5">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground font-light">{repo.owner} /</span>
            </div>
            <CardTitle className="text-lg font-bold tracking-tight text-foreground group-hover:text-primary transition-colors cursor-pointer" onClick={() => navigate(`/repo/${repo.owner}/${repo.name}/audit`)}>
              {repo.name}
            </CardTitle>
          </div>
          {repo.private ? <Badge variant="secondary" className="text-[10px] font-mono uppercase bg-muted text-muted-foreground/70">Private</Badge> : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground line-clamp-2 h-10">
          {repo.description || "No description provided."}
        </p>

        <div className="flex items-center gap-2 pt-2">
          <Button
            variant="default"
            size="sm"
            className="w-full shadow-sm bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() => navigate(`/repo/${repo.owner}/${repo.name}/audit`)}
          >
            <Activity className="h-3.5 w-3.5 mr-2" /> Health Audit
          </Button>
          <Button variant="outline" size="sm" className="px-3" asChild>
            <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RepoListItem({ repo, navigate }: { repo: RepoSummary, navigate: any }) {
  return (
    <div className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors group">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
          <GitPullRequest className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors cursor-pointer" onClick={() => navigate(`/repo/${repo.owner}/${repo.name}/audit`)}>
            {repo.owner}/{repo.name}
          </h3>
          <p className="text-xs text-muted-foreground line-clamp-1 max-w-[400px]">
            {repo.description}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/repo/${repo.owner}/${repo.name}/audit`)}>
          Audit
        </Button>
        <a href={repo.html_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground p-2">
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>
    </div>
  )
}

function ActivityItem({ type, data, navigate }: { type: 'pr' | 'issue', data: any, navigate: any }) {
  // Parsing date roughly
  const date = new Date(data.created_at || Date.now());
  const timeAgo = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60)) + 'h ago';

  // Safe property access with type narrowing logic or fallback
  const number = data.pr_number || data.issue_number || data.number || '0';
  const state = data.state || data.status;

  const handleNav = () => {
    // Try to parse repo from repo_full_name if available
    if (data.repo_full_name) {
      const parts = data.repo_full_name.split('/');
      if (parts.length === 2) {
        if (type === 'pr') navigate(`/repo/${parts[0]}/${parts[1]}/pr/${number}`);
        // Issue nav logic could be added here
        return;
      }
    }
    // Fallback to github url
    if (data.github_url) {
      window.open(data.github_url, '_blank');
    }
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-transparent hover:border-border/50 hover:bg-muted/40 transition-all cursor-pointer group"
      onClick={handleNav}
    >
      <div className={`mt-0.5 min-w-[2rem] h-8 w-8 rounded-full flex items-center justify-center border ${type === 'pr' ? 'bg-primary/5 border-primary/20 text-primary' : 'bg-orange-500/5 border-orange-500/20 text-orange-500'}`}>
        {type === 'pr' ? <GitPullRequest className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
      </div>
      <div className="space-y-1 overflow-hidden w-full">
        <div className="flex justify-between items-start gap-2">
          <p className="text-sm font-medium text-foreground leading-tight line-clamp-1 group-hover:text-primary transition-colors">
            {data.title}
          </p>
          {data.repo_full_name && (
            <span className="text-[10px] text-muted-foreground bg-muted px-1 rounded shrink-0 font-mono">
              {data.repo_full_name.split('/')[1]}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
          <span>#{number}</span>
          <span>•</span>
          <span>{timeAgo}</span>
          {state && (
            <Badge variant="outline" className={`h-4 px-1 py-0 text-[9px] uppercase ${state === 'open' || state === 'validated' ? 'text-green-600 border-green-600/30' : 'text-purple-500 border-purple-500/30'}`}>
              {state}
            </Badge>
          )}
        </div>
      </div>
      <div className="ml-auto opacity-0 group-hover:opacity-100 transition-width">
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed p-8 text-center bg-muted/20">
      <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
        <Search className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-semibold">No Repositories Found</h3>
      <p className="text-muted-foreground text-sm mt-1 max-w-sm mx-auto mb-6">
        Appears you haven't synced any repositories yet. Connect your GitHub account to get started.
      </p>
      <Button>Add Repository</Button>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <div className="border-b py-8 sticky top-16 bg-background z-10">
        <div className="container max-w-7xl px-4 space-y-2">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-5 w-96" />
        </div>
      </div>
      <div className="container max-w-7xl px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-8 space-y-4">
          <div className="grid grid-cols-2 gap-5">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 w-full rounded-xl" />)}
          </div>
        </div>
        <div className="lg:col-span-4">
          <Skeleton className="h-[600px] w-full rounded-xl" />
        </div>
      </div>
    </div>
  )
}

export default Dashboard;
