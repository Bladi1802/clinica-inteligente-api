import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import {
  fetchClinicAppointments,
  fetchDashboardSummary,
  fetchDashboardTrends,
} from "../services/dashboard";

export default function ClinicDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [summaryData, trendsData, appointmentsData] = await Promise.all([
          fetchDashboardSummary(),
          fetchDashboardTrends(7),
          fetchClinicAppointments(),
        ]);

        setSummary(summaryData);
        setTrends(trendsData);
        setAppointments(appointmentsData);
      } catch (err) {
        const detail =
          err?.data?.detail || "No fue posible cargar el dashboard de clinic.";
        setError(detail);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const trendTotal =
    trends?.points?.reduce((acc, point) => acc + (point.total || 0), 0) || 0;

  return (
    <MainLayout title="Dashboard de Clinic">
      {loading ? (
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 text-slate-300">
          Cargando dashboard...
        </div>
      ) : null}

      {error ? (
        <div className="rounded-3xl border border-red-700/40 bg-red-500/10 p-6 text-red-300">
          {error}
        </div>
      ) : null}

      {!loading && !error ? (
        <>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                Total citas
              </p>
              <h2 className="mt-4 text-3xl font-bold text-white">
                {summary?.appointments?.total ?? 0}
              </h2>
            </article>

            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                Pendientes
              </p>
              <h2 className="mt-4 text-3xl font-bold text-yellow-400">
                {summary?.appointments?.pending ?? 0}
              </h2>
            </article>

            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                Confirmadas
              </p>
              <h2 className="mt-4 text-3xl font-bold text-blue-400">
                {summary?.appointments?.confirmed ?? 0}
              </h2>
            </article>

            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                Triage alto riesgo
              </p>
              <h2 className="mt-4 text-3xl font-bold text-red-400">
                {summary?.triage?.high_risk ?? 0}
              </h2>
            </article>
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                Tendencia 7 dias
              </p>
              <h3 className="mt-4 text-2xl font-bold text-white">{trendTotal}</h3>
              <p className="mt-3 text-sm text-slate-400">
                Total de citas registradas dentro del rango consultado.
              </p>

              <div className="mt-6 space-y-3">
                {trends?.points?.slice(-7).map((point, index) => (
                  <div
                    key={`${point.date}-${index}`}
                    className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3"
                  >
                    <span className="text-sm text-slate-300">{point.date}</span>
                    <span className="text-sm font-semibold text-white">
                      {point.total}
                    </span>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.25em] text-slate-500">
                    Citas recientes
                  </p>
                  <h3 className="mt-3 text-2xl font-bold text-white">
                    Vista operativa
                  </h3>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">
                  {appointments.length} registros
                </div>
              </div>

              <div className="mt-6 space-y-4">
                {appointments.length === 0 ? (
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-slate-400">
                    No hay citas disponibles.
                  </div>
                ) : (
                  appointments.slice(0, 6).map((appointment) => (
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
                        <p>Paciente ID: {appointment.patient}</p>
                        <p>Doctor ID: {appointment.doctor || "Sin asignar"}</p>
                        <p>Fecha: {appointment.scheduled_at}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </MainLayout>
  );
}
