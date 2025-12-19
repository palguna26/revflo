import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ExternalLink, RefreshCw, TrendingUp, ArrowLeft, AlertTriangle, CheckCircle2, ShieldAlert, Ban, HelpCircle, AlertOctagon, FileCode, Check } from 'lucide-react';
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

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header loading={true} />
        <main className="container max-w-7xl px-4 py-8">
          <Skeleton className="h-24 w-full mb-6" />
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-4"><Skeleton className="h-96" /></div>
            <div className="space-y-4"><Skeleton className="h-48" /></div>
          </div>
        </main>
      </div>
    );
  }

  if (!pr || !owner || !repo) return <div className="p-8 text-center">PR not found</div>;

  const isBlocked = pr.merge_decision === false;
  const getBlockReasonText = (reason: string | null | undefined) => {
    switch (reason) {
      case 'BLOCK_CHECKLIST_FAILED': return "Mandatory requirements failed.";
      case 'BLOCK_INDETERMINATE_EVIDENCE': return "Insufficient evidence in diff.";
      case 'BLOCK_SECURITY_CRITICAL': return "Critical security vulnerabilities.";
      case 'BLOCK_INSUFFICIENT_ISSUE_SPEC': return "Issue spec too vague.";
      default: return "Merge criteria not met.";
    }
  };

  const parseMessage = (msg: string) => {
    if (msg.includes("Consequence:")) {
      const parts = msg.split("Consequence:");
      return (
        <span>
          {parts[0]} <br />
          <span className="font-semibold text-destructive/90 mt-1 block text-xs uppercase tracking-wide">Consequence: {parts[1]}</span>
        </span>
      );
    }
    return msg;
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header user={user || undefined} repos={repos} />

      <main className="container max-w-7xl px-4 py-6">
        {/* Breadcrumb & Meta */}
        <div className="mb-6">
          <Link to={`/repo/${owner}/${repo}`} className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-1 mb-3">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Repository
          </Link>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="font-mono font-normal">#{pr.pr_number}</Badge>
                <Badge variant={isBlocked ? "destructive" : "default"}>
                  {isBlocked ? "Blocked" : pr.validation_status}
                </Badge>
              </div>
              <h1 className="text-2xl font-bold tracking-tight mb-1">{pr.title}</h1>
              <p className="text-sm text-muted-foreground">Authored by <span className="font-medium text-foreground">{pr.author}</span></p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleRevalidate} disabled={revalidating}>
                <RefreshCw className={`mr-2 h-3.5 w-3.5 ${revalidating ? 'animate-spin' : ''}`} />
                Revalidate
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a href={pr.github_url} target="_blank" rel="noopener noreferrer"><ExternalLink className="mr-2 h-3.5 w-3.5" /> GitHub</a>
              </Button>
              {!isBlocked && pr.validation_status === 'validated' && (
                <Button size="sm" className="bg-success hover:bg-success/90 text-white">
                  <CheckCircle2 className="mr-2 h-3.5 w-3.5" /> Merge
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-12 gap-8">
          {/* Left Main Content (8 cols) */}
          <div className="lg:col-span-8 space-y-6">

            {/* Blocking Banner */}
            {isBlocked && (
              <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 flex items-start gap-3">
                <Ban className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <h3 className="font-semibold text-destructive">Merge Blocked by Policy</h3>
                  <p className="text-sm text-muted-foreground mt-1">{getBlockReasonText(pr.block_reason)}</p>
                  {pr.block_reason === 'BLOCK_INSUFFICIENT_ISSUE_SPEC' && (
                    <Button variant="link" className="h-auto p-0 text-destructive text-xs mt-2 underline">
                      View Issue Details
                    </Button>
                  )}
                </div>
              </div>
            )}

            <Tabs defaultValue="checklist" className="w-full">
              <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent gap-6">
                <TabsTrigger value="checklist" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-3 px-0">
                  Checklist <Badge variant="secondary" className="ml-2">{pr.manifest?.checklist_items.length || 0}</Badge>
                </TabsTrigger>
                <TabsTrigger value="issues" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-3 px-0">
                  Code Health <Badge variant={pr.code_health.length > 0 ? "destructive" : "secondary"} className="ml-2">{pr.code_health.length}</Badge>
                </TabsTrigger>
                <TabsTrigger value="tests" className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none pb-3 px-0">
                  Suggested Tests
                </TabsTrigger>
              </TabsList>

              <TabsContent value="checklist" className="pt-6 space-y-4">
                {pr.manifest?.checklist_items.map((item) => {
                  const isPassed = item.status === 'passed';
                  const isIndeterminate = item.status === 'indeterminate';
                  return (
                    <Card key={item.id} className={`transition-all ${!isPassed && !isIndeterminate ? 'border-destructive/30 bg-destructive/5' : ''}`}>
                      <div className="flex items-start p-4 gap-3">
                        <div className="mt-0.5">
                          {isPassed ? <CheckCircle2 className="h-5 w-5 text-success" /> :
                            isIndeterminate ? <HelpCircle className="h-5 w-5 text-muted-foreground" /> :
                              <AlertOctagon className="h-5 w-5 text-destructive" />}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium leading-relaxed">{item.text}</p>
                          {isIndeterminate && (
                            <div className="mt-2 text-xs bg-background/50 p-2 rounded border border-border/50 text-muted-foreground">
                              <strong>AI Note:</strong> Insufficient evidence in the diff to verify this item. Manual review required.
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  )
                })}
              </TabsContent>

              <TabsContent value="issues" className="pt-6 space-y-4">
                {pr.code_health.length === 0 ? (
                  <div className="text-center py-12 border rounded-lg bg-muted/10 border-dashed">
                    <CheckCircle2 className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">No code health issues found.</p>
                  </div>
                ) : (
                  pr.code_health.map((issue) => (
                    <Card key={issue.id} className="group hover:border-destructive/40 transition-colors">
                      <CardContent className="p-4 flex gap-4">
                        <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline" className="uppercase text-[10px] tracking-wider">{issue.severity}</Badge>
                            <span className="text-xs text-muted-foreground font-mono">{issue.file_path}:{issue.line_number}</span>
                          </div>
                          <p className="text-sm font-medium mb-2">{parseMessage(issue.message)}</p>
                          {issue.suggestion && (
                            <div className="bg-muted/30 p-2 rounded text-xs font-mono border-l-2 border-primary/20">
                              {issue.suggestion}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </TabsContent>

              <TabsContent value="tests" className="pt-6 space-y-4">
                {pr.suggested_tests.length === 0 ? <p className="text-muted-foreground">No suggestions.</p> :
                  pr.suggested_tests.map(test => <SuggestedTestCard key={test.test_id} test={test} />)
                }
              </TabsContent>
            </Tabs>
          </div>

          {/* Right Sidebar (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <Card className="bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-widest">Health Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-2">
                  <span className="text-5xl font-bold tracking-tighter text-primary">{pr.health_score}</span>
                  <span className="text-sm text-muted-foreground mb-2">/ 100</span>
                </div>
                <div className="h-2 w-full bg-secondary mt-4 rounded-full overflow-hidden">
                  <div className="h-full bg-primary transition-all duration-500" style={{ width: `${pr.health_score}%` }} />
                </div>
              </CardContent>
            </Card>

            {pr.coverage_advice.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileCode className="h-4 w-4" /> Coverage Gaps
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {pr.coverage_advice.map((advice, i) => (
                    <div key={i} className="text-sm">
                      <p className="font-mono text-xs text-muted-foreground mb-1">{advice.file_path}</p>
                      <p>{advice.suggestion}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default PRDetailPage;
