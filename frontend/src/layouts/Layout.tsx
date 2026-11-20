import DemoBanner from '../components/DemoBanner';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';

export default function Layout() {
  return (
    <>
      <DemoBanner />
      <div className="flex h-screen bg-[#0d0e12] overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-auto p-6 scrollbar-thin">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
