import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthLayout from "../layouts/AuthLayout";
import { fetchMe, getRoleHomePath, loginUser, saveSession } from "../services/auth";

export default function LoginPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
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
    setError("");
    setMessage("");

    try {
      const tokens = await loginUser(form);
      const user = await fetchMe(tokens.access);

      saveSession({
        access: tokens.access,
        refresh: tokens.refresh,
        user,
      });

      setMessage(`Sesion iniciada como ${user.username} (${user.role}).`);

      setTimeout(() => {
        navigate(getRoleHomePath(user.role));
      }, 500);
    } catch (err) {
      const detail =
        err?.data?.detail ||
        err?.data?.non_field_errors?.[0] ||
        "No fue posible iniciar sesion.";

      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Acceso seguro para pacientes, doctores y clinic."
      subtitle="Inicia sesion para acceder a tu panel, revisar citas, gestionar pacientes y continuar con tu flujo clinico."
    >
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-400">
          Login
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white">
          Iniciar sesion
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Usa tu usuario y contraseña para entrar al sistema.
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
            placeholder="usuario"
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
          {loading ? "Entrando..." : "Entrar"}
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
