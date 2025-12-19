import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ExternalLink, TrendingUp, Settings as SettingsIcon, GitPullRequest,
  AlertCircle, Activity, LayoutGrid, Clock
} from 'lucide-react';
import { api } from '@/lib/api';
import { IssueCard } from '@/components/IssueCard';
import { PRCard } from '@/components/PRCard';
import type { User, RepoSummary, Issue, PRSummary } from '@/types/api';

const RepoPage = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repoData, setRepoData] = useState<RepoSummary | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [pullRequests, setPullRequests] = useState<PRSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo) return;
      try {
        setLoading(true);
        const [userData, repoDetails, issuesData, prsData] = await Promise.all([
          api.getMe(),
          api.getRepo(owner, repo),
          api.getIssues(owner, repo),
          api.getPullRequests(owner, repo),
        ]);
        setUser(userData);
        setRepoData(repoDetails);
        setIssues(issuesData);
        setPullRequests(prsData);
        setRepos([]);
      } catch (error) {
        console.error('Failed to load repo data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [owner, repo]);

  if (loading) return <RepoSkeleton />;

  if (!repoData || !owner || !repo) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans">
        <Header user={user || undefined} repos={repos} />
        <main className="container max-w-7xl px-4 py-20 text-center">
          <div className="bg-muted/30 p-12 rounded-2xl border border-dashed">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">Repository Not Found</h2>
            <p className="text-muted-foreground mb-6">We couldn't locate the repository you're looking for.</p>
            <Button asChild><Link to="/dashboard">Return to Dashboard</Link></Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 pb-20">
      <Header user={user || undefined} repos={repos} />

      {/* Repo Header */}
      <div className="border-b bg-card/30 backdrop-blur-sm sticky top-14 z-30">
        <div className="container max-w-7xl px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <Link to="/dashboard" className="hover:text-primary transition-colors">Dashboard</Link>
                <span>/</span>
                <span className="text-foreground font-medium">{owner}</span>
              </div>
              <div className="flex items-center gap-4">
                <h1 className="text-3xl font-bold tracking-tight text-foreground">{repo}</h1>
                <Badge variant="outline" className={`font-mono text-xs uppercase tracking-wider ${repoData.private ? 'border-amber-500/50 text-amber-500 bg-amber-500/10' : 'border-blue-500/50 text-blue-500 bg-blue-500/10'}`}>
                  {repoData.private ? 'Private' : 'Public'}
                </Badge>
              </div>
              <p className="text-muted-foreground max-w-2xl line-clamp-1">{repoData.description}</p>
            </div>

            <div className="flex items-center gap-3">
              <Button size="sm" asChild className="shadow-lg shadow-primary/20 bg-primary hover:bg-primary/90">
                <Link to={`/repo/${owner}/${repo}/audit`}>
                  <Activity className="mr-2 h-4 w-4" /> Run Audit
                </Link>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a href={repoData.html_url || `https://github.com/${owner}/${repo}`} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" /> GitHub
                </a>
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-8 mt-8 border-t pt-6">
            <div className="flex items-center gap-2 group cursor-help">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <div className="text-2xl font-bold tracking-tight leading-none">{repoData.health_score}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Health Score</div>
              </div>
            </div>
            <Separator orientation="vertical" className="h-10" />
            <div className="flex items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                <GitPullRequest className="h-5 w-5" />
              </div>
              <div>
                <div className="text-2xl font-bold tracking-tight leading-none">{repoData.pr_count}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Open PRs</div>
              </div>
            </div>
            <Separator orientation="vertical" className="h-10" />
            <div className="flex items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-orange-500/10 flex items-center justify-center text-orange-500">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div>
                <div className="text-2xl font-bold tracking-tight leading-none">{repoData.issue_count}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Issues</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="container max-w-7xl px-4 py-8">
        <Tabs defaultValue="issues" className="space-y-8">
          <TabsList className="bg-transparent border-b w-full justify-start rounded-none h-auto p-0 gap-8">
            <TabsTrigger value="issues" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-4 text-sm font-medium px-2">
              Issues <Badge variant="secondary" className="ml-2 bg-muted text-muted-foreground">{issues.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="prs" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-4 text-sm font-medium px-2">
              Pull Requests <Badge variant="secondary" className="ml-2 bg-muted text-muted-foreground">{pullRequests.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-4 text-sm font-medium px-2">
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="issues" className="space-y-4 animate-in slide-in-from-bottom-2 fade-in duration-500">
            {issues.length === 0 ? (
              <EmptyTabState icon={AlertCircle} title="No Open Issues" description="There are no open issues tracked for this repository." />
            ) : (
              <div className="grid gap-4">
                {issues.map((issue) => (
                  <IssueCard key={issue.issue_number} issue={issue} repoOwner={owner} repoName={repo} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="prs" className="space-y-4 animate-in slide-in-from-bottom-2 fade-in duration-500">
            {pullRequests.length === 0 ? (
              <EmptyTabState icon={GitPullRequest} title="No Active PRs" description="There are no open pull requests tracked for this repository." />
            ) : (
              <div className="grid gap-4">
                {pullRequests.map((pr) => (
                  <PRCard key={pr.pr_number} prNumber={pr.pr_number} title={pr.title} author={pr.author} healthScore={pr.health_score} repoOwner={owner} repoName={repo} validationStatus={pr.validation_status} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="animate-in slide-in-from-bottom-2 fade-in duration-500">
            <Card>
              <CardHeader>
                <CardTitle>Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Repository settings panel is under construction.</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

function EmptyTabState({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-xl bg-muted/10 text-center">
      <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground mb-4">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-muted-foreground mt-1 max-w-sm">{description}</p>
    </div>
  )
}

function RepoSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="border-b py-10 bg-background/50">
        <div className="container max-w-7xl px-4 space-y-6">
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-4">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-32" />
          </div>
        </div>
      </div>
      <div className="container max-w-7xl px-4 py-8 space-y-4">
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    </div>
  )
}

export default RepoPage;
