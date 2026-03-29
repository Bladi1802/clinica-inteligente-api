import { Navigate, Route, Routes } from "react-router-dom";
import ClinicDashboardPage from "./pages/ClinicDashboardPage";
import DoctorDashboardPage from "./pages/DoctorDashboardPage";
import LoginPage from "./pages/LoginPage";
import PatientDashboardPage from "./pages/PatientDashboardPage";
import RegisterPage from "./pages/RegisterPage";
import ProtectedRoute from "./routes/ProtectedRoute";
import { getRoleHomePath, getStoredUser, isAuthenticated } from "./services/auth";

export default function App() {
  const user = getStoredUser();
  const homePath = user ? getRoleHomePath(user.role) : "/login";

  return (
    <Routes>
      <Route
        path="/"
        element={
          isAuthenticated() ? (
            <Navigate to={homePath} replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/login"
        element={
          isAuthenticated() ? <Navigate to={homePath} replace /> : <LoginPage />
        }
      />
      <Route
        path="/register"
        element={
          isAuthenticated() ? <Navigate to={homePath} replace /> : <RegisterPage />
        }
      />
      <Route
        path="/patient"
        element={
          <ProtectedRoute>
            <PatientDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor"
        element={
          <ProtectedRoute>
            <DoctorDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/clinic"
        element={
          <ProtectedRoute>
            <ClinicDashboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
