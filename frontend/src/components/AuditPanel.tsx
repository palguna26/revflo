import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
    AlertCircle,
    AlertTriangle,
    Info,
    ShieldAlert,
    FileCode,
    Bug,
    Trash2,
    BookOpen,
    Layers,
    ChevronDown,
    ChevronRight,
    Download,
    RefreshCw,
    TrendingUp,
    CheckCircle2,
} from 'lucide-react';
import { api } from '@/lib/api';

interface AuditPanelProps {
    repoFullName: string;
    healthScore: number;
}

interface AuditIssue {
    id: string;
    title: string;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    category: 'security' | 'code-quality' | 'anti-patterns' | 'dead-code' | 'documentation' | 'complexity';
    file_path: string;
    line_number?: number;
    description: string;
    suggestion?: string;
}

interface AuditData {
    total_issues: number;
    security_issues: number;
    code_quality_issues: number;
    lines_analyzed: number;
    issues: AuditIssue[];
    // Category scores (0-100)
    scores?: {
        overall?: number;
        security?: number;
        performance?: number;
        code_quality?: number;
        architecture?: number;
        maintainability?: number;
        testing_confidence?: number;
    };
    // AI-generated insights
    report?: {
        overview?: string;
        executive_takeaway?: string;
        fragility_map?: {
            high_risk_modules?: string[];
            change_sensitive_areas?: string[];
        };
        roadmap?: {
            fix_now?: string[];
            fix_next?: string[];
            defer?: string[];
        };
        security_reliability?: Array<{
            finding: string;
            severity: string;
            context: string;
        }>;
    };
}

const severityConfig = {
    critical: {
        icon: AlertCircle,
        color: 'text-destructive',
        bg: 'bg-destructive/10',
        border: 'border-destructive/30',
    },
    high: {
        icon: AlertTriangle,
        color: 'text-warning',
        bg: 'bg-warning/10',
        border: 'border-warning/30',
    },
    medium: {
        icon: AlertTriangle,
        color: 'text-amber-500',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
    },
    low: {
        icon: Info,
        color: 'text-muted-foreground',
        bg: 'bg-muted/10',
        border: 'border-muted/30',
    },
    info: {
        icon: Info,
        color: 'text-primary',
        bg: 'bg-primary/10',
        border: 'border-primary/30',
    },
};

const categoryConfig = {
    security: { icon: ShieldAlert, label: 'Security' },
    'code-quality': { icon: FileCode, label: 'Code Quality' },
    'anti-patterns': { icon: Bug, label: 'Anti-patterns' },
    'dead-code': { icon: Trash2, label: 'Dead Code' },
    documentation: { icon: BookOpen, label: 'Documentation' },
    complexity: { icon: Layers, label: 'Complexity' },
};

type TabFilter = 'all' | 'security' | 'code-quality' | 'anti-patterns' | 'dead-code' | 'documentation' | 'complexity';

// Helper function to map backend severity to frontend format
const mapSeverity = (severity: string | undefined): AuditIssue['severity'] => {
    const s = severity?.toLowerCase();
    if (['critical', 'high', 'medium', 'low', 'info'].includes(s || '')) {
        return s as AuditIssue['severity'];
    }
    return 'medium';
};

// Helper function to map backend category to frontend format
const mapCategory = (category: string | undefined): AuditIssue['category'] => {
    const categoryMap: Record<string, AuditIssue['category']> = {
        'security': 'security',
        'code-quality': 'code-quality',
        'quality': 'code-quality',
        'maintainability': 'code-quality',
        'anti-pattern': 'anti-patterns',
        'antipattern': 'anti-patterns',
        'anti-patterns': 'anti-patterns',
        'dead-code': 'dead-code',
        'deadcode': 'dead-code',
        'documentation': 'documentation',
        'docs': 'documentation',
        'complexity': 'complexity',
    };
    const lowerCategory = category?.toLowerCase().replace(/[_\s]/g, '-');
    return categoryMap[lowerCategory || ''] || 'code-quality';
};

// Transform backend ScanResult to frontend AuditData format
const transformScanToAuditData = (scan: any): AuditData => {
    const issues: AuditIssue[] = [];

    // Extract issues from scan.report.top_risks
    if (scan?.report?.top_risks && Array.isArray(scan.report.top_risks)) {
        scan.report.top_risks.forEach((risk: any, index: number) => {
            // Handle both V1 and V2 formats
            const title = risk.title || risk.rule_type || risk.description?.substring(0, 100) || 'Issue detected';
            const description = risk.description || risk.explanation || risk.why_it_matters || '';
            const suggestion = risk.recommended_action || risk.recommendation || risk.fix || '';

            issues.push({
                id: risk.id || `risk-${index}`,
                title,
                severity: mapSeverity(risk.severity),
                category: mapCategory(risk.category || risk.rule_type),
                file_path: risk.file_path || risk.affected_areas?.[0] || 'Unknown',
                line_number: risk.line_number,
                description,
                suggestion,
            });
        });
    }

    // Count issues by type
    const security_issues = issues.filter(i => i.category === 'security').length;
    const code_quality_issues = issues.filter(i => i.category === 'code-quality').length;

    // Extract scores from both categories and report.summary
    const scores = {
        overall: scan?.overall_score,
        security: scan?.categories?.security || scan?.report?.summary?.security,
        performance: scan?.categories?.performance || scan?.report?.summary?.performance,
        code_quality: scan?.categories?.code_quality || scan?.report?.summary?.code_quality,
        architecture: scan?.categories?.architecture || scan?.report?.summary?.architecture,
        maintainability: scan?.categories?.maintainability || scan?.report?.summary?.maintainability,
        testing_confidence: scan?.report?.summary?.testing_confidence,
    };

    // Extract AI-generated insights
    const report = scan?.report ? {
        overview: scan.report.summary?.overview,
        executive_takeaway: scan.report.executive_takeaway,
        fragility_map: scan.report.fragility_map,
        roadmap: scan.report.roadmap,
        security_reliability: scan.report.security_reliability,
    } : undefined;

    return {
        total_issues: issues.length,
        security_issues,
        code_quality_issues,
        lines_analyzed: scan?.lines_of_code || scan?.raw_metrics?.total_lines || 0,
        issues,
        scores,
        report,
    };
};

const IssueRow = ({ issue }: { issue: AuditIssue }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const severityInfo = severityConfig[issue.severity];
    const categoryInfo = categoryConfig[issue.category];
    const SeverityIcon = severityInfo.icon;
    const CategoryIcon = categoryInfo.icon;

    return (
        <div className={`rounded-lg border ${severityInfo.border} ${severityInfo.bg} overflow-hidden`}>
            <div
                className="p-4 cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                        {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        )}
                    </div>
                    <SeverityIcon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${severityInfo.color}`} />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3 mb-2">
                            <h4 className="font-medium text-foreground">{issue.title}</h4>
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <Badge variant="outline" className="text-xs capitalize">
                                    {issue.severity}
                                </Badge>
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                    <CategoryIcon className="h-3.5 w-3.5" />
                                    <span>{categoryInfo.label}</span>
                                </div>
                            </div>
                        </div>
                        <p className="text-sm text-muted-foreground font-mono">
                            {issue.file_path}
                            {issue.line_number && `:${issue.line_number}`}
                        </p>
                    </div>
                </div>
            </div>

            {isExpanded && (
                <div className="px-4 pb-4 pt-2 border-t border-border/50 space-y-3">
                    <div>
                        <p className="text-sm text-foreground mb-2">{issue.description}</p>
                    </div>
                    {issue.suggestion && (
                        <div className="rounded-md bg-primary/5 border border-primary/20 p-3">
                            <p className="text-xs font-medium text-primary mb-1">Suggested Fix</p>
                            <p className="text-sm text-foreground">{issue.suggestion}</p>
                        </div>
                    )}
                    <div className="flex items-center gap-2 pt-2">
                        <Button variant="outline" size="sm" className="gap-2">
                            <FileCode className="h-3.5 w-3.5" />
                            View in Code
                        </Button>
                        <Button variant="ghost" size="sm">
                            Ignore
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export const AuditPanel = ({ repoFullName, healthScore }: AuditPanelProps) => {
    const [auditData, setAuditData] = useState<AuditData | null>(null);
    const [loading, setLoading] = useState(true);
    const [scanning, setScanning] = useState(false);
    const [activeTab, setActiveTab] = useState<TabFilter>('all');
    const { toast } = useToast();

    const loadAuditData = async () => {
        try {
            setLoading(true);
            const [owner, repo] = repoFullName.split('/');
            const scanResult = await api.getRepoAudit(owner, repo);

            if (scanResult && scanResult.status === 'completed') {
                const transformedData = transformScanToAuditData(scanResult);
                setAuditData(transformedData);
            } else {
                // No scan yet or scan not completed - show empty state
                setAuditData({
                    total_issues: 0,
                    security_issues: 0,
                    code_quality_issues: 0,
                    lines_analyzed: 0,
                    issues: [],
                });
            }
        } catch (error) {
            console.error('Failed to load audit data:', error);
            setAuditData({
                total_issues: 0,
                security_issues: 0,
                code_quality_issues: 0,
                lines_analyzed: 0,
                issues: [],
            });
        } finally {
            setLoading(false);
        }
    };

    const handleTriggerScan = async () => {
        try {
            setScanning(true);
            const [owner, repo] = repoFullName.split('/');
            await api.triggerAuditScan(owner, repo);

            toast({
                title: 'Audit Scan Started',
                description: 'The repository audit is now running. This may take a few minutes.',
            });

            // Poll for completion (simple approach - check every 5 seconds for 2 minutes)
            let attempts = 0;
            const maxAttempts = 24; // 2 minutes total
            const pollInterval = setInterval(async () => {
                attempts++;
                const scanResult = await api.getRepoAudit(owner, repo);

                if (scanResult?.status === 'completed' || scanResult?.status === 'failed' || attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    setScanning(false);

                    if (scanResult?.status === 'completed') {
                        loadAuditData();
                        toast({
                            title: 'Audit Complete',
                            description: 'The repository audit has finished successfully.',
                        });
                    } else if (scanResult?.status === 'failed') {
                        toast({
                            title: 'Audit Failed',
                            description: 'The audit scan encountered an error. Please try again.',
                            variant: 'destructive',
                        });
                    }
                }
            }, 5000);
        } catch (error) {
            setScanning(false);
            toast({
                title: 'Failed to Start Audit',
                description: 'Unable to trigger audit scan. Please try again.',
                variant: 'destructive',
            });
        }
    };

    useEffect(() => {
        loadAuditData();
    }, [repoFullName]);

    if (loading) {
        return (
            <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-24 bg-muted/50 rounded-lg animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    if (!auditData) {
        return <div className="text-center py-12 text-muted-foreground">Failed to load audit data.</div>;
    }

    const criticalOrHighCount = auditData.issues.filter(
        (i) => i.severity === 'critical' || i.severity === 'high'
    ).length;

    // Count issues by category
    const categoryCounts: Record<string, number> = {
        all: auditData.total_issues,
        security: auditData.issues.filter((i) => i.category === 'security').length,
        'code-quality': auditData.issues.filter((i) => i.category === 'code-quality').length,
        'anti-patterns': auditData.issues.filter((i) => i.category === 'anti-patterns').length,
        'dead-code': auditData.issues.filter((i) => i.category === 'dead-code').length,
        documentation: auditData.issues.filter((i) => i.category === 'documentation').length,
        complexity: auditData.issues.filter((i) => i.category === 'complexity').length,
    };

    // Filter issues by active tab
    const filteredIssues =
        activeTab === 'all'
            ? auditData.issues
            : auditData.issues.filter((i) => i.category === activeTab);

    // Sort by severity
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
    const sortedIssues = [...filteredIssues].sort(
        (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
    );

    const formatNumber = (num: number) => num.toLocaleString();

    return (
        <div className="space-y-6">
            {/* Stats Header */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Issues</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{auditData.total_issues}</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Security Issues</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-destructive">{auditData.security_issues}</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Code Quality</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-warning">{auditData.code_quality_issues}</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Lines Analyzed</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-primary">{formatNumber(auditData.lines_analyzed)}</div>
                    </CardContent>
                </Card>
            </div>

            {/* Health Scores Section */}
            {auditData.scores && Object.values(auditData.scores).some(v => v !== undefined) && (
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-primary" />
                            Health Scores
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {auditData.scores.overall !== undefined && (
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">Overall Health</span>
                                    <span className="text-sm font-bold text-primary">{auditData.scores.overall}/100</span>
                                </div>
                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all"
                                        style={{ width: `${auditData.scores.overall}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {auditData.scores.security !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <ShieldAlert className="h-4 w-4 text-destructive" />
                                            Security
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.security}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-destructive transition-all"
                                            style={{ width: `${auditData.scores.security}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {auditData.scores.performance !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <AlertTriangle className="h-4 w-4 text-warning" />
                                            Performance
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.performance}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-warning transition-all"
                                            style={{ width: `${auditData.scores.performance}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {auditData.scores.code_quality !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <FileCode className="h-4 w-4 text-primary" />
                                            Code Quality
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.code_quality}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-primary transition-all"
                                            style={{ width: `${auditData.scores.code_quality}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {auditData.scores.architecture !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <Layers className="h-4 w-4 text-primary" />
                                            Architecture
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.architecture}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-primary transition-all"
                                            style={{ width: `${auditData.scores.architecture}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {auditData.scores.maintainability !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <FileCode className="h-4 w-4 text-success" />
                                            Maintainability
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.maintainability}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-success transition-all"
                                            style={{ width: `${auditData.scores.maintainability}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {auditData.scores.testing_confidence !== undefined && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium flex items-center gap-2">
                                            <CheckCircle2 className="h-4 w-4 text-success" />
                                            Testing Confidence
                                        </span>
                                        <span className="text-sm font-bold">{auditData.scores.testing_confidence}/100</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-success transition-all"
                                            style={{ width: `${auditData.scores.testing_confidence}%` }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Executive Summary */}
            {auditData.report?.overview && (
                <Card className="glass-card border-primary/20">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileCode className="h-5 w-5 text-primary" />
                            Executive Summary
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <p className="text-sm leading-relaxed text-foreground/90">
                            {auditData.report.overview}
                        </p>
                        {auditData.report.executive_takeaway && (
                            <div className="mt-4 p-3 rounded-lg bg-primary/10 border border-primary/20">
                                <p className="text-sm font-medium text-primary">
                                    💡 {auditData.report.executive_takeaway}
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Fragility Map */}
            {auditData.report?.fragility_map && (auditData.report.fragility_map.high_risk_modules?.length > 0 || auditData.report.fragility_map.change_sensitive_areas?.length > 0) && (
                <Card className="glass-card border-destructive/20">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-destructive" />
                            Fragility Map
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {auditData.report.fragility_map.high_risk_modules && auditData.report.fragility_map.high_risk_modules.length > 0 && (
                            <div>
                                <h4 className="text-sm font-semibold mb-2 text-destructive">High-Risk Modules</h4>
                                <div className="flex flex-wrap gap-2">
                                    {auditData.report.fragility_map.high_risk_modules.map((module, idx) => (
                                        <Badge key={idx} variant="destructive" className="font-mono text-xs">
                                            {module}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}
                        {auditData.report.fragility_map.change_sensitive_areas && auditData.report.fragility_map.change_sensitive_areas.length > 0 && (
                            <div>
                                <h4 className="text-sm font-semibold mb-2 text-warning">Change-Sensitive Areas</h4>
                                <div className="flex flex-wrap gap-2">
                                    {auditData.report.fragility_map.change_sensitive_areas.map((area, idx) => (
                                        <Badge key={idx} variant="outline" className="font-mono text-xs border-warning/30 text-warning">
                                            {area}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Security & Reliability Findings */}
            {auditData.report?.security_reliability && auditData.report.security_reliability.length > 0 && (
                <Card className="glass-card border-destructive/20">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ShieldAlert className="h-5 w-5 text-destructive" />
                            Security & Reliability
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {auditData.report.security_reliability.map((item, idx) => (
                            <div key={idx} className="p-3 rounded-lg border border-destructive/20 bg-destructive/5">
                                <div className="flex items-start gap-2 mb-2">
                                    <Badge variant="destructive" className="text-xs">
                                        {item.severity}
                                    </Badge>
                                    <p className="text-sm font-medium flex-1">{item.finding}</p>
                                </div>
                                <p className="text-xs text-muted-foreground ml-2">{item.context}</p>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}

            {/* Roadmap */}
            {auditData.report?.roadmap && (auditData.report.roadmap.fix_now?.length > 0 || auditData.report.roadmap.fix_next?.length > 0 || auditData.report.roadmap.defer?.length > 0) && (
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Layers className="h-5 w-5 text-primary" />
                            Remediation Roadmap
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {auditData.report.roadmap.fix_now && auditData.report.roadmap.fix_now.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="h-2 w-2 rounded-full bg-destructive" />
                                    <h4 className="text-sm font-semibold text-destructive">Fix Now (Critical)</h4>
                                </div>
                                <ul className="space-y-2 ml-4">
                                    {auditData.report.roadmap.fix_now.map((action, idx) => (
                                        <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                            <span className="text-destructive mt-1">•</span>
                                            <span>{action}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {auditData.report.roadmap.fix_next && auditData.report.roadmap.fix_next.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="h-2 w-2 rounded-full bg-warning" />
                                    <h4 className="text-sm font-semibold text-warning">Fix Next (High Priority)</h4>
                                </div>
                                <ul className="space-y-2 ml-4">
                                    {auditData.report.roadmap.fix_next.map((action, idx) => (
                                        <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                            <span className="text-warning mt-1">•</span>
                                            <span>{action}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {auditData.report.roadmap.defer && auditData.report.roadmap.defer.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                                    <h4 className="text-sm font-semibold text-muted-foreground">Consider Later</h4>
                                </div>
                                <ul className="space-y-2 ml-4">
                                    {auditData.report.roadmap.defer.map((action, idx) => (
                                        <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                                            <span className="mt-1">•</span>
                                            <span>{action}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Attention Banner */}
            {criticalOrHighCount > 0 && (
                <div className="glass-card rounded-lg p-4 border-destructive/30 bg-destructive/5">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                            <p className="text-sm text-foreground">
                                <span className="font-medium">{criticalOrHighCount}</span> critical or high severity{' '}
                                {criticalOrHighCount === 1 ? 'issue' : 'issues'} found. Review and address immediately.
                            </p>
                        </div>
                        <Button variant="outline" size="sm" className="gap-2 flex-shrink-0">
                            <Download className="h-3.5 w-3.5" />
                            Export Report
                        </Button>
                    </div>
                </div>
            )}

            {/* Issues Card */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">
                            Issues {auditData.total_issues > 0 && <span className="text-muted-foreground">({auditData.total_issues})</span>}
                        </CardTitle>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleTriggerScan}
                            disabled={scanning}
                            className="gap-2"
                        >
                            {scanning ? (
                                <>
                                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                                    Scanning...
                                </>
                            ) : (
                                <>
                                    <ShieldAlert className="h-3.5 w-3.5" />
                                    Run Audit
                                </>
                            )}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Tab Filters */}
                    <div className="flex flex-wrap gap-2 pb-4 border-b">
                        <Button
                            variant={activeTab === 'all' ? 'default' : 'ghost'}
                            size="sm"
                            onClick={() => setActiveTab('all')}
                        >
                            All ({categoryCounts.all})
                        </Button>
                        {(['security', 'code-quality', 'anti-patterns', 'dead-code', 'documentation', 'complexity'] as const).map(
                            (category) => {
                                const count = categoryCounts[category];
                                // Hide empty tabs except "All"
                                if (count === 0) return null;

                                return (
                                    <Button
                                        key={category}
                                        variant={activeTab === category ? 'default' : 'ghost'}
                                        size="sm"
                                        onClick={() => setActiveTab(category)}
                                    >
                                        {categoryConfig[category].label} ({count})
                                    </Button>
                                );
                            }
                        )}
                    </div>

                    {/* Issues List */}
                    {sortedIssues.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            {activeTab === 'all'
                                ? 'No issues found. Great work!'
                                : `No issues found in this category`}
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {sortedIssues.map((issue) => (
                                <IssueRow key={issue.id} issue={issue} />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};
