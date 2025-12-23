import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ScanResult, RiskItem, AuditReport, PRSummary } from "@/types/api";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
    Loader2, AlertTriangle, CheckCircle, XCircle, Shield, Zap, Activity,
    ArrowRight, BarChart3, Layers, GitCommit, AlertOctagon, TrendingUp, MessageSquare
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const getSeverityStyles = (severity: string) => {
    switch (severity) {
        case "critical": return { color: "text-destructive", bg: "bg-destructive/10", border: "border-destructive/20" };
        case "high": return { color: "text-orange-600", bg: "bg-orange-500/10", border: "border-orange-500/20" };
        case "medium": return { color: "text-yellow-600", bg: "bg-yellow-500/10", border: "border-yellow-500/20" };
        case "low": return { color: "text-blue-600", bg: "bg-blue-500/10", border: "border-blue-500/20" };
        default: return { color: "text-muted-foreground", bg: "bg-muted", border: "border-border" };
    }
};

const getScoreColor = (score: string) => {
    switch (score) {
        case "high": return "text-green-500";
        case "medium": return "text-yellow-500";
        case "low": return "text-destructive";
        default: return "text-muted-foreground";
    }
};

export default function AuditResult() {
    const { owner, repo } = useParams<{ owner: string; repo: string }>();
    const navigate = useNavigate();
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [repoId, setRepoId] = useState<string | null>(null);
    const [postingToPR, setPostingToPR] = useState<number | null>(null);

    useEffect(() => {
        api.getRepo(owner!, repo!).then((r) => {
            // @ts-ignore
            if ((r as any)._id) setRepoId((r as any)._id);
            else if ((r as any).id) setRepoId((r as any).id);
        });
    }, [owner, repo]);

    const { data: scan, isLoading, isError } = useQuery({
        queryKey: ["audit", owner, repo],
        queryFn: () => api.getRepoAudit(owner!, repo!),
        enabled: !!owner && !!repo,
        retry: false
    });

    // Fetch open PRs for posting audit
    const { data: openPRs = [] } = useQuery({
        queryKey: ["prs", owner, repo],
        queryFn: () => api.getPRs(owner!, repo!),
        enabled: !!owner && !!repo,
        retry: false
    });

    const triggerScan = useMutation({
        mutationFn: () => api.triggerRepoAudit(owner!, repo!),
        onSuccess: () => {
            toast({ title: "Scan Triggered", description: "Audit has started in the background." });
            queryClient.invalidateQueries({ queryKey: ["audit", repoId] });
        },
        onError: (error: any) => {
            toast({
                title: "Scan Failed",
                description: error.message || "Could not trigger scan. Rate limit?",
                variant: "destructive"
            });
        }
    });

    const handlePostToPR = async (prNumber: number) => {
        setPostingToPR(prNumber);
        try {
            const result = await api.postAuditToPR(owner!, repo!, prNumber, 'critical_high');
            toast({
                title: "Audit Posted!",
                description: `${result.posted_count} comments posted to PR #${prNumber}${result.warnings?.length ? ' (with warnings)' : ''}`,
            });
        } catch (error: any) {
            console.error('Failed to post audit to PR:', error);
            toast({
                title: "Failed to Post",
                description: error.message || 'Could not post audit findings to PR',
                variant: "destructive"
            });
        } finally {
            setPostingToPR(null);
        }
    };

    if (!repoId) return <div className="h-screen bg-background flex items-center justify-center"><Loader2 className="animate-spin text-primary h-8 w-8" /></div>;

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 pb-20">
            <Header />

            {/* Hero Section */}
            <div className="bg-muted/30 border-b">
                <div className="container mx-auto max-w-7xl px-4 py-12">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 text-primary font-medium tracking-tight">
                                <BarChart3 className="h-5 w-5" /> Codebase Health Audit
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-foreground">
                                {owner}/{repo}
                            </h1>
                            <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
                                Deep architectural analysis & algorithmic risk assessment.
                            </p>
                        </div>

                        <div className="flex items-center gap-3">
                            {scan && (
                                <div className="flex flex-col items-end mr-4">
                                    <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Last Analyzed</span>
                                    <span className="font-mono text-sm">{new Date(scan.started_at).toLocaleDateString()}</span>
                                </div>
                            )}
                            <Button
                                onClick={() => triggerScan.mutate()}
                                size="lg"
                                className="shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all active:scale-95"
                                disabled={triggerScan.isPending || (scan?.status === 'pending' || scan?.status === 'processing')}
                            >
                                {triggerScan.isPending || scan?.status === 'processing' ? (
                                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...</>
                                ) : (
                                    <><Activity className="mr-2 h-4 w-4" /> Run New Scan</>
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <main className="container mx-auto max-w-7xl px-4 py-10 space-y-12">

                {/* V2 Feature: PR Comment Integration */}
                {scan && scan.report && openPRs.length > 0 && (
                    <Card className="border-primary/20 bg-gradient-to-br from-primary/5 via-transparent to-transparent animate-in fade-in slide-in-from-top-4 duration-500">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <MessageSquare className="h-5 w-5 text-primary" />
                                <CardTitle>Post Audit to Pull Requests</CardTitle>
                            </div>
                            <CardDescription>
                                Share critical and high severity findings as comments on your open PRs (V2 Feature)
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {openPRs.map((pr: any) => (
                                    <div key={pr.pr_number} className="flex items-center justify-between p-4 border rounded-lg bg-background hover:bg-muted/50 transition-colors">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Badge variant="outline" className="font-mono text-xs">#{pr.pr_number}</Badge>
                                                <span className="font-medium truncate">{pr.title}</span>
                                            </div>
                                            <span className="text-sm text-muted-foreground">by {pr.author}</span>
                                        </div>
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            onClick={() => handlePostToPR(pr.pr_number)}
                                            disabled={postingToPR === pr.pr_number}
                                            className="ml-4 shrink-0"
                                        >
                                            {postingToPR === pr.pr_number ? (
                                                <><Loader2 className="mr-2 h-3 w-3 animate-spin" /> Posting...</>
                                            ) : (
                                                <><MessageSquare className="mr-2 h-3 w-3" /> Post Audit</>
                                            )}
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Empty State / Error */}
                {isError && !scan && (
                    <Card className="border-dashed bg-muted/30">
                        <CardContent className="flex flex-col items-center justify-center p-16 text-center animate-in fade-in zoom-in duration-500">
                            <div className="bg-background p-4 rounded-full border shadow-sm mb-6">
                                <Shield className="h-12 w-12 text-muted-foreground" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">No Audit Data Available</h3>
                            <p className="text-muted-foreground mb-8 max-w-md">
                                We haven't analyzed this repository yet. Start a comprehensive scan to generate architectural insights.
                            </p>
                            <Button onClick={() => triggerScan.mutate()} size="lg">Start Initial Audit</Button>
                        </CardContent>
                    </Card>
                )}

                {/* Report Content */}
                {scan && scan.report && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">

                        {/* Section: Executive Summary */}
                        <section className="space-y-6">
                            <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                                <Zap className="h-6 w-6 text-primary" /> Executive Summary
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

                                {/* Takeaway Card */}
                                <Card className="md:col-span-8 bg-gradient-to-br from-primary/5 via-transparent to-transparent border-primary/20 shadow-sm relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                                    <CardHeader>
                                        <CardTitle className="text-lg font-medium text-primary">Chief Architect's Takeaway</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-xl md:text-2xl font-medium leading-relaxed tracking-tight text-foreground/90">
                                            "{scan.report.executive_takeaway}"
                                        </p>
                                    </CardContent>
                                </Card>

                                {/* KPI Cards */}
                                <div className="md:col-span-4 grid grid-cols-2 gap-4">
                                    <MetricCard label="Maintainability" value={scan.report.summary.maintainability} />
                                    <MetricCard label="Security" value={scan.report.summary.security} />
                                    <MetricCard label="Performance" value={scan.report.summary.performance} />
                                    <MetricCard label="Confidence" value={scan.report.summary.testing_confidence} />
                                </div>
                            </div>
                        </section>

                        <Separator className="opacity-50" />

                        {/* Section: Top Risks */}
                        <section className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                                    <AlertOctagon className="h-6 w-6 text-destructive" /> Critical Risks
                                </h2>
                                <Badge variant="outline" className="font-mono text-xs">
                                    {scan.report.top_risks.length} Issues Identified
                                </Badge>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {scan.report.top_risks.map((risk, i) => (
                                    <RiskCard key={i} risk={risk} index={i} />
                                ))}
                            </div>
                        </section>

                        {/* Section: Fragility & Roadmap */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

                            {/* Fragility Map */}
                            <section className="space-y-6">
                                <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                                    <Layers className="h-6 w-6 text-blue-500" /> Fragility Heatmap
                                </h2>
                                <Card className="h-full overflow-hidden border-border/60 shadow-sm">
                                    <CardHeader className="bg-muted/30 pb-4 border-b">
                                        <CardDescription>Areas with high complexity churn intersection.</CardDescription>
                                    </CardHeader>
                                    <CardContent className="p-0">
                                        <div className="divide-y divide-border/60">
                                            <div className="p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h4 className="font-semibold text-sm text-destructive flex items-center gap-2">
                                                        <Activity className="h-4 w-4" /> High Risk Modules
                                                    </h4>
                                                    <span className="text-xs text-muted-foreground">Require Immediate Refactor</span>
                                                </div>
                                                <div className="flex flex-wrap gap-2">
                                                    {scan.report.fragility_map.high_risk_modules.length > 0 ? (
                                                        scan.report.fragility_map.high_risk_modules.map((mod, i) => (
                                                            <HeatmapBadge key={i} label={mod} severity="critical" />
                                                        ))
                                                    ) : (
                                                        <span className="text-sm text-muted-foreground italic">No high risk modules detected.</span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="p-6 bg-muted/10">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h4 className="font-semibold text-sm text-yellow-600 flex items-center gap-2">
                                                        <GitCommit className="h-4 w-4" /> Change Sensitive
                                                    </h4>
                                                    <span className="text-xs text-muted-foreground">Monitor closely during PRs</span>
                                                </div>
                                                <div className="flex flex-wrap gap-2">
                                                    {scan.report.fragility_map.change_sensitive_areas.length > 0 ? (
                                                        scan.report.fragility_map.change_sensitive_areas.map((mod, i) => (
                                                            <HeatmapBadge key={i} label={mod} severity="medium" />
                                                        ))
                                                    ) : (
                                                        <span className="text-sm text-muted-foreground italic">No sensitive areas detected.</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </section>

                            {/* Roadmap */}
                            <section className="space-y-6">
                                <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                                    <TrendingUp className="h-6 w-6 text-green-600" /> Remediation Roadmap
                                </h2>
                                <div className="space-y-4">
                                    <RoadmapGroup
                                        title="Fix Now"
                                        items={scan.report.roadmap.fix_now}
                                        type="critical"
                                        icon={<AlertTriangle className="h-4 w-4" />}
                                    />
                                    <RoadmapGroup
                                        title="Fix Next"
                                        items={scan.report.roadmap.fix_next}
                                        type="medium"
                                        icon={<ArrowRight className="h-4 w-4" />}
                                    />
                                </div>
                            </section>

                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

// --- Subtitles Components ---

function MetricCard({ label, value }: { label: string; value: string }) {
    const color = getScoreColor(value);
    return (
        <Card className="flex flex-col items-center justify-center p-4 shadow-none border-border/60 bg-card/50 hover:bg-card transition-colors">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">{label}</span>
            <span className={`text-2xl font-bold capitalize ${color}`}>{value}</span>
        </Card>
    );
}

function RiskCard({ risk, index }: { risk: RiskItem; index: number }) {
    const styles = getSeverityStyles(risk.severity);
    return (
        <Card className="group relative overflow-hidden transition-all hover:shadow-lg border-border/60">
            <div className={`absolute top-0 left-0 w-1 h-full ${styles.bg.replace('/10', '')}`} />
            <CardHeader className="pb-3 pt-5 px-5">
                <div className="flex justify-between items-start gap-4">
                    <h3 className="font-semibold text-lg leading-tight group-hover:text-primary transition-colors line-clamp-2">
                        {risk.title}
                    </h3>
                    <Badge variant="outline" className={`${styles.color} ${styles.bg} ${styles.border} uppercase text-[10px] tracking-wider`}>
                        {risk.severity}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="px-5 pb-5 space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                    {risk.why_it_matters}
                </p>

                <div className="pt-2 border-t border-border/40">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                        <span>Recommended Action</span>
                    </div>
                    <p className="text-sm font-medium text-foreground bg-muted/50 p-3 rounded-md border border-border/40">
                        {risk.recommended_action}
                    </p>
                </div>

                <div className="flex flex-wrap gap-1 pt-1">
                    {risk.affected_areas.slice(0, 3).map((area, i) => (
                        <span key={i} className="text-[10px] font-mono text-muted-foreground bg-secondary/50 px-1.5 py-0.5 rounded border border-border/50">
                            {area}
                        </span>
                    ))}
                    {risk.affected_areas.length > 3 && (
                        <span className="text-[10px] text-muted-foreground px-1 py-0.5">+ {risk.affected_areas.length - 3}</span>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

function HeatmapBadge({ label, severity }: { label: string; severity: 'critical' | 'medium' }) {
    const styles = severity === 'critical'
        ? "bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20"
        : "bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500/20 border-yellow-500/20";

    return (
        <Badge variant="outline" className={`${styles} transition-colors cursor-default py-1 px-3 text-sm`}>
            {label}
        </Badge>
    );
}

function RoadmapGroup({ title, items, type, icon }: { title: string; items: string[]; type: 'critical' | 'medium'; icon: any }) {
    const styles = type === 'critical'
        ? "border-l-destructive/50 bg-destructive/5"
        : "border-l-orange-500/50 bg-orange-500/5";

    const titleColor = type === 'critical' ? 'text-destructive' : 'text-orange-600';

    if (!items.length) return null;

    return (
        <Card className={`border-0 border-l-4 rounded-r-lg rounded-l-none shadow-sm ${styles}`}>
            <CardHeader className="py-4">
                <CardTitle className={`text-sm uppercase tracking-wide flex items-center gap-2 ${titleColor}`}>
                    {icon} {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="pb-4 pt-0">
                <ul className="space-y-3">
                    {items.map((item, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm group">
                            <span className={`mt-1.5 h-1.5 w-1.5 rounded-full ${type === 'critical' ? 'bg-destructive' : 'bg-orange-500'} group-hover:scale-150 transition-transform`} />
                            <span className="text-foreground/90 leading-relaxed font-medium">{item}</span>
                        </li>
                    ))}
                </ul>
            </CardContent>
        </Card>
    );
}
