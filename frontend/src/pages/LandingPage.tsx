import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { 
  BookOpen, 
  Shield, 
  ArrowRight, 
  FileText, 
  CheckCircle, 
  Zap,
  Lock,
  Eye,
  Globe,
  Package,
  Settings,
  Play
} from 'lucide-react';

export function LandingPage() {
  const navigate = useNavigate();
  const { loginWithRedirect, authMode } = useAuth();

  const handleLogin = async () => {
    if (authMode === 'oidc') {
      await loginWithRedirect();
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <img src="/creator_trust.png" alt="CreatorTrust" className="h-6 w-6 object-contain" />
              </div>
              <span className="font-bold text-lg">CreatorTrust</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={() => navigate('/interest')} size="sm">
                Get in touch
              </Button>
              <Button onClick={handleLogin} size="sm">
                Log in
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl text-center space-y-8">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              Turn one manuscript into a governed publishing campaign.
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              CreatorTrust helps authors repurpose their writing into book descriptions, newsletters, launch content, and social posts — while preserving voice, rights, and approval control.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button size="lg" onClick={handleLogin} className="w-full sm:w-auto">
                Log in
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button size="lg" variant="outline" onClick={handleLogin} className="w-full sm:w-auto">
                <Play className="mr-2 h-4 w-4" />
                See how it works
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Built for independent authors and small publishing teams.
            </p>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center space-y-6">
            <h2 className="text-3xl font-bold">
              Publishing and promotion should not feel fragmented.
            </h2>
            <p className="text-lg text-muted-foreground">
              Most authors are expected to turn one book into content for many channels, but the process is messy. Generic AI tools can flatten the author's voice, while manual workflows take too long to keep up with launches and deadlines.
            </p>
            <p className="text-lg font-medium">
              CreatorTrust helps authors move faster without losing control.
            </p>
          </div>
        </div>
      </section>

      {/* What it does Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">
                Repurpose one manuscript into a complete content pack.
              </h2>
              <p className="text-lg text-muted-foreground">
                Upload a manuscript or excerpt, define the author's voice, and generate platform-ready content for publishing and marketing. CreatorTrust creates book descriptions, newsletters, launch posts, podcast pitches, and other assets from the same source material.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Generate content tailored to each platform</h3>
                  <p className="text-sm text-muted-foreground">Create optimized content for different marketing channels and publishing platforms.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Eye className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Keep your writing voice visible and editable</h3>
                  <p className="text-sm text-muted-foreground">Maintain your unique style across all generated content with full control over edits.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Link outputs back to source material</h3>
                  <p className="text-sm text-muted-foreground">Trace every piece of content back to its original source in your manuscript.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Zap className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Save time across publishing and promotion</h3>
                  <p className="text-sm text-muted-foreground">Streamline your workflow and reduce manual content creation time.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust and Control Section */}
      <section className="py-20 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">
                Keep human approval at the center.
              </h2>
              <p className="text-lg text-muted-foreground">
                CreatorTrust is designed for authors who want AI support without surrendering control. It flags privacy concerns, unsupported claims, and risky wording before anything is used publicly.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Review every asset before approval</h3>
                  <p className="text-sm text-muted-foreground">Nothing goes public without your explicit review and approval.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Settings className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">See what the system learned from your writing</h3>
                  <p className="text-sm text-muted-foreground">Understand how the AI interprets your voice and style.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Shield className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Catch privacy and rights issues early</h3>
                  <p className="text-sm text-muted-foreground">Get warnings about potential privacy concerns before publishing.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Lock className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Protect the integrity of your voice</h3>
                  <p className="text-sm text-muted-foreground">Maintain consistency and authenticity across all your content.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Publishing Workflow Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">
                Prepare for KDP and IngramSpark with less friction.
              </h2>
              <p className="text-lg text-muted-foreground">
                CreatorTrust helps authors prepare platform-ready materials for publishing workflows, including descriptions, metadata support, and launch assets. Instead of starting from scratch for each channel, the author works from one governed content source.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Globe className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Create retailer-ready descriptions</h3>
                  <p className="text-sm text-muted-foreground">Generate optimized book descriptions for major retailers.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Package className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Prepare launch materials from approved content</h3>
                  <p className="text-sm text-muted-foreground">Build launch campaigns from your approved content library.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Organize work by book and edition</h3>
                  <p className="text-sm text-muted-foreground">Keep all your content organized and accessible by project.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-6 border rounded-lg">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Keep publishing assets aligned across channels</h3>
                  <p className="text-sm text-muted-foreground">Ensure consistency across all your publishing platforms.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works Section */}
      <section className="py-20 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">
                From manuscript to launch in a simple flow.
              </h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  1
                </div>
                <p className="font-medium">Upload a manuscript or excerpt</p>
              </div>
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  2
                </div>
                <p className="font-medium">Define the author's voice and audience</p>
              </div>
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  3
                </div>
                <p className="font-medium">Generate publishing and marketing assets</p>
              </div>
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  4
                </div>
                <p className="font-medium">Review risks and edit drafts</p>
              </div>
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  5
                </div>
                <p className="font-medium">Approve what gets used publicly</p>
              </div>
              <div className="flex items-center space-x-4 p-6 border rounded-lg bg-background">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 font-bold">
                  6
                </div>
                <p className="font-medium">Export the final campaign pack</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center space-y-8">
            <h2 className="text-3xl font-bold">
              Build your next book launch with more speed and less guesswork.
            </h2>
            <p className="text-lg text-muted-foreground">
              CreatorTrust gives authors a governed AI workflow for turning writing into action. If you want consistency, control, and clarity across publishing and marketing, this is where it starts.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button size="lg" onClick={handleLogin} className="w-full sm:w-auto">
                Log in
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button size="lg" variant="outline" onClick={() => navigate('/interest')} className="w-full sm:w-auto">
                Get in touch
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2024 CreatorTrust. Built for independent authors and small publishing teams.</p>
          <div className="mt-2">
            <button 
              onClick={() => navigate('/interest')}
              className="text-primary hover:underline p-0 h-auto bg-transparent border-0 cursor-pointer"
            >
              Get in touch
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}