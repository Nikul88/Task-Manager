export const environment = {
  production: false,
  apiUrl: (globalThis as any).__env?.apiUrl || 'http://localhost:8000/api'
};
