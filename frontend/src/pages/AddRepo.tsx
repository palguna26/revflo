import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input'; // Assuming you have an input component or use standard input
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Plus, Check, Lock, Globe, ArrowLeft } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import type { User, RepoSummary } from '@/types/api';

interface GithubRepo {
    id: number;
    name: string;
    full_name: string;
    private: boolean;
    description: string | null;
    html_url: string;
    updated_at: string;
}

const AddRepo = () => {
    const navigate = useNavigate();
    const { toast } = useToast();
    const [user, setUser] = useState<User | null>(null);
    const [managedRepos, setManagedRepos] = useState<string[]>([]);
    const [availableRepos, setAvailableRepos] = useState<GithubRepo[]>([]);
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState<string | null>(null);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const loadData = async () => {
            try {
                const [userData, reposData] = await Promise.all([
                    api.getMe(),
                    api.getAvailableRepos()
                ]);
                setUser(userData);
                setManagedRepos(userData.managed_repos || []);
                setAvailableRepos(reposData);
            } catch (error) {
                console.error('Failed to load repositories:', error);
                toast({
                    title: "Error",
                    description: "Failed to load repositories from GitHub.",
                    variant: "destructive"
                })
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const handleAddRepo = async (fullName: string) => {
        setAdding(fullName);
        try {
            await api.addRepo(fullName);

            // Update local state
            setManagedRepos(prev => [...prev, fullName]);

            toast({
                title: 'Repository Added',
                description: `${fullName} is now being tracked.`,
            });
        } catch (error) {
            console.error(error);
            toast({
                title: 'Failed to add repository',
                description: 'Please try again later.',
                variant: 'destructive',
            });
        } finally {
            setAdding(null);
        }
    };

    const filteredRepos = availableRepos.filter(repo =>
        repo.full_name.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-background">
                <Header loading={true} />
                <main className="container px-4 py-8 max-w-5xl">
                    <Skeleton className="h-12 w-1/3 mb-8" />
                    <div className="grid gap-4 md:grid-cols-2">
                        {[1, 2, 3, 4].map((i) => (
                            <Skeleton key={i} className="h-32 rounded-lg" />
                        ))}
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Header user={user || undefined} />

            <main className="container px-4 py-8 max-w-5xl">
                <div className="mb-6">
                    <Link
                        to="/dashboard"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Dashboard
                    </Link>
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Add Repositories</h1>
                        <p className="text-muted-foreground">Select repositories to track with RevFlo.</p>
                    </div>

                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search your repositories..."
                            className="w-full pl-9 pr-4 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    {filteredRepos.length > 0 ? (
                        filteredRepos.map((repo) => {
                            const isAdded = managedRepos.includes(repo.full_name);

                            return (
                                <Card key={repo.id} className="glass-card flex flex-col">
                                    <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                                        <div className="space-y-1 pr-4">
                                            <CardTitle className="text-base font-semibold truncate hover:underline">
                                                <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                                                    {repo.full_name}
                                                </a>
                                            </CardTitle>
                                            <CardDescription className="line-clamp-2 text-xs">
                                                {repo.description || "No description provided."}
                                            </CardDescription>
                                        </div>
                                        {repo.private ? (
                                            <Lock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                        ) : (
                                            <Globe className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                        )}
                                    </CardHeader>
                                    <CardContent className="mt-auto pt-4">
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs text-muted-foreground">
                                                Updated {new Date(repo.updated_at).toLocaleDateString()}
                                            </span>

                                            {isAdded ? (
                                                <Button variant="ghost" size="sm" className="bg-muted" disabled>
                                                    <Check className="mr-2 h-4 w-4" />
                                                    Added
                                                </Button>
                                            ) : (
                                                <Button
                                                    variant="default"
                                                    size="sm"
                                                    onClick={() => handleAddRepo(repo.full_name)}
                                                    disabled={adding === repo.full_name}
                                                >
                                                    {adding === repo.full_name ? (
                                                        <span className="animate-spin mr-2">⏳</span>
                                                    ) : (
                                                        <Plus className="mr-2 h-4 w-4" />
                                                    )}
                                                    Add Repo
                                                </Button>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })
                    ) : (
                        <div className="col-span-full text-center py-12 text-muted-foreground">
                            No repositories found matching "{search}".
                        </div>
                    )}
                </div>

            </main>
        </div>
    );
};

export default AddRepo;
