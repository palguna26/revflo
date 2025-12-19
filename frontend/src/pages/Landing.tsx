import { useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Github, Terminal, Shield, Zap, GitPullRequest, ArrowRight, Code2, Check, Lock, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { ThemeToggle } from '@/components/ThemeToggle';
import { motion, useScroll, useTransform } from 'framer-motion';

const rawBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
const API_BASE = rawBase && (rawBase.startsWith('http://') || rawBase.startsWith('https://')) ? rawBase : rawBase ? `http://${rawBase}` : '/api';

const Landing = () => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end end"] });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);

  useEffect(() => {
    const checkAuth = async () => {
      try { await api.getMe(); navigate('/dashboard'); } catch (error) { /**/ }
    };
    checkAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 overflow-hidden" ref={containerRef}>

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2 font-bold text-lg tracking-tight hover:opacity-80 transition-opacity cursor-pointer" onClick={() => navigate('/')}>
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <Terminal className="h-5 w-5" />
            </div>
            RevFlo
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button asChild size="sm" className="rounded-full font-medium" variant="default">
              <a href={`${API_BASE}/auth/github/login`}><Github className="mr-2 h-4 w-4" /> Sign In</a>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/10 rounded-full blur-[120px] opacity-50 pointer-events-none" />

        <div className="container relative z-10 px-4 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge variant="outline" className="mb-6 px-4 py-1.5 rounded-full border-primary/20 bg-primary/5 text-primary text-sm font-medium backdrop-blur-sm">
              <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse" />
              v2.0: AI-Native Code Audits
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-8xl font-black tracking-tighter mb-8 leading-[0.9] bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/50"
          >
            Quality Control <br /> for <span className="text-primary">Software Teams</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed font-light"
          >
            Ship faster with AI-powered PR reviews, automated compliance checklists, and architectural health audits.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button asChild size="lg" className="h-14 px-8 rounded-full text-lg shadow-xl shadow-primary/20 hover:scale-105 transition-transform">
              <a href={`${API_BASE}/auth/github/login`}>
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </a>
            </Button>
            <Button asChild size="lg" variant="outline" className="h-14 px-8 rounded-full text-lg border-2 hover:bg-secondary/50">
              <a href={`${API_BASE}/auth/github/demo-login`}>Live Demo</a>
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Bento Grid Features */}
      <section className="container px-4 py-24">
        <div className="grid md:grid-cols-3 gap-6 h-auto md:h-[500px]">

          {/* Feature 1: Compliance */}
          <motion.div whileHover={{ y: -5 }} className="group md:col-span-2 relative rounded-3xl border bg-card overflow-hidden shadow-2xl shadow-primary/5 flex flex-col justify-between p-10">
            <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:opacity-20 transition-opacity">
              <Shield className="w-64 h-64 text-primary" />
            </div>
            <div className="relative z-10 max-w-lg">
              <h3 className="text-3xl font-bold tracking-tight mb-4">Traffic Control for PRs</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Define strict merge policies. If the checklist isn't passed or security risks are found, the merge button is physically disabled. Enforce quality at the gate.
              </p>
              <ul className="mt-8 space-y-3">
                <li className="flex items-center gap-3"><Check className="text-green-500 h-5 w-5" /> <span>Mandatory Security Scans</span></li>
                <li className="flex items-center gap-3"><Check className="text-green-500 h-5 w-5" /> <span>Architecture Compliance</span></li>
                <li className="flex items-center gap-3"><Check className="text-green-500 h-5 w-5" /> <span>Automated Issue Specs</span></li>
              </ul>
            </div>
          </motion.div>

          {/* Feature 2: Audit */}
          <motion.div whileHover={{ y: -5 }} className="group relative rounded-3xl border bg-gradient-to-br from-primary/5 to-transparent overflow-hidden shadow-2xl shadow-primary/5 p-10 flex flex-col justify-center text-center">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
              <Zap className="h-8 w-8" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight mb-2">Instant Audits</h3>
            <p className="text-muted-foreground">
              One-click architectural analysis to find fragility "hotspots" in your codebase.
            </p>
          </motion.div>

          {/* Feature 3: Specs */}
          <motion.div whileHover={{ y: -5 }} className="group relative rounded-3xl border bg-card overflow-hidden shadow-2xl shadow-primary/5 p-10 flex flex-col">
            <div className="flex items-center gap-2 text-primary font-mono text-sm mb-6">
              <Terminal className="h-4 w-4" /> AI_Spec_Gen.exe
            </div>
            <h3 className="text-2xl font-bold tracking-tight mb-4">Vague Issue? No Problem.</h3>
            <p className="text-muted-foreground flex-1">
              RevFlo expands one-sentence issues into fully defined implementation plans with atomic checklists.
            </p>
          </motion.div>

          {/* Feature 4: Integration */}
          <motion.div whileHover={{ y: -5 }} className="md:col-span-2 group relative rounded-3xl border bg-card overflow-hidden shadow-2xl shadow-primary/5 p-10 flex items-center justify-between">
            <div className="max-w-md">
              <h3 className="text-2xl font-bold tracking-tight mb-2">Works with GitHub</h3>
              <p className="text-muted-foreground">
                Zero friction. Installs as a GitHub App and comments directly on your Pull Requests.
              </p>
            </div>
            <div className="hidden md:flex gap-4">
              <div className="p-4 rounded-xl bg-secondary"><Github className="h-8 w-8" /></div>
              <ArrowRight className="h-8 w-8 text-muted-foreground self-center" />
              <div className="p-4 rounded-xl bg-primary/20 text-primary"><Shield className="h-8 w-8" /></div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t bg-muted/20">
        <div className="container px-4 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2 font-bold tracking-tight opacity-50">
            <Terminal className="h-5 w-5" /> RevFlo
          </div>
          <p className="text-muted-foreground text-sm">© {new Date().getFullYear()} RevFlo Inc.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
