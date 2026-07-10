import { useState } from 'react';
import type { FormEvent } from 'react';
import { Activity, LockKeyhole, ShieldCheck } from 'lucide-react';

interface LoginScreenProps {
  onLogin: (name: string) => void;
}

const ACCESS_CODE = 'silentlink';

export const LoginScreen = ({ onLogin }: LoginScreenProps) => {
  const [name, setName] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (name.trim().length < 2) {
      setError('Enter a profile name to continue.');
      return;
    }

    if (accessCode.trim().toLowerCase() !== ACCESS_CODE) {
      setError('Access code did not match.');
      return;
    }

    setError('');
    onLogin(name.trim());
  };

  return (
    <main className="login-shell">
      <section className="login-hero" aria-label="Silentlink secure login">
        <div className="login-brand">
          <div className="brand-icon">
            <Activity />
          </div>
          <div>
            <span className="brand-name">Silentlink</span>
            <span className="brand-subtitle">Secure gesture workspace</span>
          </div>
        </div>

        <div className="login-copy">
          <p className="eyebrow">Controlled access</p>
          <h1>Sign in before gesture control starts.</h1>
          <p>
            Camera tracking, WebSocket gesture commands, cursor movement, and launch actions start only after this session is authenticated.
          </p>
        </div>

        <div className="login-assurance">
          <div>
            <ShieldCheck />
            <span>Camera locked at login</span>
          </div>
          <div>
            <LockKeyhole />
            <span>Login required</span>
          </div>
        </div>
      </section>

      <section className="login-card" aria-label="Login form">
        <div className="section-heading">
          <div>
            <span className="section-kicker"><LockKeyhole /> Operator Login</span>
            <h2>Enter workspace</h2>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            <span>Profile name</span>
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              autoComplete="username"
              placeholder="Operator"
            />
          </label>

          <label>
            <span>Access code</span>
            <input
              type="password"
              value={accessCode}
              onChange={(event) => setAccessCode(event.target.value)}
              autoComplete="current-password"
              placeholder="silentlink"
            />
          </label>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="login-button">
            <ShieldCheck />
            Unlock session
          </button>
        </form>

        <p className="login-footnote">Demo access code: silentlink</p>
      </section>
    </main>
  );
};
