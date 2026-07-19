/**
 * TASK-026 acceptance criterion under test: "Navigating to /console with no
 * staff session lands on the console login; the patient app at / is
 * byte-for-byte unaffected (its entry still renders PatientCompanionApp;
 * ?home=1 still works)."
 */
import { afterEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

function goTo(path: string) {
  window.history.pushState({}, '', path);
}

describe('App entry switch (TASK-026: path-based /console mount, patient app untouched)', () => {
  afterEach(() => {
    goTo('/');
  });

  it('renders the patient companion app (onboarding) at "/"', () => {
    goTo('/');
    render(<App />);
    expect(screen.getByText(/Đăng nhập để theo dõi lịch khám/)).toBeInTheDocument();
  });

  it('the ?home=1 demo shortcut still opens the in-hospital live-companion home', () => {
    goTo('/?home=1');
    render(<App />);
    expect(screen.getByText(/Đang đồng hành cùng bạn/)).toBeInTheDocument();
  });

  it('renders the console login when the path starts with /console', () => {
    goTo('/console');
    render(<App />);
    expect(screen.getByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ })).toBeInTheDocument();
  });

  it('a nested /console path also mounts the console (not the patient app)', () => {
    goTo('/console/dashboard');
    render(<App />);
    expect(screen.getByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ })).toBeInTheDocument();
    expect(screen.queryByText(/Đăng nhập để theo dõi lịch khám/)).not.toBeInTheDocument();
  });

  it('any non-/console path still renders the patient app entry, unaffected', () => {
    goTo('/');
    render(<App />);
    expect(screen.getByText(/Đăng nhập để theo dõi lịch khám/)).toBeInTheDocument();
  });

  it('a sibling path merely prefixed by "console" (e.g. /console-room) renders the patient app, not the console (code-reviewer Minor finding)', () => {
    goTo('/console-room');
    render(<App />);
    expect(screen.getByText(/Đăng nhập để theo dõi lịch khám/)).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ }),
    ).not.toBeInTheDocument();
  });

  it('another sibling path (/consoles) also renders the patient app, not the console', () => {
    goTo('/consoles');
    render(<App />);
    expect(screen.getByText(/Đăng nhập để theo dõi lịch khám/)).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ }),
    ).not.toBeInTheDocument();
  });
});
