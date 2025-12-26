
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { CheckCircle2, XCircle, Clock, ExternalLink, ArrowLeft, RefreshCw, MessageSquare } from 'lucide-react';
import { api } from '@/lib/api';
import { toast, useToast } from '@/hooks/use-toast';
import { GitHubStateBadge } from '@/components/GitHubStateBadge';
import { SyncStatus } from '@/components/SyncStatus';
import { ChecklistItem } from '@/components/ChecklistItem';
import type { User, RepoSummary, Issue, ChecklistItem as IssueChecklistItem } from '@/types/api';

const IssueDetail = () => {
  const { owner, repo, issueNumber } = useParams<{ owner: string; repo: string; issueNumber: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [targetPrNumber, setTargetPrNumber] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo || !issueNumber) {
        console.error('Missing params:', { owner, repo, issueNumber });
        return;
      }

      try {
        console.log('Loading issue data for:', { owner, repo, issueNumber });

        const [userData, reposData, issueData] = await Promise.all([
          api.getMe(),
          api.getRepos(),
          api.getIssue(owner, repo, parseInt(issueNumber)),
        ]);

        console.log('Loaded data:', {
          user: userData,
          repos: reposData?.length,
          issue: issueData
        });

        setUser(userData);
        setRepos(reposData);
        setIssue(issueData);
      } catch (error) {
        console.error('Failed to load issue data:', error);
        // Log the full error details
        if (error instanceof Error) {
          console.error('Error message:', error.message);
          console.error('Error stack:', error.stack);
        }
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [owner, repo, issueNumber]);

  const handleRunReview = async () => {
    if (!owner || !repo || !issueNumber || !targetPrNumber) return;

    setReviewing(true);
    try {
      await api.runReview(owner, repo, parseInt(issueNumber), parseInt(targetPrNumber));

      toast({
        title: 'Review Complete',
        description: `PR #${targetPrNumber} has been validated against this checklist.`,
      });

      // Reload issue data
      const updatedIssue = await api.getIssue(owner, repo, parseInt(issueNumber));
      setIssue(updatedIssue);

    } catch (error) {
      console.error(error);
      toast({
        title: 'Review Failed',
        description: 'Unable to complete the review. Please check the PR number and try again.',
        variant: 'destructive',
      });
    } finally {
      setReviewing(false);
    }
  };

  const handleRegenerate = async () => {
    if (!owner || !repo || !issueNumber) return;

    setRegenerating(true);
    try {
      await api.generateChecklist(owner, repo, parseInt(issueNumber));

      toast({
        title: 'Checklist Generated',
        description: 'A new checklist based on the issue description has been created.',
      });

      // Reload issue data
      const updatedIssue = await api.getIssue(owner, repo, parseInt(issueNumber));
      setIssue(updatedIssue);
    } catch (error) {
      toast({
        title: 'Generation Failed',
        description: 'Unable to generate checklist. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <main className="container px-4 py-8">
          <Skeleton className="h-32 rounded-lg mb-8" />
          <Skeleton className="h-96 rounded-lg" />
        </main>
      </div>
    );
  }

  if (!issue || !owner || !repo) {
    console.error('Missing data:', { issue: !!issue, owner: !!owner, repo: !!repo });
    return (
      <div className="min-h-screen bg-background">
        <main className="container px-4 py-8">
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">Issue not found</p>
          </Card>
        </main>
      </div>
    );
  }

  console.log('Rendering issue:', issue);

  const { passed = 0, failed = 0, pending = 0, total = 0 } = issue.checklist_summary || {};
  const completionPercentage = total > 0 ? Math.round((passed / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-background">
      <main className="container px-4 py-8 max-w-5xl">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link
            to={`/repo/${owner}/${repo}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to {owner}/{repo}
          </Link>
        </div>

        {/* Issue Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={issue.status === 'completed' ? 'default' : 'outline'}>
                  {issue.status}
                </Badge>
                <span className="text-sm text-muted-foreground">#{issue.issue_number}</span>
              </div>
              <h1 className="text-3xl font-bold mb-2">{issue.title}</h1>
            </div>

            <Button asChild variant="outline">
              <a
                href={issue.github_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                GitHub
              </a>
            </Button>
          </div>

          {/* Progress Summary */}
          <Card className="glass-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium">Checklist Progress</span>
                <span className="text-2xl font-bold text-primary">{completionPercentage}%</span>
              </div>

              <div className="w-full bg-muted rounded-full h-2 mb-4">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-success" />
                  <span>{passed} Passed</span>
                </div>
                {failed > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-destructive" />
                    <span>{failed} Failed</span>
                  </div>
                )}
                {pending > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-warning" />
                    <span>{pending} Pending</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Checklist */}
        <Card className="glass-card mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Quality Checklist</CardTitle>
              <div className="flex items-center gap-2">
                {/* Review Controls */}
                <div className="flex items-center gap-2 mr-4 border-r pr-4 border-border/50">
                  <input
                    type="number"
                    placeholder="PR #"
                    className="h-8 w-20 rounded border bg-background px-2 text-sm"
                    value={targetPrNumber}
                    onChange={(e) => setTargetPrNumber(e.target.value)}
                  />
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleRunReview}
                    disabled={reviewing || !targetPrNumber}
                  >
                    {reviewing ? <RefreshCw className="mr-2 h-3 w-3 animate-spin" /> : null}
                    Run Review
                  </Button>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerate}
                  disabled={regenerating}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${regenerating ? 'animate-spin' : ''}`} />
                  Generate Checklist
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href={`${issue.github_url}#issuecomment-new`} target="_blank" rel="noopener noreferrer">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Comment
                  </a>
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-3">
            {issue.checklist && issue.checklist.length > 0 ? (
              issue.checklist.map((item) => (
                <ChecklistItem key={item.id} item={item} />
              ))
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No checklist items generated yet.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Metadata */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Issue Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{new Date(issue.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Last Updated</span>
              <span>{new Date(issue.updated_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Total Items</span>
              <span>{total}</span>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default IssueDetail;
