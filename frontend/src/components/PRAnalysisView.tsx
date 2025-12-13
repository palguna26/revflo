import { AlertTriangle, CheckCircle, Info } from "lucide-react";

// Types matching backend PRDetail roughly
interface CodeHealthIssue {
    severity: "critical" | "high" | "medium" | "low";
    message: string;
    file_path: string;
    suggestion?: string;
}

interface SuggestedTest {
    name: string;
    snippet: string;
    reasoning?: string;
}

interface TestResult {
    name: string;
    status: "passed" | "failed" | "skipped";
}

interface PRDetail {
    health_score: number;
    validation_status: string;
    code_health: CodeHealthIssue[];
    suggested_tests: SuggestedTest[];
    test_results: TestResult[];
}

interface Props {
    data: PRDetail;
}

export default function PRAnalysisView({ data }: Props) {
    if (!data) return null;

    return (
        <div className="space-y-8">
            {/* Score Card */}
            <div className="flex items-center space-x-4 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className={`text-4xl font-bold ${data.health_score > 80 ? "text-green-500" : "text-yellow-500"}`}>
                    {data.health_score}
                </div>
                <div>
                    <h3 className="text-lg font-medium">Health Score</h3>
                    <p className="text-sm text-gray-500">Based on coverage, static analysis, and checklist adherence.</p>
                </div>
            </div>

            {/* Issues */}
            <div>
                <h3 className="text-lg font-bold mb-4 flex items-center">
                    <AlertTriangle className="mr-2 w-5 h-5 text-yellow-600" />
                    Code Health Issues
                </h3>
                {data.code_health.length === 0 ? (
                    <p className="text-gray-500 italic">No issues detected.</p>
                ) : (
                    <div className="space-y-3">
                        {data.code_health.map((issue, i) => (
                            <div key={i} className="p-4 bg-white rounded border border-gray-200 flex justify-between">
                                <div>
                                    <div className="flex items-center space-x-2">
                                        <span className={`uppercase text-xs font-bold px-2 py-0.5 rounded ${issue.severity === 'critical' ? 'bg-red-100 text-red-700' :
                                                issue.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                                                    'bg-blue-100 text-blue-700'
                                            }`}>
                                            {issue.severity}
                                        </span>
                                        <span className="font-mono text-sm text-gray-500">{issue.file_path}</span>
                                    </div>
                                    <p className="mt-1 text-gray-800">{issue.message}</p>
                                    {issue.suggestion && (
                                        <div className="mt-2 text-sm bg-gray-50 p-2 rounded font-mono text-gray-700">
                                            {issue.suggestion}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Suggested Tests */}
            <div>
                <h3 className="text-lg font-bold mb-4 flex items-center">
                    <CheckCircle className="mr-2 w-5 h-5 text-green-600" />
                    Suggested Tests
                </h3>
                {data.suggested_tests.length === 0 ? (
                    <p className="text-gray-500 italic">No new tests suggested.</p>
                ) : (
                    <div className="grid grid-cols-1 gap-4">
                        {data.suggested_tests.map((test, i) => (
                            <div key={i} className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="font-bold text-green-400">{test.name}</span>
                                </div>
                                <pre className="text-xs font-mono">{test.snippet}</pre>
                                {test.reasoning && (
                                    <p className="mt-2 text-xs text-slate-400 border-t border-slate-700 pt-2">
                                        {test.reasoning}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
