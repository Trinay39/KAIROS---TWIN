import { useEffect, useRef, useState } from 'react';
import { Clock } from 'lucide-react';
import { messageForError } from '../api/client';
import { endpoints } from '../api/endpoints';
import { HistoryCharts } from '../components/HistoryCharts';
import { useDemo } from '../context/DemoContext';
import type { RequestStatus, StudentHistory as StudentHistoryType } from '../types';
import { isFailureStatus } from '../types';

export default function StudentHistory() {
  const { state } = useDemo();
  const { input } = state;
  const [history, setHistory] = useState<StudentHistoryType | null>(null);
  const [status, setStatus] = useState<RequestStatus>('pending');
  const [error, setError] = useState<string | null>(null);
  const [loadedKey, setLoadedKey] = useState<string | null>(null);
  const requestSeq = useRef(0);
  const selectionKey = `${input.student_id}:${input.day}`;
  const observations = history?.student_id === input.student_id ? (history.observations ?? []) : [];
  const summary = history?.observation_summary;
  const loading = loadedKey !== selectionKey;

  useEffect(() => {
    requestSeq.current += 1;
    const requestId = requestSeq.current;

    endpoints.history(input.student_id, input.day)
      .then((response) => {
        if (requestSeq.current !== requestId) return;
        setHistory(response);
        setStatus('done');
        setError(null);
        setLoadedKey(selectionKey);
      })
      .catch((caught: unknown) => {
        if (requestSeq.current !== requestId) return;
        setError(messageForError(caught, 'Student history is unavailable.'));
        setStatus('error');
        setLoadedKey(selectionKey);
      });
  }, [selectionKey, input.student_id, input.day]);

  return (
    <div className="max-w-6xl mx-auto space-y-5 animate-fade-up">
      <header className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1">
          <Clock size={14} className="text-[#00bfa5]" />
          <span className="text-[10px] uppercase tracking-widest text-white/30">Student History</span>
        </div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">Student History</h1>
        <p className="text-sm text-white/40 mt-2">Student: <b className="text-white">{input.student_id}</b> / Current day: <b className="text-white">{input.day}</b></p>
      </header>

      <section className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
        <h2 className="text-[10px] font-bold text-[#00bfa5] mb-2">PROVENANCE</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[10px] text-white/60">
          <span>Observation source: <b className="text-white">{summary?.data_source ?? 'Unavailable'}</b></span>
          <span>Rows loaded: <b className="text-white">{summary?.total_observations ?? observations.length}</b></span>
          <span>Current day limit: <b className="text-white">{summary?.current_day ?? input.day}</b></span>
        </div>
        <p className="text-[10px] text-white/30 mt-2">Synthetic/demo observation means prototype demo data. Derived Twin state and model predictions are separate from these observed rows.</p>
      </section>

      {loading && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-[#f0a500]">Loading student history...</div>
      )}

      {!loading && isFailureStatus(status) && (
        <div className="rounded-xl p-4 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">{error || 'Student history is unavailable.'}</div>
      )}

      {!loading && status === 'done' && observations.length === 0 && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/35">
          {summary?.reason ?? 'No historical observations available.'}
        </div>
      )}

      {!loading && status === 'done' && observations.length > 0 && (
        <>
          <HistoryCharts observations={observations} />
          <p className="text-[10px] text-white/20 text-center">History charts use observations up to the selected day only. They are not historical ground-truth overload labels.</p>
        </>
      )}
    </div>
  );
}
