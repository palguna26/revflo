import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Github, Check, Terminal, Shield, Zap, GitPullRequest } from 'lucide-react';
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
    <div className="min-h-screen bg-background text-foreground selection:bg-primary/20">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Terminal className="h-4 w-4" />
            </div>
            RevFlo
          </div>
          <Button asChild size="sm" variant="outline">
            <a href={`${API_BASE}/auth/github/login`}>
              <Github className="mr-2 h-4 w-4" />
              Sign in
            </a>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="container px-4 py-24 md:py-32 flex flex-col items-center text-center">
        <Badge variant="secondary" className="mb-6 px-4 py-1.5 text-sm font-normal rounded-full">
          v2.0 Now Available: Enterprise-Grade Security
        </Badge>
        <h1 className="text-4xl md:text-6xl font-bold tracking-tighter max-w-3xl mb-6">
          Code Quality Assurance for <span className="text-primary">Engineering Teams</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mb-10 leading-relaxed">
          Automate PR reviews with AI-powered checklists. Enforce standards, detect security risks, and ship with confidence.
        </p>
        <div className="flex items-center gap-4">
          <Button asChild size="lg" className="h-11 px-8">
            <a href={`${API_BASE}/auth/github/login`}>
              Start for free
            </a>
          </Button>
          <Button asChild size="lg" variant="secondary" className="h-11 px-8">
            <a href={`${API_BASE}/auth/github/demo-login`}>
              View Live Demo
            </a>
          </Button>
        </div>

        {/* Code Preview Mockup */}
        <div className="mt-20 w-full max-w-4xl mx-auto rounded-xl border bg-card shadow-sm overflow-hidden">
          <div className="border-b bg-muted/30 px-4 py-2 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/20" />
              <div className="w-3 h-3 rounded-full bg-amber-500/20" />
              <div className="w-3 h-3 rounded-full bg-green-500/20" />
            </div>
            <div className="text-xs text-muted-foreground font-mono ml-2">checklists.yml</div>
          </div>
          <div className="p-6 text-left font-mono text-sm leading-6 overflow-x-auto bg-card">
            <div className="text-muted-foreground"># Automated PR Policy</div>
            <div className="text-primary mt-2">security_check:</div>
            <div className="pl-4"><span className="text-blue-500">enabled:</span> true</div>
            <div className="pl-4"><span className="text-blue-500">severity:</span> critical</div>

            <div className="text-primary mt-4">checklist_rules:</div>
            <div className="pl-4">- <span className="text-green-600">"Verify API inputs are sanitized"</span></div>
            <div className="pl-4">- <span className="text-green-600">"Ensure database migrations are backward compatible"</span></div>
            <div className="pl-4">- <span className="text-green-600">"Check for hardcoded secrets in diff"</span></div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container px-4 py-24 border-t">
        <div className="grid md:grid-cols-3 gap-12">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <GitPullRequest className="h-5 w-5" />
            </div>
            <h3 className="text-xl font-semibold">Automated Reviews</h3>
            <p className="text-muted-foreground leading-relaxed">
              AI agents analyze every pull request against your custom requirements, blocking merges until standards are met.
            </p>
          </div>
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <Shield className="h-5 w-5" />
            </div>
            <h3 className="text-xl font-semibold">Security Guardrails</h3>
            <p className="text-muted-foreground leading-relaxed">
              Detect SQL injection, XSS, and broken access controls before they reach production. zero-config scanning.
            </p>
          </div>
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <Zap className="h-5 w-5" />
            </div>
            <h3 className="text-xl font-semibold">Instant Spec Generation</h3>
            <p className="text-muted-foreground leading-relaxed">
              Convert vague issue descriptions into rigid, atomic checklists automatically using quantum prompt engineering.
            </p>
          </div>
        </div>
      </section>

      {/* Trust */}
      <section className="py-24 bg-muted/30 border-t">
        <div className="container px-4 text-center">
          <h2 className="text-2xl font-bold mb-12">Trusted by engineering teams at</h2>
          <div className="flex flex-wrap justify-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
            {/* Simple text placeholders for logos to stick to "minimal" instruction */}
            <span className="text-xl font-bold">Acme Corp</span>
            <span className="text-xl font-bold">Globex</span>
            <span className="text-xl font-bold">Soylent</span>
            <span className="text-xl font-bold">Initech</span>
            <span className="text-xl font-bold">Umbrella</span>
          </div>
        </div>
      </section>
    </div>
  );
};


export default Landing;
