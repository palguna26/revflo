import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ThemeToggle';
import { FeatureCard } from '@/components/FeatureCard';
import {
  Workflow,
  Github,
  CheckCircle2,
  GitPullRequest,
  TrendingUp,
  Shield,
  Sparkles,
  ArrowRight
} from 'lucide-react';
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

  const features = [
    {
      icon: CheckCircle2,
      title: 'Smart Checklists',
      description: 'AI-generated quality checklists tailored to each issue, ensuring comprehensive coverage and consistency.',
    },
    {
      icon: GitPullRequest,
      title: 'PR Validation',
      description: 'Automated PR validation against issue checklists, catching gaps before merge.',
    },
    {
      icon: TrendingUp,
      title: 'Health Metrics',
      description: 'Repository health scoring and analytics to track code quality trends over time.',
    },
    {
      icon: Shield,
      title: 'Security Analysis',
      description: 'Continuous security scanning and vulnerability detection to protect your codebase.',
    },
    {
      icon: Sparkles,
      title: 'Test Suggestions',
      description: 'Intelligent test recommendations with code snippets to improve coverage.',
    },
    {
      icon: Github,
      title: 'GitHub Integration',
      description: 'Seamless integration with GitHub repositories and workflows.',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2 font-semibold">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Workflow className="h-5 w-5" />
            </div>
            <span>RevFlo</span>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button asChild size="sm">
              <a href={`${API_BASE}/auth/github/login`}>Sign in</a>
            </Button>
          </div>
        </div>
      </header>

      <main className="container max-w-6xl mx-auto px-4">
        {/* Hero Section */}
        <section className="py-20 md:py-28 text-center">
          <div className="space-y-6 max-w-3xl mx-auto">
            <p className="text-sm uppercase tracking-wider text-primary font-medium">
              Enterprise Code Review
            </p>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              Streamline your code review workflow
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground leading-relaxed">
              Automate PR reviews with AI-powered checklists. Enforce standards, detect security risks, and ship with confidence.
            </p>
            <div className="flex items-center justify-center gap-4 flex-col sm:flex-row pt-4">
              <Button asChild size="lg" className="gap-2">
                <a href={`${API_BASE}/auth/github/login`}>
                  Get started <ArrowRight className="h-4 w-4" />
                </a>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="/dashboard">View demo</a>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-20 border-t">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <FeatureCard
                key={feature.title}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
              />
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20">
          <div className="glass-card rounded-2xl p-12 text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
            <p className="text-muted-foreground mb-8">
              Join teams using RevFlo to improve code quality and ship faster.
            </p>
            <Button asChild size="lg" className="gap-2">
              <a href={`${API_BASE}/auth/github/login`}>
                <Github className="h-5 w-5" />
                Sign in with GitHub
              </a>
            </Button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t bg-muted/20">
        <div className="container px-4 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} RevFlo. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
