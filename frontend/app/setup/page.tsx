'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader2, Eye, EyeOff, Key, Globe, Bot, Phone, Mail, Database } from 'lucide-react';

interface EnvVar {
  key: string;
  label: string;
  description: string;
  required: boolean;
  icon: React.ReactNode;
  placeholder: string;
  value: string;
  status: 'pending' | 'validating' | 'valid' | 'invalid';
  error?: string;
}

const SETUP_STEPS = [
  { id: 'welcome', title: 'Welcome', description: 'Get started with AI Realtor' },
  { id: 'essential', title: 'Essential Keys', description: 'Required API keys' },
  { id: 'optional', title: 'Optional Keys', description: 'Enhanced features' },
  { id: 'complete', title: 'Complete', description: 'Ready to use' },
];

export default function SetupPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);

  const [envVars, setEnvVars] = useState<EnvVar[]>([
    {
      key: 'GOOGLE_PLACES_API_KEY',
      label: 'Google Places API',
      description: 'Required for address lookup and property validation',
      required: true,
      icon: <Globe className="w-5 h-5" />,
      placeholder: 'AIzaSy...',
      value: '',
      status: 'pending'
    },
    {
      key: 'RAPIDAPI_KEY',
      label: 'RapidAPI Key',
      description: 'Zillow enrichment and Skip Trace (get from rapidapi.com)',
      required: true,
      icon: <Key className="w-5 h-5" />,
      placeholder: '7f97645717msh...',
      value: '',
      status: 'pending'
    },
    {
      key: 'DOCUSEAL_API_KEY',
      label: 'DocuSeal API Key',
      description: 'E-signature integration for contracts',
      required: true,
      icon: <Database className="w-5 h-5" />,
      placeholder: 'jnTC1bKhVToZZFek...',
      value: '',
      status: 'pending'
    },
    {
      key: 'TELEGRAM_BOT_TOKEN',
      label: 'Telegram Bot Token',
      description: 'Chat with @BotFather on Telegram to get this',
      required: true,
      icon: <Bot className="w-5 h-5" />,
      placeholder: '123456789:ABCdef...',
      value: '',
      status: 'pending'
    },
    {
      key: 'ZHIPU_API_KEY',
      label: 'Zhipu AI API Key',
      description: 'AI provider for Nanobot (alternative to Claude)',
      required: true,
      icon: <Bot className="w-5 h-5" />,
      placeholder: 'becbf743529740ce...',
      value: '',
      status: 'pending'
    },
    {
      key: 'ANTHROPIC_API_KEY',
      label: 'Anthropic Claude API',
      description: 'AI recaps, contract analysis, and compliance (optional)',
      required: false,
      icon: <Bot className="w-5 h-5" />,
      placeholder: 'sk-ant-...',
      value: '',
      status: 'pending'
    },
    {
      key: 'VAPI_API_KEY',
      label: 'VAPI Phone Calls',
      description: 'AI-powered phone call automation (optional)',
      required: false,
      icon: <Phone className="w-5 h-5" />,
      placeholder: 'your_vapi_key',
      value: '',
      status: 'pending'
    },
    {
      key: 'ELEVENLABS_API_KEY',
      label: 'ElevenLabs Voice',
      description: 'Text-to-speech for phone calls (optional)',
      required: false,
      icon: <Phone className="w-5 h-5" />,
      placeholder: 'your_elevenlabs_key',
      value: '',
      status: 'pending'
    },
    {
      key: 'RESEND_API_KEY',
      label: 'Resend Email',
      description: 'Email notifications and reports (optional)',
      required: false,
      icon: <Mail className="w-5 h-5" />,
      placeholder: 're_...',
      value: '',
      status: 'pending'
    },
    {
      key: 'EXA_API_KEY',
      label: 'Exa AI Research',
      description: 'AI-powered property research (optional)',
      required: false,
      icon: <Globe className="w-5 h-5" />,
      placeholder: 'exa_...',
      value: '',
      status: 'pending'
    },
  ]);

  useEffect(() => {
    // Check if setup is already complete
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const response = await fetch('/api/setup/status');
      const data = await response.json();

      if (data.configured) {
        setSetupComplete(true);
        // Pre-fill existing values
        setEnvVars(prev => prev.map(envVar => ({
          ...envVar,
          value: data.values[envVar.key] || '',
          status: data.values[envVar.key] ? 'valid' : 'pending'
        })));
      }
    } catch (error) {
      console.error('Failed to check setup status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const validateApiKey = async (envVar: EnvVar): Promise<boolean> => {
    setEnvVars(prev => prev.map(ev =>
      ev.key === envVar.key ? { ...ev, status: 'validating' } : ev
    ));

    try {
      const response = await fetch('/api/setup/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: envVar.key,
          value: envVar.value
        })
      });

      const data = await response.json();
      const isValid = data.valid;

      setEnvVars(prev => prev.map(ev =>
        ev.key === envVar.key ? {
          ...ev,
          status: isValid ? 'valid' : 'invalid',
          error: data.error
        } : ev
      ));

      return isValid;
    } catch (error) {
      setEnvVars(prev => prev.map(ev =>
        ev.key === envVar.key ? {
          ...ev,
          status: 'invalid',
          error: 'Failed to validate'
        } : ev
      ));
      return false;
    }
  };

  const handleValueChange = (key: string, value: string) => {
    setEnvVars(prev => prev.map(ev =>
      ev.key === key ? { ...ev, value, status: 'pending' } : ev
    ));
  };

  const handleBlur = async (envVar: EnvVar) => {
    if (envVar.value.trim()) {
      await validateApiKey(envVar);
    }
  };

  const handleValidateAll = async () => {
    const essentialVars = envVars.filter(ev => ev.required);
    for (const envVar of essentialVars) {
      if (envVar.value.trim()) {
        await validateApiKey(envVar);
      }
    }
  };

  const handleSaveAndRestart = async () => {
    setIsSaving(true);

    try {
      const response = await fetch('/api/setup/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          values: envVars.reduce((acc, ev) => ({
            ...acc,
            [ev.key]: ev.value
          }), {})
        })
      });

      if (response.ok) {
        setSetupComplete(true);
        setCurrentStep(3); // Complete step

        // Trigger restart
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const essentialVars = envVars.filter(ev => ev.required);
  const optionalVars = envVars.filter(ev => !ev.required);

  const essentialComplete = essentialVars.every(ev => ev.status === 'valid');
  const hasErrors = envVars.some(ev => ev.status === 'invalid');

  if (isLoading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className={`text-lg ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Loading setup...</p>
        </div>
      </div>
    );
  }

  if (setupComplete && currentStep === 0) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className={`max-w-2xl w-full mx-4 p-8 rounded-2xl shadow-xl ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
          <div className="text-center mb-8">
            <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
            <h1 className={`text-3xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Setup Complete!
            </h1>
            <p className={`text-lg ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Your AI Realtor platform is configured and ready to use.
            </p>
          </div>

          <div className={`p-6 rounded-xl mb-6 ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
            <h2 className={`text-xl font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Configured Integrations
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {envVars.filter(ev => ev.value).map(ev => (
                <div key={ev.key} className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    {ev.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setSetupComplete(false)}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition ${
                isDarkMode
                  ? 'bg-gray-800 text-white hover:bg-gray-700'
                  : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
              }`}
            >
              Edit Configuration
            </button>
            <a
              href="/"
              className={`flex-1 px-6 py-3 rounded-lg font-semibold text-center transition ${
                isDarkMode
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
      {/* Progress Steps */}
      <div className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {SETUP_STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition ${
                      index <= currentStep
                        ? 'bg-blue-600 text-white'
                        : isDarkMode
                        ? 'bg-gray-800 text-gray-500'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {index < currentStep ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <div className={`mt-2 text-xs text-center ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {step.title}
                  </div>
                </div>
                {index < SETUP_STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 rounded ${
                      index < currentStep
                        ? 'bg-blue-600'
                        : isDarkMode
                        ? 'bg-gray-800'
                        : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {currentStep === 0 && (
          <div className={`p-8 rounded-2xl shadow-xl ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
            <h1 className={`text-4xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Welcome to AI Realtor 🏠
            </h1>
            <p className={`text-xl mb-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Let's configure your platform in just a few minutes
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className={`p-6 rounded-xl ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                <div className="w-12 h-12 rounded-lg bg-blue-600 flex items-center justify-center mb-4">
                  <Key className="w-6 h-6 text-white" />
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  Add API Keys
                </h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Enter your API keys for essential services
                </p>
              </div>

              <div className={`p-6 rounded-xl ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                <div className="w-12 h-12 rounded-lg bg-green-600 flex items-center justify-center mb-4">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  Validate Keys
                </h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  We'll test each key to make sure it works
                </p>
              </div>

              <div className={`p-6 rounded-xl ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                <div className="w-12 h-12 rounded-lg bg-purple-600 flex items-center justify-center mb-4">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  Start Using
                </h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Your platform will be ready to use instantly
                </p>
              </div>
            </div>

            <button
              onClick={() => setCurrentStep(1)}
              className={`w-full px-6 py-4 rounded-lg font-semibold text-lg transition ${
                isDarkMode
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Get Started →
            </button>
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <div className={`p-8 rounded-2xl shadow-xl mb-6 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
              <h2 className={`text-2xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Essential API Keys
              </h2>
              <p className={`mb-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                These keys are required for the platform to work
              </p>

              <div className="space-y-6">
                {essentialVars.map((envVar) => (
                  <EnvVarInput
                    key={envVar.key}
                    envVar={envVar}
                    isDarkMode={isDarkMode}
                    onChange={handleValueChange}
                    onBlur={handleBlur}
                  />
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => setCurrentStep(0)}
                className={`px-6 py-3 rounded-lg font-semibold transition ${
                  isDarkMode
                    ? 'bg-gray-800 text-white hover:bg-gray-700'
                    : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
                }`}
              >
                ← Back
              </button>
              <button
                onClick={handleValidateAll}
                disabled={!essentialVars.every(ev => ev.value.trim())}
                className={`flex-1 px-6 py-3 rounded-lg font-semibold transition ${
                  essentialVars.every(ev => ev.value.trim())
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-400 text-gray-600 cursor-not-allowed'
                }`}
              >
                Validate All Keys
              </button>
              <button
                onClick={() => setCurrentStep(2)}
                disabled={!essentialComplete}
                className={`px-6 py-3 rounded-lg font-semibold transition ${
                  essentialComplete
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-400 text-gray-600 cursor-not-allowed'
                }`}
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div>
            <div className={`p-8 rounded-2xl shadow-xl mb-6 ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
              <h2 className={`text-2xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Optional API Keys
              </h2>
              <p className={`mb-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Add these keys to unlock additional features (you can add them later too)
              </p>

              <div className="space-y-6">
                {optionalVars.map((envVar) => (
                  <EnvVarInput
                    key={envVar.key}
                    envVar={envVar}
                    isDarkMode={isDarkMode}
                    onChange={handleValueChange}
                    onBlur={handleBlur}
                  />
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => setCurrentStep(1)}
                className={`px-6 py-3 rounded-lg font-semibold transition ${
                  isDarkMode
                    ? 'bg-gray-800 text-white hover:bg-gray-700'
                    : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
                }`}
              >
                ← Back
              </button>
              <button
                onClick={handleSaveAndRestart}
                disabled={!essentialComplete || hasErrors || isSaving}
                className={`flex-1 px-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                  !essentialComplete || hasErrors || isSaving
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Saving and Restarting...
                  </>
                ) : (
                  'Complete Setup & Restart'
                )}
              </button>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className={`p-8 rounded-2xl shadow-xl ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
            <div className="text-center">
              <CheckCircle className="w-20 h-20 mx-auto mb-6 text-green-500" />
              <h1 className={`text-4xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Setup Complete! 🎉
              </h1>
              <p className={`text-xl mb-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Your AI Realtor platform is now configured and ready to use.
              </p>

              <div className={`p-6 rounded-xl mb-8 ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                <h2 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  What's Next?
                </h2>
                <div className="space-y-3 text-left">
                  <a href="/" className={`flex items-center gap-3 p-3 rounded-lg transition ${
                    isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                  }`}>
                    <Globe className="w-5 h-5 text-blue-500" />
                    <span className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>
                      Open the Dashboard
                    </span>
                  </a>
                  <div className={`flex items-center gap-3 p-3 rounded-lg ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    <Bot className="w-5 h-5 text-green-500" />
                    <span>Chat with @Smartrealtoraibot on Telegram</span>
                  </div>
                  <div className={`flex items-center gap-3 p-3 rounded-lg ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    <Phone className="w-5 h-5 text-purple-500" />
                    <span>Connect Claude Desktop for 135+ voice commands</span>
                  </div>
                </div>
              </div>

              <a
                href="/"
                className={`inline-block px-8 py-4 rounded-lg font-semibold text-lg transition ${
                  isDarkMode
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                Go to Dashboard →
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface EnvVarInputProps {
  envVar: EnvVar;
  isDarkMode: boolean;
  onChange: (key: string, value: string) => void;
  onBlur: (envVar: EnvVar) => void;
}

function EnvVarInput({ envVar, isDarkMode, onChange, onBlur }: EnvVarInputProps) {
  const [showValue, setShowValue] = useState(false);

  return (
    <div className={`p-6 rounded-xl border-2 transition ${
      envVar.status === 'valid'
        ? 'border-green-500'
        : envVar.status === 'invalid'
        ? 'border-red-500'
        : envVar.status === 'validating'
        ? 'border-blue-500'
        : isDarkMode
        ? 'border-gray-700'
        : 'border-gray-200'
    }`}>
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
          {envVar.icon}
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <label className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              {envVar.label}
            </label>
            {envVar.required && (
              <span className="px-2 py-0.5 text-xs rounded bg-red-600 text-white">Required</span>
            )}
            {envVar.status === 'valid' && (
              <CheckCircle className="w-5 h-5 text-green-500" />
            )}
            {envVar.status === 'invalid' && (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
            {envVar.status === 'validating' && (
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            )}
          </div>

          <p className={`text-sm mb-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            {envVar.description}
          </p>

          <div className="relative">
            <input
              type={showValue ? 'text' : 'password'}
              value={envVar.value}
              onChange={(e) => onChange(envVar.key, e.target.value)}
              onBlur={() => onBlur(envVar)}
              placeholder={envVar.placeholder}
              className={`w-full px-4 py-3 pr-12 rounded-lg font-mono text-sm border-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isDarkMode
                  ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'
              }`}
            />
            <button
              type="button"
              onClick={() => setShowValue(!showValue)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showValue ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          {envVar.error && (
            <p className="mt-2 text-sm text-red-500">{envVar.error}</p>
          )}

          {envVar.status === 'valid' && (
            <p className="mt-2 text-sm text-green-500">✓ API key is valid and working!</p>
          )}
        </div>
      </div>
    </div>
  );
}
