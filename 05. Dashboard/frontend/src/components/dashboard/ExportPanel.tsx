import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import { api } from '../../lib/api';

interface Client {
  id: number;
  user_id: string;
  probability: number;
  status: string;
  age?: number;
  income_range?: string;
  risk_profile?: string;
  priority?: string;
}

export const ExportPanel = () => {
  // Fetch all clients (max 100)
  const { data: clients = [], isLoading } = useQuery<Client[]>({
    queryKey: ['clientsExport'],
    queryFn: async () => {
      const res = await api.get(`/clients/priority-list?page=1&size=100`);
      return res.data;
    }
  });

  // Filter options
  const statusOptions = ['pending','contacted','followup','converted','rejected'];
  const riskOptions = ['conservative','moderate','aggressive'];
  const priorityOptions = ['high','medium','low'];

  // State for selected filters
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [riskFilter, setRiskFilter] = useState<string[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<string[]>([]);

  const toggleFilter = (value: string, arr: string[], setter: (v: string[]) => void) => {
    if (arr.includes(value)) setter(arr.filter(x => x !== value));
    else setter([...arr, value]);
  };

  // Apply filters
  const filtered = clients.filter(c =>
    (statusFilter.length === 0 || statusFilter.includes(c.status)) &&
    (riskFilter.length === 0 || riskFilter.includes(c.risk_profile || '')) &&
    (priorityFilter.length === 0 || priorityFilter.includes(c.priority || ''))
  );

  // Export CSV
  const handleExport = () => {
    const header = ['id','user_id','probability','status','age','income_range','risk_profile','priority'];
    const rows = filtered.map(c => [
      c.id,
      c.user_id,
      c.probability.toFixed(2),
      c.status,
      c.age || '',
      c.income_range || '',
      c.risk_profile || '',
      c.priority || ''
    ]);
    const csvContent = [header, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clients_export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <h2 className="text-lg font-bold text-prometeo-black mb-4">Exportación y Marketing</h2>

      {/* Filtros */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <h3 className="text-sm font-medium mb-1">Estado</h3>
          <div className="flex flex-wrap gap-2">
            {statusOptions.map(opt => (
              <button
                key={opt}
                className={`px-2 py-1 text-xs rounded ${statusFilter.includes(opt) ? 'bg-prometeo-blue text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={() => toggleFilter(opt, statusFilter, setStatusFilter)}
              >{opt}</button>
          ))}
        </div>
      </div>
        <div>
          <h3 className="text-sm font-medium mb-1">Perfil</h3>
          <div className="flex flex-wrap gap-2">
            {riskOptions.map(opt => (
              <button
                key={opt}
                className={`px-2 py-1 text-xs rounded ${riskFilter.includes(opt) ? 'bg-prometeo-blue text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={() => toggleFilter(opt, riskFilter, setRiskFilter)}
              >{opt}</button>
            ))}
              </div>
        </div>
        <div>
          <h3 className="text-sm font-medium mb-1">Prioridad</h3>
          <div className="flex flex-wrap gap-2">
            {priorityOptions.map(opt => (
            <button
                key={opt}
                className={`px-2 py-1 text-xs rounded ${priorityFilter.includes(opt) ? 'bg-prometeo-blue text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={() => toggleFilter(opt, priorityFilter, setPriorityFilter)}
              >{opt}</button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Tabla de clientes */}
      <div className="overflow-auto max-h-80 mb-4">
        <table className="w-full text-sm table-auto">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1">Cliente</th>
              <th className="px-2 py-1">Prob.</th>
              <th className="px-2 py-1">Estado</th>
              <th className="px-2 py-1">Edad</th>
              <th className="px-2 py-1">Ingresos</th>
              <th className="px-2 py-1">Perfil</th>
              <th className="px-2 py-1">Prioridad</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.id} className="border-b hover:bg-gray-50">
                <td className="px-2 py-1">{c.user_id}</td>
                <td className="px-2 py-1">{(c.probability * 100).toFixed(1)}%</td>
                <td className="px-2 py-1">{c.status}</td>
                <td className="px-2 py-1">{c.age ?? '-'}</td>
                <td className="px-2 py-1">{c.income_range ?? '-'}</td>
                <td className="px-2 py-1">{c.risk_profile ?? '-'}</td>
                <td className="px-2 py-1">{c.priority ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
            </div>
            
      {/* Botón de exportación */}
              <button 
        className="flex items-center px-4 py-2 bg-prometeo-blue text-white rounded disabled:opacity-50"
            onClick={handleExport}
        disabled={filtered.length === 0 || isLoading}
          >
            <Download size={16} />
        <span className="ml-2">Descargar CSV ({filtered.length})</span>
          </button>
    </div>
  );
};

export default ExportPanel;
