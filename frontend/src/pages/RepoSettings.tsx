import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
// import { Button } from "@/components/ui/button"; // Assuming shadcn or similar exists or standard HTML
// Assuming basic UI for now as I don't know the component library details fully
// The file list showed components/ui, so likely shadcn/radix.

export default function RepoSettings() {
    const { owner, repo } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleDelete = async () => {
        if (!confirm("Are you sure you want to remove this repository from RevFlo?")) return;

        setLoading(true);
        try {
            // API call to remove repo from managed_repos
            // This likely needs a backend endpoint to 'uninstall' or just update user managed_repos
            const res = await fetch(`/api/repos/${owner}/${repo}`, { method: "DELETE" });
            if (res.ok) {
                navigate("/dashboard");
            } else {
                alert("Failed to delete");
            }
        } catch (e) {
            console.error(e);
            alert("Error deleting repo");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Repository Settings</h1>
            <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                <h2 className="text-xl font-semibold mb-4 text-red-600">Danger Zone</h2>
                <p className="mb-4 text-gray-600">
                    Removing this repository will stop all monitoring and delete associated health data from RevFlo.
                    It will not affect the repository on GitHub.
                </p>
                <button
                    onClick={handleDelete}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                >
                    {loading ? "Removing..." : "Remove Repository"}
                </button>
            </div>
        </div>
    );
}
