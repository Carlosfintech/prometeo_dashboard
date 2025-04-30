import axios from "axios";

// Extender el objeto ImportMetaEnv para incluir las variables de entorno específicas
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

// Extender ImportMeta
interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Configuración del cliente axios
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  // No enviar cookies para peticiones cross-origin
  withCredentials: false,
  // Asegurar que los headers CORS estén configurados correctamente
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Interceptor para debug
api.interceptors.request.use(config => {
  console.log(`🚀 Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config);
  return config;
});

api.interceptors.response.use(
  response => {
    console.log(`✅ Response:`, response);
    return response;
  },
  error => {
    console.error(`❌ Error:`, error);
    return Promise.reject(error);
  }
); 