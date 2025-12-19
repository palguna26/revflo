import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  ExternalLink, RefreshCw, ArrowLeft, AlertTriangle, CheckCircle2,
  ShieldAlert, Ban, HelpCircle, AlertOctagon, FileCode, Check,
  GitPullRequest, LayoutDashboard, Clock
} from 'lucide-react';
import { api } from '@/lib/api';
import { SuggestedTestCard } from '@/components/SuggestedTestCard';
import { useToast } from '@/hooks/use-toast';
import type { User, RepoSummary, PRDetail, CodeHealthIssue } from '@/types/api';

const PRDetailPage = () => {
  const { owner, repo, prNumber } = useParams<{ owner: string; repo: string; prNumber: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [pr, setPr] = useState<PRDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo || !prNumber) return;
      try {
        const [userData, reposData, prData] = await Promise.all([
          api.getMe(),
          api.getRepos(),
          api.getPR(owner, repo, parseInt(prNumber)),
        ]);
        setUser(userData);
        setRepos(reposData);
        setPr(prData);
      } catch (error) {
        console.error('Failed to load PR:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [owner, repo, prNumber]);

  const handleRevalidate = async () => {
    if (!owner || !repo || !prNumber) return;
    setRevalidating(true);
    try {
      await api.revalidatePR(owner, repo, parseInt(prNumber));
      toast({ title: 'Revalidation Started', description: 'Analysis in progress...' });
      setTimeout(async () => {
        const updatedPR = await api.getPR(owner, repo, parseInt(prNumber));
        setPr(updatedPR);
      }, 2000);
    } catch {
      toast({ title: 'Revalidation Failed', variant: 'destructive' });
    } finally {
      setRevalidating(false);
    }
  };

  if (loading) return <PRSkeleton />;
  if (!pr || !owner || !repo) return <div className="p-8 text-center">PR not found</div>;

  const isBlocked = pr.merge_decision === false;
  const checklistProgress = pr.manifest?.checklist_items
    ? (pr.manifest.checklist_items.filter(i => i.status === 'passed').length / pr.manifest.checklist_items.length) * 100
    : 0;

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 pb-20">
      <Header user={user || undefined} repos={repos} />

      <div className="bg-muted/30 border-b relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[300px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="container max-w-7xl mx-auto px-4 py-8 relative z-10">

          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
            <Link to="/dashboard" className="hover:text-primary transition-colors flex items-center gap-1">
              <LayoutDashboard className="h-3.5 w-3.5" /> Dashboard
            </Link>
            <span>/</span>
            <Link to={`/repo/${owner}/${repo}/audit`} className="hover:text-primary transition-colors">
              {owner}/{repo}
            </Link>
            <span>/</span>
            <span className="text-foreground font-medium">PR #{prNumber}</span>
          </div>

          {/* Header Content */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-4 max-w-3xl">
              <div className="flex items-center gap-3">
                <Badge variant={isBlocked ? "destructive" : "outline"} className={`text-sm px-2.5 py-0.5 uppercase tracking-wide font-semibold ${isBlocked ? "" : "border-green-500/50 text-green-600 bg-green-500/10"}`}>
                  {isBlocked ? "Block Policy Active" : "Ready for Merge"}
                </Badge>
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" /> Reviewed just now
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground leading-tight">
                {pr.title}
              </h1>
              <div className="flex items-center gap-3">
                <span className="bg-muted px-2 py-1 rounded text-xs font-mono text-muted-foreground">
                  {pr.head_sha.substring(0, 7)}
                </span>
                <span className="text-muted-foreground text-sm">by <span className="text-foreground font-medium">{pr.author}</span></span>
              </div>
            </div>

            <div className="flex flex-row md:flex-col gap-3 shrink-0">
              {!isBlocked && (
                <Button size="lg" className="w-full md:w-auto shadow-lg shadow-green-500/20 bg-green-600 hover:bg-green-700 text-white border-none">
                  <CheckCircle2 className="mr-2 h-5 w-5" /> Merge Pull Request
                </Button>
              )}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleRevalidate} disabled={revalidating}>
                  <RefreshCw className={`mr-2 h-3.5 w-3.5 ${revalidating ? 'animate-spin' : ''}`} />
                  Revalidate
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href={pr.github_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="container max-w-7xl mx-auto px-4 py-10">
        <div className="grid lg:grid-cols-12 gap-10">

          {/* Left Panel: Compliance Engine */}
          <div className="lg:col-span-8 space-y-8">

            {/* Block Reason Card */}
            {isBlocked && (
              <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 animate-in fade-in slide-in-from-top-4">
                <div className="flex items-start gap-4">
                  <div className="bg-destructive/10 p-3 rounded-full">
                    <Ban className="h-6 w-6 text-destructive" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-destructive tracking-tight">Merge Blocked: {getBlockReasonText(pr.block_reason)}</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      This PR currently violates strict repository policies. Address the issues below to unlock merging.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold tracking-tight">Compliance Checklist</h2>
                <span className="text-sm text-muted-foreground font-mono">{Math.round(checklistProgress)}% Passing</span>
              </div>
              <Progress value={checklistProgress} className="h-2" />

              <div className="grid gap-3 mt-4">
                {pr.manifest?.checklist_items.map((item) => (
                  <ChecklistItem key={item.id} item={item} />
                ))}
              </div>
            </div>

            <div className="space-y-4 pt-4">
              <h2 className="text-xl font-bold tracking-tight">AI Code Analysis</h2>
              <div className="space-y-4">
                {pr.code_health.length === 0 ? (
                  <div className="p-8 border border-dashed rounded-xl text-center bg-muted/10">
                    <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-3" />
                    <p className="text-muted-foreground">No critical issues found. Code looks healthy!</p>
                  </div>
                ) : (
                  pr.code_health.map((issue) => (
                    <IssueCard key={issue.id} issue={issue} />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Panel: Metadata & Suggestions */}
          <div className="lg:col-span-4 space-y-8">

            {/* Health Score */}
            <Card className="border-border/60 shadow-sm overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-primary/40" />
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Code Health Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-6xl font-bold tracking-tighter text-foreground">{pr.health_score}</span>
                  <span className="text-lg text-muted-foreground font-light">/100</span>
                </div>
                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div className="h-full bg-primary transition-all duration-1000 ease-out" style={{ width: `${pr.health_score}%` }} />
                </div>
              </CardContent>
            </Card>

            {/* Suggested Tests */}
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2">
                <FileCode className="h-4 w-4" /> Recommended Tests
              </h3>
              <div className="space-y-3">
                {pr.suggested_tests.map(test => <SuggestedTestCard key={test.test_id} test={test} />)}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
};

// --- Sub Components ---

function ChecklistItem({ item }: { item: any }) {
  const isPassed = item.status === 'passed';
  const isIndeterminate = item.status === 'indeterminate';

  return (
    <div className={`group flex items-start p-4 rounded-lg border transition-all ${isPassed ? 'bg-card border-border/40 hover:border-green-500/30' :
        isIndeterminate ? 'bg-secondary/20 border-border/60' :
          'bg-destructive/5 border-destructive/20'
      }`}>
      <div className={`mt-0.5 p-1 rounded-full ${isPassed ? 'text-green-500 bg-green-500/10' :
          isIndeterminate ? 'text-orange-500 bg-orange-500/10' :
            'text-destructive bg-destructive/10'
        }`}>
        {isPassed ? <Check className="h-4 w-4" /> :
          isIndeterminate ? <HelpCircle className="h-4 w-4" /> :
            <AlertOctagon className="h-4 w-4" />}
      </div>
      <div className="ml-3 flex-1">
        <p className={`text-sm font-medium ${isPassed ? 'text-foreground' : 'text-foreground/90'}`}>
          {item.text}
        </p>
        {isIndeterminate && (
          <p className="text-xs text-muted-foreground mt-1.5 bg-background/50 p-2 rounded border border-border/50">
            <span className="font-semibold text-orange-500">AI Note:</span> Insufficient context to verify automatically. Please review manually.
          </p>
        )}
      </div>
    </div>
  )
}

function IssueCard({ issue }: { issue: CodeHealthIssue }) {
  const parseMessage = (msg: string) => {
    if (msg.includes("Consequence:")) {
      const parts = msg.split("Consequence:");
      return (
        <span>
          {parts[0]}
          <span className="block mt-2 text-xs font-semibold text-destructive/80 uppercase tracking-wider bg-destructive/5 p-1 rounded w-fit">
            Consequence: {parts[1]}
          </span>
        </span>
      );
    }
    return msg;
  };

  return (
    <Card className="border-l-4 border-l-destructive/60 hover:shadow-md transition-shadow">
      <CardHeader className="pb-2 pt-4">
        <div className="flex justify-between items-start">
          <Badge variant="outline" className="uppercase text-[10px] tracking-wider border-destructive/30 text-destructive">{issue.severity}</Badge>
          <span className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
            {issue.file_path}:{issue.line_number}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm font-medium leading-relaxed">
          {parseMessage(issue.message)}
        </p>
        {issue.suggestion && (
          <div className="mt-3 bg-muted/40 p-3 rounded-md border border-border/50">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 font-semibold">Suggested Fix</div>
            <code className="text-xs font-mono text-primary block whitespace-pre-wrap">
              {issue.suggestion}
            </code>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getBlockReasonText(reason: string | null | undefined) {
  switch (reason) {
    case 'BLOCK_CHECKLIST_FAILED': return "Mandatory Requirements Failed";
    case 'BLOCK_INDETERMINATE_EVIDENCE': return "Insufficient Evidence in Diff";
    case 'BLOCK_SECURITY_CRITICAL': return "Critical Security Vulnerabilities Detected";
    case 'BLOCK_INSUFFICIENT_ISSUE_SPEC': return "Linked Issue Spec Too Vague";
    default: return "Merge Criteria Not Met";
  }
};

function PRSkeleton() {
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <div className="bg-muted/30 border-b py-12">
        <div className="container max-w-7xl px-4 space-y-4">
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-10 w-full max-w-2xl" />
          <Skeleton className="h-6 w-96" />
        </div>
      </div>
      <div className="container max-w-7xl px-4 py-10 grid lg:grid-cols-12 gap-10">
        <div className="lg:col-span-8 space-y-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
        <div className="lg:col-span-4">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  )
}

export default PRDetailPage;
