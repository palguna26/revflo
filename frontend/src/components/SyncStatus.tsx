/**
 * Sync Status Component
 * 
 * Shows sync confidence and last synced timestamp.
 * Part of Control Plane UI improvements.
 */
import { Clock, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Badge } from '@/components/ui/badge';

interface SyncStatusProps {
    lastSynced?: string;
    className?: string;
}

export function SyncStatus({ lastSynced, className = '' }: SyncStatusProps) {
    if (!lastSynced) {
        return (
            <div className={`flex items-center gap-2 text-muted-foreground text-sm ${className}`}>
                <HelpCircle className="h-3 w-3" />
                <span>Never synced</span>
            </div>
        );
    }

    const syncDate = new Date(lastSynced);
    const age = Date.now() - syncDate.getTime();

    // Confidence thresholds (match backend SyncGuard)
    const isFresh = age < 60 * 1000;        // < 1 minute
    const isStale = age < 10 * 60 * 1000;   // < 10 minutes

    const getConfidenceStyle = () => {
        if (isFresh) {
            return {
                icon: CheckCircle,
                color: 'text-green-600',
                label: 'fresh'
            };
        } else if (isStale) {
            return {
                icon: Clock,
                color: 'text-yellow-600',
                label: 'stale'
            };
        } else {
            return {
                icon: AlertTriangle,
                color: 'text-red-600',
                label: 'outdated'
            };
        }
    };

    const { icon: Icon, color, label } = getConfidenceStyle();

    return (
        <div className={`flex items-center gap-2 ${color} text-sm ${className}`}>
            <Icon className="h-3 w-3" />
            <span>
                Synced {formatDistanceToNow(syncDate, { addSuffix: true })}
            </span>
            {!isFresh && (
                <Badge variant="outline" className={`text-xs ${color}`}>
                    {label}
                </Badge>
            )}
        </div>
    );
}
