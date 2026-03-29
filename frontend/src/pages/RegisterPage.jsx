import { useState } from "react";
import AuthLayout from "../layouts/AuthLayout";
import { registerPatient } from "../services/auth";

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    phone: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const user = await registerPatient(form);
      setMessage(`Cuenta creada correctamente para ${user.username}.`);
      setForm({
        username: "",
        email: "",
        phone: "",
        password: "",
      });
    } catch (err) {
      const data = err?.data;
      const firstError =
        data?.username?.[0] ||
        data?.email?.[0] ||
        data?.password?.[0] ||
        data?.phone?.[0] ||
        data?.detail ||
        "No fue posible registrar la cuenta.";

      setError(firstError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Registro de pacientes con acceso rapido a la clinica."
      subtitle="Crea tu cuenta como paciente para agendar citas, consultar historial y acceder a telemedicina."
    >
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-400">
          Registro
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white">
          Crear cuenta
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Este formulario es solo para pacientes.
        </p>
      </div>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-200">
            Usuario
          </label>
          <input
            name="username"
            type="text"
            value={form.username}
            onChange={handleChange}
            placeholder="patient_user"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-200">
            Correo electronico
          </label>
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            placeholder="patient@email.com"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-200">
            Telefono
          </label>
          <input
            name="phone"
            type="text"
            value={form.phone}
            onChange={handleChange}
            placeholder="6641234567"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-200">
            Contraseña
          </label>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="********"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Creando cuenta..." : "Crear cuenta"}
        </button>
      </form>

      {message ? (
        <div className="mt-6 rounded-2xl border border-emerald-700/40 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          {message}
        </div>
      ) : null}

      {error ? (
        <div className="mt-6 rounded-2xl border border-red-700/40 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      ) : null}
    </AuthLayout>
  );
}
