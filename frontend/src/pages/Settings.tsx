import { Header } from '@/components/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { User, RepoSummary } from '@/types/api';
import { Trash2, Check } from 'lucide-react';

export default function SettingsPage() {
    const [user, setUser] = useState<User | null>(null);
    const [repos, setRepos] = useState<RepoSummary[]>([]);
    const [removing, setRemoving] = useState<string | null>(null);
    const { toast } = useToast();

    useEffect(() => {
        const loadData = async () => {
            try {
                const [u, r] = await Promise.all([api.getMe(), api.getRepos()]);
                setUser(u);
                setRepos(r);
            } catch (e) {
                console.error(e);
            }
        };
        loadData();
    }, []);

    const handleSave = () => {
        toast({
            title: "Settings Saved",
            description: "Your preferences have been updated.",
        });
    };

    const handleRemoveRepo = async (fullName: string) => {
        setRemoving(fullName);
        try {
            await api.removeRepo(fullName);

            // Update local state
            setRepos(prev => prev.filter(r => r.repo_full_name !== fullName));

            toast({
                title: "Repository Removed",
                description: `${fullName} has been removed from your managed repos.`,
            });
        } catch (error) {
            console.error(error);
            toast({
                title: "Removal Failed",
                description: "Unable to remove repository. Please try again.",
                variant: "destructive",
            });
        } finally {
            setRemoving(null);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header user={user || undefined} repos={repos} />
            <main className="container max-w-4xl px-4 py-8">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
                <p className="text-muted-foreground mb-8">Manage your account settings and preferences.</p>

                <Tabs defaultValue="repos" className="w-full">
                    <TabsList className="mb-6">
                        <TabsTrigger value="repos">Repositories</TabsTrigger>
                        <TabsTrigger value="general">General</TabsTrigger>
                        <TabsTrigger value="notifications">Notifications</TabsTrigger>
                        <TabsTrigger value="billing">Billing</TabsTrigger>
                    </TabsList>

                    <TabsContent value="repos">
                        <Card>
                            <CardHeader>
                                <CardTitle>Managed Repositories</CardTitle>
                                <CardDescription>Add or remove repositories you want to track with RevFlo.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {repos.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <p className="mb-4">No repositories managed yet.</p>
                                        <Button onClick={() => window.location.href = '/add-repo'}>
                                            Add Your First Repository
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {repos.map((repo) => (
                                            <div
                                                key={repo.repo_full_name}
                                                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                                            >
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-3">
                                                        <h3 className="font-medium">{repo.repo_full_name}</h3>
                                                        <Badge variant={repo.is_installed ? "default" : "secondary"}>
                                                            {repo.is_installed ? <><Check className="h-3 w-3 mr-1" />Active</> : "Inactive"}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground mt-1">
                                                        Health Score: {repo.health_score} • {repo.pr_count} PRs • {repo.issue_count} Issues
                                                    </p>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleRemoveRepo(repo.repo_full_name)}
                                                    disabled={removing === repo.repo_full_name}
                                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                                >
                                                    <Trash2 className="h-4 w-4 mr-1" />
                                                    {removing === repo.repo_full_name ? "Removing..." : "Remove"}
                                                </Button>
                                            </div>
                                        ))}

                                        <Button
                                            variant="outline"
                                            className="w-full mt-4"
                                            onClick={() => window.location.href = '/add-repo'}
                                        >
                                            Add Repository
                                        </Button>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="general">
                        <Card>
                            <CardHeader>
                                <CardTitle>Profile Information</CardTitle>
                                <CardDescription>Update your account details and public profile.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Display Name</Label>
                                    <Input id="name" defaultValue={user?.name || ""} disabled />
                                    <p className="text-xs text-muted-foreground">Managed by GitHub</p>
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input id="email" defaultValue={user?.login || ""} disabled />
                                </div>
                                <Button onClick={handleSave}>Save Changes</Button>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="notifications">
                        <Card>
                            <CardHeader>
                                <CardTitle>Notifications</CardTitle>
                                <CardDescription>Configure how you receive alerts.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <p className="text-muted-foreground text-sm">Email notifications are currently disabled for this plan.</p>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="billing">
                        <Card>
                            <CardHeader>
                                <CardTitle>Billing</CardTitle>
                                <CardDescription>Manage your subscription and payment methods.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
                                    <h3 className="font-semibold text-primary mb-1">Free Tier</h3>
                                    <p className="text-sm text-muted-foreground">You are currently on the free tier. Upgrade for unlimited repositories.</p>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
}
