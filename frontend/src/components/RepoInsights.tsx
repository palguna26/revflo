import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { RepoSummary } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, ShieldAlert, Layers, Box, Info } from 'lucide-react';

interface Finding {
    id: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    file_path: string;
    line: number;
    description: string;
    explanation?: string;
}

interface AuditCategories {
    security: number;
    performance: number;
    code_quality: number;
    architecture: number;
    maintainability: number;
    dependencies: number;
}

interface AuditResult {
    audit_id: string;
    repo_id: string;
    commit_sha: string;
    overall_score: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    engine_version: string;
    created_at: string;
    categories: AuditCategories;
    findings: Finding[];
}

export const RepoInsights = () => {
    const { owner, repo } = useParams<{ owner: string; repo: string }>();
    const [loading, setLoading] = useState(true);
    const [audit, setAudit] = useState<AuditResult | null>(null);
    const [isEmpty, setIsEmpty] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [repoDetails, setRepoDetails] = useState<RepoSummary | null>(null);

    useEffect(() => {
        loadData();
    }, [owner, repo]);

    const loadData = async () => {
        if (!owner || !repo) return;
        setLoading(true);
        setIsEmpty(false);

        try {
            const r = await api.getRepo(owner, repo);
            setRepoDetails(r);

            try {
                const auditData = await api.getRepoAudit(owner, repo);
                setAudit(auditData);
            } catch (err: any) {
                if (err.message?.includes('404') || err.message?.includes('No audit')) {
                    setIsEmpty(true);
                }
            }
        } catch (e) {
            console.error("Failed to load audit data", e);
        } finally {
            setLoading(false);
        }
    };

    const handleRunSnapshot = async () => {
        if (!owner || !repo) return;

        setScanning(true);
        try {
            await api.triggerRepoAudit(owner, repo);
            setTimeout(() => {
                loadData();
                setScanning(false);
            }, 3000);
        } catch (e) {
            console.error(e);
            setScanning(false);
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'low': return 'bg-green-500/10 text-green-500';
            case 'medium': return 'bg-yellow-500/10 text-yellow-500';
            case 'high': return 'bg-orange-500/10 text-orange-500';
            case 'critical': return 'bg-red-500/10 text-red-500';
            default: return 'bg-gray-500/10 text-gray-500';
        }
    };

    if (loading) return <Skeleton className="h-64 w-full" />;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between p-6 glass-card rounded-lg">
                <div>
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Info className="h-5 w-5 text-primary" />
                        System Health Snapshot
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        On-demand analysis of architectural and security risks.
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    {audit && audit.created_at && (
                        <span className="text-xs text-muted-foreground">
                            Last snapshot: {new Date(audit.created_at).toLocaleDateString()}
                        </span>
                    )}
                    <Button size="sm" onClick={handleRunSnapshot} disabled={scanning}>
                        {scanning ? 'Analyzing System...' : 'Run Analysis Snapshot'}
                    </Button>
                </div>
            </div>

            {isEmpty && !audit ? (
                <div className="text-center py-12 border rounded-lg border-dashed">
                    <p className="text-muted-foreground mb-4">No system insights available yet.</p>
                    <Button variant="secondary" onClick={handleRunSnapshot} disabled={scanning}>
                        Run First Analysis
                    </Button>
                </div>
            ) : (
                <>
                    {/* Score & Risk */}
                    <div className="grid gap-6 md:grid-cols-4">
                        <Card className="md:col-span-1">
                            <CardHeader className="pb-2"><CardTitle className="text-xs font-medium text-muted-foreground">Health Score</CardTitle></CardHeader>
                            <CardContent>
                                <div className="text-4xl font-bold">{audit?.overall_score}</div>
                                <Progress value={audit?.overall_score} className="h-2 mt-4" />
                            </CardContent>
                        </Card>
                        <Card className="md:col-span-3">
                            <CardHeader className="pb-2"><CardTitle className="text-xs font-medium text-muted-foreground">High Risk Areas</CardTitle></CardHeader>
                            <CardContent>
                                <div className="flex gap-4">
                                    <Badge className={getRiskColor(audit?.risk_level || 'low') + " text-lg px-4 py-2 capitalize"}>
                                        {audit?.risk_level} Risk
                                    </Badge>
                                    <div className="flex-1 grid grid-cols-3 gap-4">
                                        {(audit?.findings || [])
                                            .filter(f => f.severity === 'critical')
                                            .slice(0, 3)
                                            .map(f => (
                                                <div key={f.id} className="text-xs border p-2 rounded bg-red-500/5 border-red-500/20 truncate" title={f.description}>
                                                    {f.file_path ? f.file_path.split('/').pop() : 'Unknown file'}
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Detailed Breakdown */}
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader><CardTitle className="flex items-center gap-2"><Layers className="h-4 w-4" /> Architecture & Quality</CardTitle></CardHeader>
                            <CardContent className="space-y-4">
                                {Object.entries(audit?.categories || {}).map(([k, v]) => (
                                    <div key={k} className="flex justify-between text-sm">
                                        <span className="capitalize text-muted-foreground">{k.replace('_', ' ')}</span>
                                        <span className="font-medium">{v}/100</span>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-4 w-4" /> Active Findings</CardTitle></CardHeader>
                            <CardContent className="max-h-[300px] overflow-y-auto space-y-3">
                                {(audit?.findings || []).map(f => (
                                    <div key={f.id} className="p-3 border rounded-md text-sm">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Badge variant="outline" className={`text-[10px] uppercase ${f.severity === 'critical' ? 'text-red-500' : 'text-orange-500'}`}>
                                                {f.severity}
                                            </Badge>
                                            <span className="font-mono text-xs">{f.file_path}</span>
                                        </div>
                                        <p className="line-clamp-2 text-muted-foreground">{f.description}</p>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    );
};
