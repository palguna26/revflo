import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Github, Check, Terminal, Shield, Zap, GitPullRequest, ArrowRight, Code2 } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';

const rawBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
const API_BASE =
  rawBase && (rawBase.startsWith('http://') || rawBase.startsWith('https://'))
    ? rawBase
    : rawBase
      ? `http://${rawBase}`
      : '/api';

const Landing = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await api.getMe();
        navigate('/dashboard');
      } catch (error) {
        // Not logged in
      }
    };
    checkAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary/20 overflow-hidden relative">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0 bg-dot-pattern opacity-50 pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-primary/20 blur-[120px] rounded-full opacity-30 pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-lg shadow-primary/25">
              <Terminal className="h-5 w-5" />
            </div>
            RevFlo
          </div>
          <Button asChild size="sm" variant="outline" className="rounded-full shadow-sm hover:shadow-md transition-all">
            <a href={`${API_BASE}/auth/github/login`}>
              <Github className="mr-2 h-4 w-4" />
              Sign in
            </a>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="container relative z-10 px-4 py-24 md:py-32 flex flex-col items-center text-center">
        <div className="animate-fade-up">
          <Badge variant="secondary" className="mb-8 px-4 py-1.5 text-sm font-medium rounded-full border bg-secondary/50 backdrop-blur-sm">
            <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse" />
            v2.0 Now Available: Enterprise-Grade Security
          </Badge>
        </div>

        <h1 className="animate-fade-up delay-100 text-5xl md:text-7xl font-bold tracking-tighter max-w-4xl mb-8 leading-[1.1]">
          Code Quality Assurance for <span className="text-primary text-glow">Engineering Teams</span>
        </h1>

        <p className="animate-fade-up delay-200 text-xl text-muted-foreground max-w-2xl mb-12 leading-relaxed">
          Automate PR reviews with AI-powered checklists. Enforce standards, detect security risks, and ship with confidence.
        </p>

        <div className="animate-fade-up delay-300 flex items-center gap-4 flex-col sm:flex-row">
          <Button asChild size="lg" className="h-12 px-8 rounded-full text-base shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all hover:scale-105 active:scale-95">
            <a href={`${API_BASE}/auth/github/login`}>
              Start for free <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
          <Button asChild size="lg" variant="secondary" className="h-12 px-8 rounded-full text-base border shadow-sm hover:bg-secondary/80 transition-all">
            <a href={`${API_BASE}/auth/github/demo-login`}>
              View Live Demo
            </a>
          </Button>
        </div>

        {/* Code Preview Mockup */}
        <div className="animate-fade-up delay-100 mt-24 w-full max-w-5xl mx-auto rounded-xl border bg-card/50 backdrop-blur-sm shadow-2xl shadow-primary/10 overflow-hidden ring-1 ring-white/10">
          <div className="border-b bg-muted/50 px-4 py-3 flex items-center justify-between">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/30" />
              <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/30" />
              <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/30" />
            </div>
            <div className="text-xs text-muted-foreground font-mono flex items-center gap-2">
              <Code2 className="h-3 w-3" />
              checklists.yml
            </div>
            <div className="w-12" />
          </div>
          <div className="p-8 text-left font-mono text-sm leading-7 overflow-x-auto bg-card/80">
            <div className="text-muted-foreground select-none"># Automated PR Policy</div>
            <div className="text-primary mt-4 font-bold">security_check:</div>
            <div className="pl-6 border-l-2 border-border ml-1.5"><span className="text-blue-500">enabled:</span> true</div>
            <div className="pl-6 border-l-2 border-border ml-1.5"><span className="text-blue-500">severity:</span> critical</div>

            <div className="text-primary mt-6 font-bold">checklist_rules:</div>
            <div className="pl-6 border-l-2 border-border ml-1.5 space-y-1">
              <div>- <span className="text-success">"Verify API inputs are sanitized"</span></div>
              <div>- <span className="text-success">"Ensure database migrations are backward compatible"</span></div>
              <div>- <span className="text-success">"Check for hardcoded secrets in diff"</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container px-4 py-32 border-t relative overflow-hidden">
        <div className="grid md:grid-cols-3 gap-12 relative z-10">
          <div className="group space-y-4 p-6 rounded-2xl transition-all hover:bg-muted/50 hover:border-border/50 border border-transparent">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <GitPullRequest className="h-6 w-6" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight">Automated Reviews</h3>
            <p className="text-muted-foreground leading-relaxed">
              AI agents analyze every pull request against your custom requirements, blocking merges until standards are met.
            </p>
          </div>
          <div className="group space-y-4 p-6 rounded-2xl transition-all hover:bg-muted/50 hover:border-border/50 border border-transparent">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <Shield className="h-6 w-6" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight">Security Guardrails</h3>
            <p className="text-muted-foreground leading-relaxed">
              Detect SQL injection, XSS, and broken access controls before they reach production with zero-config scanning.
            </p>
          </div>
          <div className="group space-y-4 p-6 rounded-2xl transition-all hover:bg-muted/50 hover:border-border/50 border border-transparent">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <Zap className="h-6 w-6" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight">Instant Spec Generation</h3>
            <p className="text-muted-foreground leading-relaxed">
              Convert vague issue descriptions into rigid, atomic checklists automatically using quantum prompt engineering.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t bg-muted/20">
        <div className="container px-4 text-center text-muted-foreground text-sm">
          <p>© {new Date().getFullYear()} RevFlo Inc. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
