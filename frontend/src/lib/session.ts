const SESSION_KEY = 'aibrief_session_id';
const USER_KEY = 'aibrief_user';

export interface StoredUser {
  userId: string;
  username: string;
}

export function getSessionId(): string {
  if (typeof window === 'undefined') return 'ssr';
  // Logged-in users use their user_id as the persistent session
  const user = getStoredUser();
  if (user) return user.userId;
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function resetSessionId(): void {
  if (typeof window === 'undefined') return;
  // Don't reset session for logged-in users
  if (getStoredUser()) return;
  localStorage.setItem(SESSION_KEY, crypto.randomUUID());
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as StoredUser) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(USER_KEY);
}
