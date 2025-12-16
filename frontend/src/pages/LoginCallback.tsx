import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const LoginCallback = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showSlowMessage, setShowSlowMessage] = useState(false);

  useEffect(() => {
    const handleAuth = async () => {
      // Show "server waking up" message after 3 seconds
      const timer = setTimeout(() => setShowSlowMessage(true), 3000);

      try {
        // Extract and save token if present
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        if (token) {
          localStorage.setItem('qr_token', token);
        }

        // Fetch user profile to verify authentication
        await api.getMe();

        toast({
          title: 'Success!',
          description: 'Successfully signed in with GitHub.',
        });

        navigate('/dashboard');
      } catch (error) {
        console.error("Login callback failed:", error);
        toast({
          title: 'Authentication Failed',
          description: 'Unable to sign in. Please try again.',
          variant: 'destructive',
        });

        navigate('/');
      } finally {
        clearTimeout(timer);
      }
    };

    handleAuth();
  }, [navigate, toast]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Authenticating...</h2>
        <p className="text-muted-foreground">Please wait while we sign you in.</p>
        {showSlowMessage && (
          <p className="text-sm text-yellow-600 mt-4 animate-in fade-in slide-in-from-bottom-2">
            Server might be waking up (Render Free Tier). <br />This could take up to a minute...
          </p>
        )}
      </div>
    </div>
  );
};

export default LoginCallback;
