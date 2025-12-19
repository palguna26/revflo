import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ScanResult, RiskItem, AuditReport } from "@/types/api"; // Ensure AuditReport is imported if needed for types
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2, AlertTriangle, CheckCircle, XCircle, Shield, Zap, Activity } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const getSeverityColor = (severity: string) => {
    switch (severity) {
        case "critical": return "destructive";
        case "high": return "destructive";
        case "medium": return "warning"; // amber/orange
        case "low": return "secondary";
        default: return "outline";
    }
};

const getScoreColor = (score: string) => {
    switch (score) {
        case "high": return "text-green-500";
        case "medium": return "text-yellow-500";
        case "low": return "text-red-500";
        default: return "text-muted-foreground";
    }
};

export default function AuditResult() {
    const { owner, repo } = useParams<{ owner: string; repo: string }>();
    const navigate = useNavigate();
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [repoId, setRepoId] = useState<string | null>(null);

    // 1. Resolve owner/repo to ID
    useEffect(() => {
        api.getRepo(owner!, repo!).then((r) => {
            // @ts-ignore
            if ((r as any)._id) setRepoId((r as any)._id);
            else if ((r as any).id) setRepoId((r as any).id);
        });
    }, [owner, repo]);

    const { data: scan, isLoading, isError } = useQuery({
        queryKey: ["audit", repoId],
        queryFn: () => api.getLatestAudit(repoId!),
        enabled: !!repoId,
        retry: false
    });

    const triggerScan = useMutation({
        mutationFn: () => api.triggerAuditScan(repoId!),
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

    if (!repoId) return <div className="h-screen bg-background flex items-center justify-center"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
            <Header />
            <main className="container mx-auto max-w-7xl px-4 py-8 space-y-8">

                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Codebase Health Audit</h1>
                        <p className="text-muted-foreground mt-1">Deep architectural analysis & risk assessment.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {scan && (
                            <Badge variant="outline" className="font-mono">
                                Latest: {new Date(scan.started_at).toLocaleDateString()}
                            </Badge>
                        )}
                        <Button
                            onClick={() => triggerScan.mutate()}
                            disabled={triggerScan.isPending || (scan?.status === 'pending' || scan?.status === 'processing')}
                        >
                            {triggerScan.isPending || scan?.status === 'processing' ? (
                                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Scanning...</>
                            ) : (
                                <><Activity className="mr-2 h-4 w-4" /> Run New Scan</>
                            )}
                        </Button>
                    </div>
                </div>

                {/* Empty State / Error */}
                {isError && !scan && (
                    <Card className="border-dashed">
                        <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                            <Shield className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium">No Audit Found</h3>
                            <p className="text-muted-foreground mb-4 max-w-md">
                                We haven't analyzed this repository yet. Run a scan to generate insights.
                            </p>
                            <Button onClick={() => triggerScan.mutate()}>Start Initial Audit</Button>
                        </CardContent>
                    </Card>
                )}

                {/* Report Content */}
                {scan && scan.report && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* Executive Takeaway */}
                        <Card className="bg-primary/5 border-primary/20">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Zap className="h-5 w-5 text-primary" /> Executive Takeaway
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-lg font-medium leading-relaxed">
                                    {scan.report.executive_takeaway}
                                </p>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                                    <Stat label="Maintainability" val={scan.report.summary.maintainability} />
                                    <Stat label="Security" val={scan.report.summary.security} />
                                    <Stat label="Performance" val={scan.report.summary.performance} />
                                    <Stat label="Confidence" val={scan.report.summary.testing_confidence} />
                                </div>
                            </CardContent>
                        </Card>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                            {/* Top Risks */}
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold flex items-center gap-2">
                                    <AlertTriangle className="text-destructive h-6 w-6" /> Top Risks
                                </h2>
                                {scan.report.top_risks.map((risk, i) => (
                                    <Card key={i} className="hover:shadow-md transition-shadow">
                                        <CardHeader className="pb-2">
                                            <div className="flex justify-between items-start">
                                                <CardTitle className="text-base font-semibold">{risk.title}</CardTitle>
                                                <Badge variant={getSeverityColor(risk.severity) as any}>{risk.severity}</Badge>
                                            </div>
                                            <CardDescription className="line-clamp-2">{risk.why_it_matters}</CardDescription>
                                        </CardHeader>
                                        <CardContent className="text-sm space-y-3 pt-0">
                                            <div className="bg-muted p-2 rounded text-xs font-mono">
                                                Affected: {risk.affected_areas.join(", ")}
                                            </div>
                                            <p className="text-muted-foreground">
                                                <span className="font-semibold text-foreground">Fix:</span> {risk.recommended_action}
                                            </p>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {/* Roadmap & Fragility */}
                            <div className="space-y-8">

                                {/* Roadmap */}
                                <div>
                                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                                        <Activity className="text-blue-500 h-6 w-6" /> Roadmap
                                    </h2>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <Card className="border-l-4 border-l-destructive/50">
                                            <CardHeader><CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">Fix Now</CardTitle></CardHeader>
                                            <CardContent>
                                                <ul className="space-y-2">
                                                    {scan.report.roadmap.fix_now.map((item, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm">
                                                            <XCircle className="h-4 w-4 text-destructive mt-0.5" /> {item}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </CardContent>
                                        </Card>
                                        <Card className="border-l-4 border-l-orange-500/50">
                                            <CardHeader><CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">Fix Next</CardTitle></CardHeader>
                                            <CardContent>
                                                <ul className="space-y-2">
                                                    {scan.report.roadmap.fix_next.map((item, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm">
                                                            <Activity className="h-4 w-4 text-orange-500 mt-0.5" /> {item}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>

                                {/* Fragility Map */}
                                <div>
                                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                                        Fragility Map
                                    </h2>
                                    <Card>
                                        <CardContent className="p-6">
                                            <h4 className="font-semibold mb-2 text-sm text-destructive">High Risk Modules</h4>
                                            <div className="flex flex-wrap gap-2 mb-6">
                                                {scan.report.fragility_map.high_risk_modules.map((mod, i) => (
                                                    <Badge key={i} variant="outline" className="border-destructive/30 text-destructive bg-destructive/5">
                                                        {mod}
                                                    </Badge>
                                                ))}
                                            </div>

                                            <h4 className="font-semibold mb-2 text-sm text-yellow-500">Change Sensitive</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {scan.report.fragility_map.change_sensitive_areas.map((mod, i) => (
                                                    <Badge key={i} variant="outline" className="border-yellow-500/30 text-yellow-600 bg-yellow-500/5">
                                                        {mod}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>

                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

function Stat({ label, val }: { label: string; val: string }) {
    return (
        <div className="flex flex-col">
            <span className="text-xs text-muted-foreground uppercase tracking-wider">{label}</span>
            <span className={`text-xl font-bold capitalized ${getScoreColor(val)}`}>
                {val}
            </span>
        </div>
    );
}
