import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const RentCars: React.FC = () => {
  const navigate = useNavigate();
  useEffect(() => {
    navigate('/buy', { replace: true });
  }, [navigate]);
  return null;
};
