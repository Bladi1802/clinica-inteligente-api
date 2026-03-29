import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { getStoredUser } from "../services/auth";
import { fetchMyAppointments } from "../services/appointments";

export default function PatientDashboardPage() {
  const user = getStoredUser();

  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAppointments() {
      setLoading(true);
      setError("");

      try {
        const data = await fetchMyAppointments();
        setAppointments(data);
      } catch (err) {
        const detail =
          err?.data?.detail || "No fue posible cargar las citas del paciente.";
        setError(detail);
      } finally {
        setLoading(false);
      }
    }

    loadAppointments();
  }, []);

  return (
    <MainLayout title="Dashboard de Paciente">
      <div className="grid gap-6 md:grid-cols-3">
        <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
            Usuario
          </p>
          <h2 className="mt-4 text-2xl font-bold text-white">{user?.username}</h2>
        </article>

        <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
            Rol
          </p>
          <h2 className="mt-4 text-2xl font-bold text-white">{user?.role}</h2>
        </article>

        <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
            Total citas
          </p>
          <h2 className="mt-4 text-2xl font-bold text-blue-400">
            {appointments.length}
          </h2>
        </article>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <h3 className="text-xl font-semibold text-white">Mis citas</h3>
        <p className="mt-3 text-slate-300">
          Vista inicial del paciente conectada al endpoint real de citas.
        </p>

        {loading ? (
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-slate-400">
            Cargando citas...
          </div>
        ) : null}

        {error ? (
          <div className="mt-6 rounded-2xl border border-red-700/40 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        ) : null}

        {!loading && !error ? (
          <div className="mt-6 space-y-4">
            {appointments.length === 0 ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-slate-400">
                No tienes citas registradas.
              </div>
            ) : (
              appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-white">
                        Cita #{appointment.id}
                      </p>
                      <p className="mt-1 text-sm text-slate-400">
                        {appointment.reason || "Sin motivo especificado"}
                      </p>
                    </div>

                    <span className="rounded-full border border-slate-700 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                      {appointment.status}
                    </span>
                  </div>

                  <div className="mt-4 grid gap-2 text-sm text-slate-400 sm:grid-cols-2">
                    <p>Fecha: {appointment.scheduled_at}</p>
                    <p>Doctor ID: {appointment.doctor || "Sin asignar"}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : null}
        
      </div>
    </MainLayout>
  );
}
