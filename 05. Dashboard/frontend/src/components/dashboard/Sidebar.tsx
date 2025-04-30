
import { useState } from "react";
import { 
  BarChart, 
  PieChart, 
  Users, 
  Calendar, 
  MessageSquare, 
  Settings,
  Menu,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  return (
    <div 
      className={cn(
        "h-screen bg-white border-r border-gray-200 transition-all duration-300",
        collapsed ? "w-20" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!collapsed && (
          <h1 className="text-xl font-bold text-prometeo-black">Prometeo</h1>
        )}
        <button 
          onClick={toggleSidebar}
          className="p-2 rounded-md hover:bg-prometeo-gray transition"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <Menu size={20} /> : <X size={20} />}
        </button>
      </div>
      
      <nav className="p-3">
        <ul className="space-y-2">
          <NavItem 
            icon={<BarChart />} 
            text="Dashboard" 
            active={true} 
            collapsed={collapsed}
          />
          <NavItem 
            icon={<Users />} 
            text="Clientes" 
            collapsed={collapsed}
          />
          <NavItem 
            icon={<PieChart />} 
            text="Analíticas" 
            collapsed={collapsed}
          />
          <NavItem 
            icon={<Calendar />} 
            text="Agenda" 
            collapsed={collapsed}
          />
          <NavItem 
            icon={<MessageSquare />} 
            text="Asistente IA" 
            collapsed={collapsed}
          />
          <NavItem 
            icon={<Settings />} 
            text="Configuración" 
            collapsed={collapsed}
          />
        </ul>
      </nav>
    </div>
  );
};

interface NavItemProps {
  icon: React.ReactNode;
  text: string;
  active?: boolean;
  collapsed: boolean;
}

const NavItem = ({ icon, text, active = false, collapsed }: NavItemProps) => {
  return (
    <li>
      <a 
        href="#" 
        className={cn(
          "flex items-center p-3 rounded-md transition-colors",
          active 
            ? "bg-prometeo-blue text-white" 
            : "text-gray-600 hover:bg-prometeo-gray",
          collapsed ? "justify-center" : "justify-start"
        )}
      >
        <span className="w-5 h-5">{icon}</span>
        {!collapsed && <span className="ml-3">{text}</span>}
      </a>
    </li>
  );
};

export default Sidebar;
