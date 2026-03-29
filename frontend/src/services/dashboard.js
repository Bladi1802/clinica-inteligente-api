import { apiRequest } from "./api";

export async function fetchDashboardSummary() {
  return apiRequest("/api/dashboard/summary/");
}

export async function fetchDashboardTrends(days = 7) {
  return apiRequest(`/api/dashboard/trends/?days=${days}`);
}

export async function fetchClinicAppointments() {
  return apiRequest("/api/clinic/appointments/");
}
