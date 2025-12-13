import { Link } from 'react-router-dom';
import { Github, Sparkles, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api } from '@/lib/api';
import { RepoSwitcher } from './RepoSwitcher';

interface HeaderProps {
  user?: { login: string; avatar_url: string; name?: string };
  repos?: Array<{ repo_full_name: string; owner: string; name: string }>;
  loading?: boolean;
}

export const Header = ({ user, repos, loading }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-lg">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2 transition-transform hover:scale-105">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold gradient-text">RevFlo</span>
          </Link>

          {user && repos && repos.length > 0 && (
            <RepoSwitcher repos={repos} />
          )}
        </div>

        <div className="flex items-center gap-4">
          {loading ? (
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-4 w-24 hidden sm:block" />
            </div>
          ) : user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full overflow-hidden">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.avatar_url} alt={user.login} />
                    <AvatarFallback>{user.login.slice(0, 2).toUpperCase()}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user.name || user.login}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      @{user.login}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={async () => {
                  try {
                    await api.logout();
                    // Force reload to clear state and redirect
                    window.location.href = '/';
                  } catch (error) {
                    console.error("Logout failed", error);
                  }
                }}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button asChild variant="default" className="btn-hero">
              <a href="/auth/github">
                <Github className="mr-2 h-4 w-4" />
                Sign in with GitHub
              </a>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};
