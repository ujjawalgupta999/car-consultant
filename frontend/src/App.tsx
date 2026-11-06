import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { FloatingConsultantDrawer } from './components/FloatingConsultantDrawer';
import { useConsultantStore } from './store/consultantStore';
import { useVehicleStore } from './store/vehicleStore';

// Marketplace & Flow Pages
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
import { About } from './pages/About';
import { Contact } from './pages/Contact';
import { ConsultantPage } from './pages/ConsultantPage';
import { SellCarPage } from './pages/SellCarPage';

// Authenticated User Dashboard Sub-pages
import { DashboardLayout } from './pages/dashboard/DashboardLayout';
import { OverviewPage } from './pages/dashboard/OverviewPage';
import { PurchasesPage } from './pages/dashboard/PurchasesPage';
import { RentalsPage } from './pages/dashboard/RentalsPage';
import { PaymentsPage } from './pages/dashboard/PaymentsPage';
import { VehiclesPage } from './pages/dashboard/VehiclesPage';
import { ListingsPage } from './pages/dashboard/ListingsPage';
import { SavedPage } from './pages/dashboard/SavedPage';
import { ProfilePage } from './pages/dashboard/ProfilePage';
import { PaymentProcessingPage } from './pages/PaymentProcessingPage';
import { PaymentResultPage } from './pages/PaymentResultPage';

// Scroll to top and synchronize route context
const ScrollToTop: React.FC = () => {
  const { pathname } = useLocation();
  const { setActiveContext } = useConsultantStore();
  const { vehicles, fetchVehicles } = useVehicleStore();

  useEffect(() => {
    window.scrollTo(0, 0);
    setActiveContext({ currentRoute: pathname });
  }, [pathname, setActiveContext]);

  useEffect(() => {
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles]);

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
            <Route path="/sell-car" element={<SellCarPage />} />
            <Route path="/vehicles/:id" element={<VehicleDetails />} />
            <Route path="/compare" element={<CompareCars />} />
            <Route path="/booking/:vehicleId" element={<Booking />} />
            <Route path="/checkout/:id" element={<Checkout />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/payment/processing/:orderId" element={<PaymentProcessingPage />} />
            <Route path="/payment/result/:orderId" element={<PaymentResultPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            {/* Complete Authenticated User Dashboard */}
            <Route path="/dashboard" element={<DashboardLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="purchases" element={<PurchasesPage />} />
              <Route path="rentals" element={<RentalsPage />} />
              <Route path="payments" element={<PaymentsPage />} />
              <Route path="vehicles" element={<VehiclesPage />} />
              <Route path="listings" element={<ListingsPage />} />
              <Route path="saved" element={<SavedPage />} />
              <Route path="profile" element={<ProfilePage />} />
            </Route>

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
