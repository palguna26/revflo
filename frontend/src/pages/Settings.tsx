import { Header } from '@/components/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { User, RepoSummary } from '@/types/api';

export default function SettingsPage() {
    const [user, setUser] = useState<User | null>(null);
    const [repos, setRepos] = useState<RepoSummary[]>([]);
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

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header user={user || undefined} repos={repos} />
            <main className="container max-w-4xl px-4 py-8">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
                <p className="text-muted-foreground mb-8">Manage your account settings and preferences.</p>

                <Tabs defaultValue="general" className="w-full">
                    <TabsList className="mb-6">
                        <TabsTrigger value="general">General</TabsTrigger>
                        <TabsTrigger value="notifications">Notifications</TabsTrigger>
                        <TabsTrigger value="billing">Billing</TabsTrigger>
                    </TabsList>

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
