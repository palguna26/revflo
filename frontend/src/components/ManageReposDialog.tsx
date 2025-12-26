import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Settings2,
    Search,
    Github,
    ExternalLink,
    Trash2,
    Plus,
} from 'lucide-react';
import type { RepoSummary } from '@/types/api';

interface ManageReposDialogProps {
    repos: RepoSummary[];
    onAddRepo?: (repoFullName: string) => void;
    onRemoveRepo?: (repoFullName: string) => void;
}

export const ManageReposDialog = ({ repos, onAddRepo, onRemoveRepo }: ManageReposDialogProps) => {
    const [activeTab, setActiveTab] = useState<'connected' | 'add'>('connected');
    const [searchQuery, setSearchQuery] = useState('');

    // In a real implementation, this would come from an API
    // For now, we'll just show the repos we already have
    const connectedRepos = repos.filter((r) => r.is_installed);
    const availableRepos: RepoSummary[] = []; // Would come from GitHub API

    const filteredConnected = connectedRepos.filter((repo) =>
        repo.repo_full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredAvailable = availableRepos.filter((repo) =>
        repo.repo_full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <Settings2 className="h-4 w-4" />
                    Manage Repositories
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle>Manage Repositories</DialogTitle>
                    <DialogDescription>
                        Add or remove repositories from RevFlo. Only repositories where the RevFlo GitHub App is installed will appear here.
                    </DialogDescription>
                </DialogHeader>

                {/* Tab Buttons */}
                <div className="flex gap-2 border-b">
                    <Button
                        variant={activeTab === 'connected' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setActiveTab('connected')}
                        className="rounded-b-none"
                    >
                        Connected ({connectedRepos.length})
                    </Button>
                    <Button
                        variant={activeTab === 'add' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setActiveTab('add')}
                        className="rounded-b-none gap-1"
                    >
                        <Plus className="h-3.5 w-3.5" />
                        Add Repository
                    </Button>
                </div>

                {/* Search Input */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search repositories..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto min-h-[300px] -mx-6 px-6">
                    {activeTab === 'connected' ? (
                        <div className="space-y-2">
                            {filteredConnected.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    <p className="mb-4">No repositories connected yet.</p>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setActiveTab('add')}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Add Repository
                                    </Button>
                                </div>
                            ) : (
                                filteredConnected.map((repo) => (
                                    <div
                                        key={repo.repo_full_name}
                                        className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                                    >
                                        <div className="flex items-center gap-3 min-w-0">
                                            <Github className="h-5 w-5 text-primary flex-shrink-0" />
                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium truncate">{repo.repo_full_name}</span>
                                                    {repo.is_installed && (
                                                        <Badge variant="secondary" className="text-xs">
                                                            Active
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    {repo.pr_count} PRs • {repo.issue_count} Issues
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => window.open(`https://github.com/${repo.repo_full_name}`, '_blank')}
                                            >
                                                <ExternalLink className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onRemoveRepo?.(repo.repo_full_name)}
                                                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {availableRepos.length === 0 ? (
                                <div className="space-y-4">
                                    <div className="text-center py-8 text-muted-foreground">
                                        <p>All available repositories are already connected.</p>
                                    </div>
                                    <div className="glass-card rounded-lg p-4 border-primary/20">
                                        <h4 className="font-medium mb-2 flex items-center gap-2">
                                            <Github className="h-4 w-4" />
                                            Configure GitHub App
                                        </h4>
                                        <p className="text-sm text-muted-foreground mb-3">
                                            Install the RevFlo GitHub App on more repositories to add them here.
                                        </p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => window.open('https://github.com/apps/revflo/installations/new', '_blank')}
                                            className="gap-2 w-full"
                                        >
                                            <ExternalLink className="h-3.5 w-3.5" />
                                            Install on More Repos
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    {filteredAvailable.map((repo) => (
                                        <div
                                            key={repo.repo_full_name}
                                            className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                                        >
                                            <div className="flex items-center gap-3 min-w-0">
                                                <Github className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                                                <div className="min-w-0">
                                                    <span className="font-medium truncate block">{repo.repo_full_name}</span>
                                                    <p className="text-xs text-muted-foreground truncate">
                                                        Available to connect
                                                    </p>
                                                </div>
                                            </div>
                                            <Button
                                                variant="default"
                                                size="sm"
                                                onClick={() => onAddRepo?.(repo.repo_full_name)}
                                            >
                                                Add
                                            </Button>
                                        </div>
                                    ))}
                                    <div className="glass-card rounded-lg p-4 border-primary/20 mt-4">
                                        <h4 className="font-medium mb-2 flex items-center gap-2">
                                            <Github className="h-4 w-4" />
                                            Configure GitHub App
                                        </h4>
                                        <p className="text-sm text-muted-foreground mb-3">
                                            Install the RevFlo GitHub App on more repositories.
                                        </p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => window.open('https://github.com/apps/revflo/installations/new', '_blank')}
                                            className="gap-2 w-full"
                                        >
                                            <ExternalLink className="h-3.5 w-3.5" />
                                            Install on More Repos
                                        </Button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
};
