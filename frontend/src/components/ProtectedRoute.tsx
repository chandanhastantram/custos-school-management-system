import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user } = useAuthStore();
  console.log("ProtectedRoute check:", { isAuthenticated, user });
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default ProtectedRoute;
