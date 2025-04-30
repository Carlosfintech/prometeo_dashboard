import axios from "axios";

// Extender el objeto ImportMetaEnv para incluir las variables de entorno específicas
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

// Extender ImportMeta
interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Verificar la URL del API
const API_URL = import.meta.env.VITE_API_URL;
if (!API_URL) {
  console.error("⚠️ La variable de entorno VITE_API_URL no está definida");
}

// Configuración del cliente axios
export const api = axios.create({
  baseURL: API_URL,
  // No enviar cookies para peticiones cross-origin - evita problemas CORS
  withCredentials: false,
  // Asegurar que los headers CORS estén configurados correctamente
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // Timeouts para evitar bloqueos en peticiones lentas
  timeout: 10000,  // 10 segundos
});

// Interceptor para debug - solo en desarrollo
if (import.meta.env.DEV) {
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
}

// Interceptor para manejo de errores - siempre activo
api.interceptors.response.use(
  response => response,
  async error => {
    // Extraer información del error
    const { response, request, message, config } = error;
    
    // Caso 1: Error de timeout o de red
    if (!response) {
      console.error(`Error de red o timeout: ${message}`);
      return Promise.reject(error);
    }
    
    // Caso 2: Error del servidor (500, etc.)
    if (response.status >= 500) {
      console.error(`Error del servidor ${response.status}: ${response.statusText}`);
      return Promise.reject(error);
    }

    // Caso 3: Error de cliente (400, 401, 404, etc.)
    if (response.status >= 400) {
      console.error(`Error del cliente ${response.status}: ${response.statusText}`);
      
      // En caso de 404, podríamos intentar realizar un fallback o reintentar
      if (response.status === 404 && !config._isRetry) {
        // Marcar que estamos reintentando para evitar bucles infinitos
        const newConfig = { ...config, _isRetry: true };
        
        // Si la URL termina con un slash, intentar sin él o viceversa
        if (config.url?.endsWith('/')) {
          newConfig.url = config.url.slice(0, -1);
        } else if (config.url) {
          newConfig.url = config.url + '/';
        }
        
        // Solo reintentar si la URL cambió
        if (newConfig.url !== config.url) {
          console.log(`Reintentando petición con URL modificada: ${newConfig.url}`);
          return api(newConfig);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Verificar conectividad al iniciar
api.get('/')
  .then(() => console.log('✅ Conexión exitosa con el API'))
  .catch(error => {
    console.error('❌ Error al verificar conexión con el API:', error.message);
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Data:`, error.response.data);
    }
  });

export default api; 