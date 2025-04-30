import axios from "axios";

// Extender el objeto ImportMetaEnv para incluir las variables de entorno específicas
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

// Extender ImportMeta
interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
}); 