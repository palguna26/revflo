import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Recommendation {
    id: string;
    type: 'optimization' | 'security' | 'style';
    message: string;
    repo: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
}

interface AIRecommendationsFeedProps {
    recommendations?: Recommendation[];
}

export const AIRecommendationsFeed = ({ recommendations = [] }: AIRecommendationsFeedProps) => {
    return (
        <Card className="glass-card h-full flex flex-col">
            <CardHeader className="pb-3 border-b border-white/5">
                <CardTitle className="flex items-center gap-2 text-base">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    AI Insights & Recommendations
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto pt-4 pr-1 custom-scrollbar">
                {recommendations.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-4 text-muted-foreground">
                        <CheckCircle className="h-8 w-8 mb-2 opacity-20" />
                        <p className="text-sm">No critical issues detected.</p>
                        <p className="text-xs opacity-50 mt-1">AI analysis will appear here after your first review.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {recommendations.map((rec) => (
                            <div key={rec.id} className="p-3 rounded-lg border border-white/10 bg-white/5 flex gap-3 hover:bg-white/10 transition-colors">
                                <div className="mt-1 flex-shrink-0">
                                    {rec.severity === 'high' || rec.severity === 'critical' ? (
                                        <AlertTriangle className="h-4 w-4 text-destructive" />
                                    ) : (
                                        <Lightbulb className="h-4 w-4 text-primary" />
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium leading-snug">{rec.message}</p>
                                    <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
                                        <span className={`px-1.5 py-0.5 rounded-full bg-background/50 border border-white/10 capitalize ${rec.type === 'security' ? 'text-destructive' : 'text-primary'
                                            }`}>
                                            {rec.type}
                                        </span>
                                        <span className="truncate max-w-[120px]" title={rec.repo}>{rec.repo}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
