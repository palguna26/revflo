import { useEffect, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import type { User, RepoSummary } from '@/types/api';

export interface DashboardContextType {
    user: User | null;
    repos: RepoSummary[];
    loading: boolean;
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
    setRepos: React.Dispatch<React.SetStateAction<RepoSummary[]>>;
}

export const DashboardLayout = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState<User | null>(null);
    const [repos, setRepos] = useState<RepoSummary[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadGlobalData = async () => {
            try {
                const urlParams = new URLSearchParams(window.location.search);
                const token = urlParams.get('token');
                if (token) {
                    localStorage.setItem('qr_token', token);
                    window.history.replaceState({}, document.title, window.location.pathname);
                }

                // Fetch user and repos once for the layout
                const [userData, reposData] = await Promise.all([
                    api.getMe(),
                    api.getRepos()
                ]);

                setUser(userData);
                setRepos(reposData);
            } catch (error) {
                console.error('Failed to load global data:', error);
                // If auth fails, redirect to home
                navigate('/');
            } finally {
                setLoading(false);
            }
        };

        loadGlobalData();
    }, [navigate]);

    if (loading) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <Header loading={true} />
                <main className="container max-w-7xl mx-auto px-4 py-8">
                    <Skeleton className="h-12 w-48 mb-6" />
                    <div className="space-y-4">
                        <Skeleton className="h-32 w-full" />
                        <Skeleton className="h-32 w-full" />
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header user={user || undefined} repos={repos} />
            <Outlet context={{ user, repos, loading, setUser, setRepos } satisfies DashboardContextType} />
        </div>
    );
};
