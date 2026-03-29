import { apiRequest } from "./api";

export async function fetchMyAppointments() {
  return apiRequest("/api/appointments/");
}

export async function fetchDoctorAppointments() {
  return apiRequest("/api/doctor/appointments/");
}
