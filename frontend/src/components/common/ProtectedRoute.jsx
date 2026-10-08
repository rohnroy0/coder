import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';

export const ProtectedRoute = ({ children, allowedRole }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner fullScreen message="Verifying authentication..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRole && user?.role !== allowedRole) {
    // Redirect teacher to teacher dashboard, student to student dashboard
    const redirectPath = user?.role === 'TEACHER' ? '/teacher' : '/student';
    return <Navigate to={redirectPath} replace />;
  }

  return children;
};

export default ProtectedRoute;
