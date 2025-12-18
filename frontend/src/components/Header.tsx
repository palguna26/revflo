import { Link } from 'react-router-dom';
import { Github, Sparkles, LogOut, Command } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api, API_BASE } from '@/lib/api';
import { RepoSwitcher } from './RepoSwitcher';

interface HeaderProps {
  user?: { login: string; avatar_url: string; name?: string };
  repos?: Array<{ repo_full_name: string; owner: string; name: string }>;
  loading?: boolean;
}

export const Header = ({ user, repos, loading }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2 font-semibold">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Command className="h-5 w-5" />
            </div>
            <span className="hidden sm:inline-block">RevFlo</span>
          </Link>

          {user && repos && repos.length > 0 && (
            <div className="hidden md:block">
              <span className="text-muted-foreground mr-2">/</span>
              <RepoSwitcher repos={repos} />
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />

          {loading ? (
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
            </div>
          ) : user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8 border">
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
            <Button asChild size="sm" className="h-9 px-4">
              <a href={`${API_BASE}/auth/github/login`}>
                <Github className="mr-2 h-4 w-4" />
                Sign in
              </a>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};
