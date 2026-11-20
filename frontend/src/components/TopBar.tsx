import { useEffect, useState } from 'react';
import { PlayCircle, Wifi, WifiOff } from 'lucide-react';
import { endpoints } from '../api/endpoints';
import { useDemo } from '../context/DemoContext';
import DemoModal from './DemoModal';
import type { ModelMetadata } from '../types';

export default function TopBar() {
  const { state } = useDemo();
  const [demoOpen, setDemoOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'unhealthy' | 'offline'>('checking');
  const [modelMetadata, setModelMetadata] = useState<ModelMetadata | null>(null);
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    async function check() {
      try {
        const health = await endpoints.health();
        setApiStatus(health.status === 'ok' && health.model_loaded && health.production_model_available ? 'online' : 'unhealthy');
        try {
          const metadata = await endpoints.modelMetadata();
          setModelMetadata(metadata);
        } catch {
          setModelMetadata(null);
        }
      } catch {
        setApiStatus('offline');
        setModelMetadata(null);
      }
    }
    check();
    const interval = setInterval(check, 8000);
    return () => clearInterval(interval);
  }, []);

  const online = apiStatus === 'online';
  const statusText = online
    ? 'API ONLINE'
    : apiStatus === 'checking'
      ? 'Checking API...'
      : apiStatus === 'unhealthy'
        ? 'API UNHEALTHY'
        : 'API OFFLINE';

  return (
    <>
      <header className="h-14 flex items-center justify-between px-6 border-b border-white/5 bg-[#121317] shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-[11px] uppercase tracking-widest text-white/30">Student</span>
          <span className="text-sm font-medium text-white/80">Demo Mode</span>
          <span className="text-xs text-white/30">-</span>
          <span className="text-sm font-mono text-[#00bfa5]">{state.input.student_id}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden xl:flex items-center gap-2 text-[11px] text-white/35">
            <span className="uppercase tracking-widest">Production</span>
            <span className="font-mono text-white/65">
              {modelMetadata
                ? `${modelMetadata.model_name.toUpperCase()} / threshold ${modelMetadata.threshold}`
                : 'model metadata unavailable'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-white/30">
            {online ? <Wifi size={12} className="text-[#4ade80]" /> : <WifiOff size={12} className="text-[#e0606e]" />}
            <span>{statusText}</span>
            <span className="text-white/20 font-mono text-[10px] ml-1">{apiUrl}</span>
          </div>
          <button
            onClick={() => setDemoOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-white/8 hover:bg-white/12 text-white/80 hover:text-white rounded-lg text-xs font-medium transition-colors"
          >
            <PlayCircle size={14} />
            Demo Mode
          </button>
        </div>
      </header>
      {demoOpen && <DemoModal onClose={() => setDemoOpen(false)} />}
    </>
  );
}
