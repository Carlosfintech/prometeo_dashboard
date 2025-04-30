# Prometeo Dashboard - Frontend

Frontend para el dashboard de análisis y gestión de clientes de Prometeo, desarrollado con React, TypeScript y Vite.

## Tecnologías

- **React 18**: Biblioteca para construcción de interfaces de usuario
- **TypeScript**: Superset de JavaScript con tipado estático
- **Vite**: Build tool y servidor de desarrollo
- **TailwindCSS**: Framework CSS de utilidades
- **shadcn/ui**: Componentes de UI accesibles y personalizables
- **React Query**: Gestión de estado del servidor y caché
- **React Router**: Enrutamiento para aplicaciones React
- **Recharts/Chart.js**: Bibliotecas para visualización de datos
- **Axios**: Cliente HTTP para comunicación con la API

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/      # Componentes específicos del dashboard
│   │   └── ui/             # Componentes de UI reutilizables (shadcn)
│   ├── hooks/              # Custom hooks 
│   ├── lib/                # Utilidades y configuración
│   │   ├── api.ts          # Cliente HTTP y configuración de API
│   │   ├── react-query.ts  # Configuración de React Query
│   │   └── utils.ts        # Funciones de utilidad
│   ├── pages/              # Componentes de páginas/rutas
│   │   ├── Index.tsx       # Página principal del dashboard
│   │   └── NotFound.tsx    # Página 404
│   └── main.tsx            # Punto de entrada de la aplicación
└── ...
```

## Componentes Principales

### Componentes de Dashboard

- **HeatMap**: Visualiza correlaciones entre variables como edad, ingresos y perfil de riesgo con un mapa de calor interactivo.
- **PriorityClientsTable**: Tabla paginada de clientes prioritarios con opciones de gestión.
- **KPICards**: Tarjetas con indicadores clave de rendimiento y métricas de negocio.
- **ContactProgress**: Seguimiento del progreso de contacto de clientes con visualización de metas.
- **ProbabilityDistribution**: Gráfico de distribución de probabilidades por categorías.
- **AIAssistant**: Asistente de IA para análisis de datos y recomendaciones.
- **ExportPanel**: Panel para exportación de datos y generación de reportes.
- **Sidebar**: Barra lateral de navegación del dashboard.
- **TopBar**: Barra superior con búsqueda y controles de usuario.

## Configuración de Desarrollo

### Requisitos Previos

- Node.js 18+ 
- npm o yarn

### Variables de Entorno

Cree un archivo `.env` basado en `.env.example`:

```
VITE_API_URL=http://localhost:8001
```

### Instalación

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en [http://localhost:8082](http://localhost:8082)

### Scripts Disponibles

```bash
# Desarrollo
npm run dev

# Compilación para producción
npm run build

# Vista previa de la versión de producción
npm run preview

# Ejecución de pruebas
npm run test
```

## Comunicación con el Backend

El frontend se comunica con el backend a través de una API RESTful configurada en `src/lib/api.ts`. La URL base del API se configura mediante la variable de entorno `VITE_API_URL`.

## Despliegue

Para desplegar el frontend:

1. Generar build de producción:

```bash
npm run build
```

2. El directorio `dist` contiene los archivos estáticos optimizados listos para ser desplegados en cualquier servicio de hosting estático como Netlify, Vercel, o un servidor web tradicional.
