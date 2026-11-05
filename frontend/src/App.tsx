import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { FloatingConsultantDrawer } from './components/FloatingConsultantDrawer';

// Pages
import { Home } from './pages/Home';
import { ExploreCars } from './pages/ExploreCars';
import { RentCars } from './pages/RentCars';
import { BuyCars } from './pages/BuyCars';
import { VehicleDetails } from './pages/VehicleDetails';
import { CompareCars } from './pages/CompareCars';
import { Booking } from './pages/Booking';
import { Checkout } from './pages/Checkout';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { About } from './pages/About';
import { Contact } from './pages/Contact';
import { ConsultantPage } from './pages/ConsultantPage';

// Scroll to top on route navigation
const ScrollToTop: React.FC = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

export const App: React.FC = () => {
  return (
    <Router>
      <ScrollToTop />
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
        <Navbar />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/explore" element={<ExploreCars />} />
            <Route path="/rent" element={<RentCars />} />
            <Route path="/buy" element={<BuyCars />} />
            <Route path="/vehicles/:id" element={<VehicleDetails />} />
            <Route path="/compare" element={<CompareCars />} />
            <Route path="/booking/:vehicleId" element={<Booking />} />
            <Route path="/checkout/:id" element={<Checkout />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/consultant" element={<ConsultantPage />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </main>

        <Footer />

        {/* Global Persistent AI Automotive Consultant Drawer */}
        <FloatingConsultantDrawer />
      </div>
    </Router>
  );
};
export default App;
