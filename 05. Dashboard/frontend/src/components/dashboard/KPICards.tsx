import { TrendingUp, TrendingDown, Users, DollarSign, CheckCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

interface KPICardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow';
  loading?: boolean;
}

// Interfaz para los datos de métricas
interface KPISummary {
  total_clients: number;
  churn_risk_mean: number;
  contacted: number;
  conversion_rate: number;
  at_risk_count: number;
  // Business metrics
  potential_clients: number;
  expected_conversion: number;
  financial_opportunity: number;
  contact_progress: number;
}

const KPICard = ({ 
  title, 
  value, 
  description, 
  trend, 
  trendValue, 
  icon, 
  color = 'blue', 
  loading = false 
}: KPICardProps) => {
  
  const colorClasses = {
    blue: 'bg-prometeo-blue/10 text-prometeo-blue',
    green: 'bg-prometeo-green/10 text-prometeo-green',
    red: 'bg-prometeo-red/10 text-prometeo-red',
    yellow: 'bg-prometeo-yellow/10 text-prometeo-yellow',
  };

  const trendIcon = trend === 'up' ? (
    <TrendingUp size={16} className="text-prometeo-green" />
  ) : trend === 'down' ? (
    <TrendingDown size={16} className="text-prometeo-red" />
  ) : null;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      {loading ? (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-sm font-medium text-gray-500">{title}</h3>
            {icon && <div className={`p-2 rounded-full ${colorClasses[color]}`}>{icon}</div>}
          </div>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold">{value}</p>
            {trend && trendValue && (
              <div className="flex items-center ml-2 text-xs">
                {trendIcon}
                <span className={trend === 'up' ? 'text-prometeo-green' : 'text-prometeo-red'}>
                  {trendValue}
                </span>
              </div>
            )}
          </div>
          {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
        </>
      )}
    </div>
  );
};

export const KPICards = () => {
  // Obtener los datos de métricas usando React Query y el cliente API centralizado
  const { data, isLoading, error } = useQuery<KPISummary>({
    queryKey: ["metricsSummary"],
    queryFn: () => api.get("/metrics/summary").then(res => res.data),
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Si hay un error o está cargando, mostrar las tarjetas en estado de carga
  if (isLoading || error) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Clientes Potenciales"
          value=""
          icon={<Users size={18} />}
          color="blue"
          loading={true}
        />
        <KPICard
          title="Conversión Esperada"
          value=""
          icon={<TrendingUp size={18} />}
          color="green"
          loading={true}
        />
        <KPICard
          title="Oportunidad Financiera"
          value=""
          icon={<DollarSign size={18} />}
          color="yellow"
          loading={true}
        />
        <KPICard
          title="Progreso de Contactos"
          value=""
          icon={<CheckCircle size={18} />}
          color="red"
          loading={true}
        />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* 1. Clientes Potenciales */}
      <KPICard
        title="Clientes Potenciales"
        value={data?.potential_clients ?? 0}
        icon={<Users size={18} />}
        color="blue"
        description="Clientes con probabilidad > umbral"
      />
      {/* 2. Conversión Esperada */}
      <KPICard
        title="Conversión Esperada"
        value={data?.expected_conversion ?? 0}
        icon={<TrendingUp size={18} />}
        color="green"
        description="20% de clientes potenciales"
      />
      {/* 3. Oportunidad Financiera */}
      <KPICard
        title="Oportunidad Financiera"
        value={`$${data?.financial_opportunity ?? 0}`}
        icon={<DollarSign size={18} />}
        color="yellow"
        description="Potencial en USD"
      />
      {/* 4. Progreso de Contactos */}
      <KPICard
        title="Progreso de Contactos"
        value={data?.contact_progress ?? 0}
        icon={<CheckCircle size={18} />}
        color="red"
        description="Contactados o en seguimiento"
      />
    </div>
  );
};

export default KPICards;
