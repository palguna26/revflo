import { Link } from 'react-router-dom';
import { GitPullRequest, TrendingUp } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface PRCardProps {
  prNumber: number;
  title: string;
  author: string;
  healthScore: number;
  repoOwner: string;
  repoName: string;
  validationStatus: 'pending' | 'validated' | 'needs_work';
}

const statusConfig = {
  pending: { color: 'bg-warning/10 text-warning border-warning/20', label: 'Pending' },
  validated: { color: 'bg-success/10 text-success border-success/20', label: 'Validated' },
  needs_work: { color: 'bg-destructive/10 text-destructive border-destructive/20', label: 'Needs Work' },
};

export const PRCard = ({ prNumber, title, author, healthScore, repoOwner, repoName, validationStatus, compact }: PRCardProps & { compact?: boolean }) => {
  const status = statusConfig[validationStatus] || statusConfig.pending;

  if (compact) {
    return (
      <Link to={`/repo/${repoOwner}/${repoName}/prs/${prNumber}`} className="block group">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <GitPullRequest className={`h-4 w-4 ${status.color.split(' ')[1] || 'text-muted-foreground'}`} />
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-medium truncate group-hover:text-primary transition-colors">{title}</span>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>#{prNumber}</span>
                <span>•</span>
                <span>{author}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px] h-5 px-1.5 font-normal">
              {status.label}
            </Badge>
            <div className="flex items-center gap-1 w-10 justify-end">
              <TrendingUp className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium">{healthScore}</span>
            </div>
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link to={`/repo/${repoOwner}/${repoName}/prs/${prNumber}`}>
      <Card className="h-full transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <GitPullRequest className="h-4 w-4 text-primary" />
                <span className="text-xs font-medium text-muted-foreground">#{prNumber}</span>
                <Badge className={status.color}>
                  {status.label}
                </Badge>
              </div>

              <h3 className="font-semibold text-foreground mb-2 truncate">
                {title}
              </h3>

              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span>by {author}</span>
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-primary" />
                <span className="text-2xl font-bold text-primary">{healthScore}</span>
              </div>
              <span className="text-xs text-muted-foreground">Health Score</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};
