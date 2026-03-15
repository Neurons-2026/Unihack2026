const SESSION_KEY = 'aibrief_session_id';

export function getSessionId(): string {
  if (typeof window === 'undefined') return 'ssr';
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function resetSessionId(): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(SESSION_KEY, crypto.randomUUID());
}
