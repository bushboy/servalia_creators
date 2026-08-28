import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { getRuntimeConfig, runtimeOrVite } from '@/lib/runtimeConfig';

// Create a public API instance without auth headers for the interest form
const API_BASE_URL =
  runtimeOrVite(
    getRuntimeConfig().apiBaseUrl,
    import.meta.env.VITE_API_BASE_URL
  ) || '';

const publicApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function InterestFormPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    organization: '',
    role: '',
    message: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    
    try {
      await publicApi.post('/interest', formData);
      setIsSubmitting(false);
      setIsSubmitted(true);
      toast.success('Thank you for your interest! We\'ll be in touch soon.');
      setFormData({
        name: '',
        email: '',
        organization: '',
        role: '',
        message: ''
      });
    } catch (error) {
      setIsSubmitting(false);
      toast.error('Failed to submit your information. Please try again.');
      console.error('Interest form submission error:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-background">
        <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <img src="/creator_trust.png" alt="CreatorTrust" className="h-6 w-6 object-contain" />
              </div>
              <span className="font-bold text-lg">CreatorTrust</span>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-20">
          <div className="mx-auto max-w-md text-center space-y-6">
            <div className="flex justify-center">
              <div className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-10 w-10 text-green-600" />
              </div>
            </div>
            <h1 className="text-3xl font-bold">Thank you for your interest!</h1>
            <p className="text-lg text-muted-foreground">
              We've received your information and will be in touch soon to discuss how CreatorTrust can help with your publishing workflow.
            </p>
            <Button onClick={() => navigate('/')} size="lg">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to home
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <img src="/creator_trust.png" alt="CreatorTrust" className="h-6 w-6 object-contain" />
              </div>
              <span className="font-bold text-lg">CreatorTrust</span>
            </div>
            <Button variant="ghost" onClick={() => navigate('/')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-20">
        <div className="mx-auto max-w-2xl">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold mb-4">Get in touch</h1>
            <p className="text-lg text-muted-foreground">
              Interested in learning more about CreatorTrust? Leave your details and we'll reach out to discuss how we can help streamline your publishing workflow.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium">
                  Name <span className="text-destructive">*</span>
                </label>
                <Input
                  id="name"
                  name="name"
                  placeholder="Your name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email <span className="text-destructive">*</span>
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label htmlFor="organization" className="text-sm font-medium">
                  Organization
                </label>
                <Input
                  id="organization"
                  name="organization"
                  placeholder="Your organization or company"
                  value={formData.organization}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="role" className="text-sm font-medium">
                  Role
                </label>
                <Input
                  id="role"
                  name="role"
                  placeholder="Author, Publisher, etc."
                  value={formData.role}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="message" className="text-sm font-medium">
                Message
              </label>
              <textarea
                id="message"
                name="message"
                placeholder="Tell us about your publishing needs or any questions you have..."
                value={formData.message}
                onChange={handleChange}
                disabled={isSubmitting}
                rows={5}
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit'
              )}
            </Button>
          </form>

          <div className="mt-8 text-center text-sm text-muted-foreground">
            <p>We respect your privacy and will only use your information to respond to your inquiry.</p>
          </div>
        </div>
      </div>
    </div>
  );
}