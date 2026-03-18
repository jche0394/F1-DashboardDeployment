import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import WelcomePage from "./pages/WelcomePage";
import DashboardPage from "./pages/DashboardPage";
import PredictionsPage from "./pages/PredictionsPage";
import RankingsPage from "./pages/RankingsPage";
import ComparePage from "./pages/ComparePage";
import Navbar from "./components/layout/Navbar";
import RenderNoticeModal from "./components/shared/RenderNoticeModal";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-black font-sans">
        <RenderNoticeModal />
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          
          <Route path="/dashboard" element={
            <div className="relative min-h-screen bg-black overflow-hidden">
              <div className="absolute inset-0 z-0">
                <div className="w-full h-full bg-gradient-to-br from-red-900/40 via-black to-blue-900/40"></div>
                
                {/* Speed lines effect */}
                <div className="absolute inset-0 opacity-15">
                  <div className="w-full h-full bg-speed-lines" style={{
                    backgroundImage: `
                      repeating-linear-gradient(
                        45deg,
                        transparent,
                        transparent 10px,
                        rgba(255,255,255,0.1) 10px,
                        rgba(255,255,255,0.1) 20px
                      )
                    `
                  }}></div>
                </div>
                
                {/* Checkered flag pattern */}
                <div className="absolute inset-0 opacity-5">
                  <div className="w-full h-full" style={{
                    backgroundImage: `
                      linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                      linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)
                    `,
                    backgroundSize: '20px 20px',
                    backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px'
                  }}></div>
                </div>
              </div>
              
              <div className="relative z-10">
                <Navbar />
                <DashboardPage />
              </div>
            </div>
          } />
          <Route path="/predictions" element={
            <div className="relative min-h-screen bg-black overflow-hidden">
              {/* Racing Background Effects */}
              <div className="absolute inset-0 z-0">
                {/* Racing-inspired gradient */}
                <div className="w-full h-full bg-gradient-to-br from-red-900/40 via-black to-blue-900/40"></div>
                
                {/* Speed lines effect */}
                <div className="absolute inset-0 opacity-15">
                  <div className="w-full h-full bg-speed-lines" style={{
                    backgroundImage: `
                      repeating-linear-gradient(
                        45deg,
                        transparent,
                        transparent 10px,
                        rgba(255,255,255,0.1) 10px,
                        rgba(255,255,255,0.1) 20px
                      )
                    `
                  }}></div>
                </div>
                
                {/* Checkered flag pattern */}
                <div className="absolute inset-0 opacity-5">
                  <div className="w-full h-full" style={{
                    backgroundImage: `
                      linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                      linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)
                    `,
                    backgroundSize: '20px 20px',
                    backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px'
                  }}></div>
                </div>
              </div>
              
              <div className="relative z-10">
                <Navbar />
                <PredictionsPage />
              </div>
            </div>
          } />
          <Route path="/rankings" element={
            <div className="relative min-h-screen bg-black overflow-hidden">
              {/* Racing Background Effects */}
              <div className="absolute inset-0 z-0">
                {/* Racing-inspired gradient */}
                <div className="w-full h-full bg-gradient-to-br from-red-900/40 via-black to-blue-900/40"></div>
                
                {/* Speed lines effect */}
                <div className="absolute inset-0 opacity-15">
                  <div className="w-full h-full bg-speed-lines" style={{
                    backgroundImage: `
                      repeating-linear-gradient(
                        45deg,
                        transparent,
                        transparent 10px,
                        rgba(255,255,255,0.1) 10px,
                        rgba(255,255,255,0.1) 20px
                      )
                    `
                  }}></div>
                </div>
                
                {/* Checkered flag pattern */}
                <div className="absolute inset-0 opacity-5">
                  <div className="w-full h-full" style={{
                    backgroundImage: `
                      linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                      linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)
                    `,
                    backgroundSize: '20px 20px',
                    backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px'
                  }}></div>
                </div>
              </div>
              
              <div className="relative z-10">
                <Navbar />
                <RankingsPage />
              </div>
            </div>
          } />
          <Route path="/compare" element={
            <div className="relative min-h-screen bg-black overflow-hidden">
              {/* Racing Background Effects */}
              <div className="absolute inset-0 z-0">
                {/* Racing-inspired gradient */}
                <div className="w-full h-full bg-gradient-to-br from-red-900/40 via-black to-blue-900/40"></div>
                
                {/* Speed lines effect */}
                <div className="absolute inset-0 opacity-15">
                  <div className="w-full h-full bg-speed-lines" style={{
                    backgroundImage: `
                      repeating-linear-gradient(
                        45deg,
                        transparent,
                        transparent 10px,
                        rgba(255,255,255,0.1) 10px,
                        rgba(255,255,255,0.1) 20px
                      )
                    `
                  }}></div>
                </div>
                
                {/* Checkered flag pattern */}
                <div className="absolute inset-0 opacity-5">
                  <div className="w-full h-full" style={{
                    backgroundImage: `
                      linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                      linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                      linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)
                    `,
                    backgroundSize: '20px 20px',
                    backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px'
                  }}></div>
                </div>
              </div>
              
              <div className="relative z-10">
                <Navbar />
                <ComparePage />
              </div>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}