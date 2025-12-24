import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TrendDataPoint {
    timestamp: string;
    overall_score: number;
    risk_level: string;
    categories: {
        maintainability: number;
        security: number;
        performance: number;
        code_quality: number;
        architecture: number;
        dependencies: number;
    };
    findings_count: {
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
}

interface TrendChartProps {
    data: TrendDataPoint[];
    metric: 'overall_score' | 'categories' | 'findings';
    title: string;
}

export function TrendChart({ data, metric, title }: TrendChartProps) {
    // Transform data for chart
    const chartData = data.map(d => {
        const baseData = {
            date: format(new Date(d.timestamp), 'MMM dd'),
            fullDate: d.timestamp
        };

        if (metric === 'overall_score') {
            return { ...baseData, Score: d.overall_score };
        } else if (metric === 'categories') {
            return {
                ...baseData,
                Maintainability: d.categories.maintainability,
                Security: d.categories.security,
                'Code Quality': d.categories.code_quality
            };
        } else if (metric === 'findings') {
            return {
                ...baseData,
                Critical: d.findings_count.critical,
                High: d.findings_count.high,
                Medium: d.findings_count.medium
            };
        }
        return baseData;
    });

    return (
        <Card className="glass-card">
            <CardHeader>
                <CardTitle className="text-lg font-semibold">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted-foreground/20" />
                        <XAxis
                            dataKey="date"
                            className="text-xs text-muted-foreground"
                        />
                        <YAxis
                            className="text-xs text-muted-foreground"
                            domain={metric === 'overall_score' ? [0, 100] : undefined}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--background))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '0.5rem'
                            }}
                        />
                        <Legend />

                        {metric === 'overall_score' && (
                            <Line
                                type="monotone"
                                dataKey="Score"
                                stroke="hsl(var(--primary))"
                                strokeWidth={2}
                                dot={{ fill: 'hsl(var(--primary))', r: 4 }}
                            />
                        )}

                        {metric === 'categories' && (
                            <>
                                <Line
                                    type="monotone"
                                    dataKey="Maintainability"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="Security"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="Code Quality"
                                    stroke="#f59e0b"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                            </>
                        )}

                        {metric === 'findings' && (
                            <>
                                <Line
                                    type="monotone"
                                    dataKey="Critical"
                                    stroke="#dc2626"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="High"
                                    stroke="#f97316"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="Medium"
                                    stroke="#eab308"
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                />
                            </>
                        )}
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
