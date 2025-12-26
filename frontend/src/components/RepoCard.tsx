import { Button } from '@/components/ui/button';
import { Github, TrendingUp, ExternalLink } from 'lucide-react';
import type { RepoSummary } from '@/types/api';
import { formatDistanceToNow } from 'date-fns';

interface RepoCardProps {
    repo: RepoSummary;
    onClick: () => void;
}

export const RepoCard = ({ repo, onClick }: RepoCardProps) => {
    const lastActivityText = repo.last_activity
        ? formatDistanceToNow(new Date(repo.last_activity), { addSuffix: true })
        : 'No activity';

    return (
        <div
            onClick={onClick}
            className="glass-card rounded-xl p-6 cursor-pointer hover:border-primary/30 transition-all hover:shadow-sm"
        >
            <div className="flex flex-col gap-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                        <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Github className="h-5 w-5 text-primary" />
                        </div>
                        <div className="min-w-0">
                            <h3 className="font-semibold text-foreground truncate">
                                {repo.repo_full_name}
                            </h3>
                        </div>
                    </div>
                </div>

                {/* Health Score */}
                <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-primary">{repo.health_score}</span>
                        <span className="text-sm text-muted-foreground">Health Score</span>
                    </div>
                </div>

                {/* Stats */}
                <div className="text-sm text-muted-foreground">
                    {repo.pr_count} Pull Requests • {repo.issue_count} Issues • Last activity: {lastActivityText}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="gap-2"
                        onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://github.com/${repo.repo_full_name}`, '_blank');
                        }}
                    >
                        <ExternalLink className="h-3.5 w-3.5" />
                        View on GitHub
                    </Button>
                    {!repo.is_installed && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                // Navigate to GitHub app installation
                                window.open('https://github.com/apps/revflo/installations/new', '_blank');
                            }}
                        >
                            Install RevFlo
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
};
