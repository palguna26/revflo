import { CheckCircle2, Circle, XCircle, Clock, Tag } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { ChecklistItem as ChecklistItemType } from '@/types/api';

interface ChecklistItemProps {
  item: ChecklistItemType;
}

const statusConfig = {
  passed: { icon: CheckCircle2, color: 'text-success', bgColor: 'bg-success/10' },
  failed: { icon: XCircle, color: 'text-destructive', bgColor: 'bg-destructive/10' },
  pending: { icon: Clock, color: 'text-warning', bgColor: 'bg-warning/10' },
  skipped: { icon: Circle, color: 'text-muted-foreground', bgColor: 'bg-muted/10' },
};

export const ChecklistItem = ({ item }: ChecklistItemProps) => {
  const status = statusConfig[item.status];
  const StatusIcon = status.icon;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${status.bgColor} border-border/50`}>
      <StatusIcon className={`h-5 w-5 ${status.color} mt-0.5 flex-shrink-0`} />

      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground mb-1">{item.text}</p>

        {item.latest_validation && (
          <div className="mt-2 mb-2 text-sm text-foreground/80 bg-background/50 p-2 rounded border border-border/10">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-xs uppercase tracking-wider text-muted-foreground">
                Verified in PR #{item.latest_validation.pr_number}
              </span>
            </div>
            {item.latest_validation.reasoning && (
              <p className="mb-1 italic">"{item.latest_validation.reasoning}"</p>
            )}
            {item.latest_validation.evidence && (
              <p className="font-mono text-xs text-muted-foreground truncate" title={item.latest_validation.evidence}>
                Ref: {item.latest_validation.evidence}
              </p>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 flex-wrap">
          {item.required && (
            <Badge variant="outline" className="text-xs">
              Required
            </Badge>
          )}

          {item.linked_tests.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Tag className="h-3 w-3" />
              <span>{item.linked_tests.length} test{item.linked_tests.length !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
