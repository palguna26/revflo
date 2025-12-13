import { useParams } from "react-router-dom";

export default function HealthAnalytics() {
    const { owner, repo } = useParams();

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Health Analytics: {owner}/{repo}</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-lg font-medium mb-4">Health Score Trend</h3>
                    <div className="h-64 bg-gray-50 flex items-center justify-center text-gray-400">
                        [Chart: Score vs Time]
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-lg font-medium mb-4">Issue Velocity</h3>
                    <div className="h-64 bg-gray-50 flex items-center justify-center text-gray-400">
                        [Chart: Opened vs Closed]
                    </div>
                </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium mb-4">Top Code Health Issues</h3>
                <div className="space-y-4">
                    <div className="p-4 border rounded bg-red-50 border-red-100">
                        <span className="font-bold text-red-700">Critical</span>
                        <span className="ml-2">Security vulnerability in package.json dependencies</span>
                    </div>
                    <div className="p-4 border rounded bg-yellow-50 border-yellow-100">
                        <span className="font-bold text-yellow-700">Warning</span>
                        <span className="ml-2">Low test coverage in core modules</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
