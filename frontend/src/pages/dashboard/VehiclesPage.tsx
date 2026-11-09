import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const VehiclesPage: React.FC = () => {
  const navigate = useNavigate();
  useEffect(() => {
    navigate('/dashboard/purchases', { replace: true });
  }, [navigate]);
  return null;
};
