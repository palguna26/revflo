/**
 * GitHub State Badge Component
 * 
 * Shows visual indicator for GitHub entity state (Open/Closed/Merged).
 * Part of Control Plane UI improvements.
 */
import { CheckCircle, XCircle, GitMerge } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface GitHubStateBadgeProps {
    githubState?: 'open' | 'closed';
    merged?: boolean;
    entityType: 'pr' | 'issue';
    className?: string;
}

export function GitHubStateBadge({
    githubState = 'open',
    merged = false,
    entityType,
    className = ''
}: GitHubStateBadgeProps) {

    // PR-specific: merged state
    if (entityType === 'pr' && githubState === 'closed' && merged) {
        return (
            <Badge className={`bg-purple-500/10 text-purple-600 border-purple-300 ${className}`}>
                <GitMerge className="h-3 w-3 mr-1" />
                Merged
            </Badge>
        );
    }

    // Closed state
    if (githubState === 'closed') {
        return (
            <Badge className={`bg-gray-500/10 text-gray-600 border-gray-300 ${className}`}>
                <XCircle className="h-3 w-3 mr-1" />
                Closed
            </Badge>
        );
    }

    // Open state
    return (
        <Badge className={`bg-green-500/10 text-green-600 border-green-300 ${className}`}>
            <CheckCircle className="h-3 w-3 mr-1" />
            Open
        </Badge>
    );
}
