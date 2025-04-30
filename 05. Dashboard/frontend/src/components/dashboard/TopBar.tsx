import { Search, Calendar, Filter, ChevronDown } from "lucide-react";
import { useState } from "react";

const TIME_PERIODS = ["Hoy", "Semana", "Mes", "Trimestre"];
const CLIENT_SEGMENTS = ["Todos", "Básico", "Premium", "VIP"];

export const TopBar = () => {
  const [timePeriod, setTimePeriod] = useState("Mes");
  const [segment, setSegment] = useState("Todos");
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="bg-white border-b border-gray-200 py-3 px-4 flex justify-between items-center">
      <div className="flex gap-4">
        {/* Time Period Selector */}
        <div className="relative">
          <Dropdown 
            options={TIME_PERIODS}
            selected={timePeriod}
            onSelect={setTimePeriod}
            icon={<Calendar size={16} />}
          />
        </div>

        {/* Client Segment Filter */}
        <div className="relative">
          <Dropdown 
            options={CLIENT_SEGMENTS}
            selected={segment}
            onSelect={setSegment}
            icon={<Filter size={16} />}
          />
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={16} className="text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Buscar cliente..."
          className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prometeo-blue focus:border-transparent"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
    </div>
  );
};

interface DropdownProps {
  options: string[];
  selected: string;
  onSelect: (value: string) => void;
  icon?: React.ReactNode;
}

const Dropdown = ({ options, selected, onSelect, icon }: DropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-white border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-prometeo-blue"
      >
        {icon && <span className="text-gray-500">{icon}</span>}
        <span>{selected}</span>
        <ChevronDown size={16} className="text-gray-500" />
      </button>

      {isOpen && (
        <div className="absolute mt-1 z-10 w-48 bg-white border border-gray-200 rounded-md shadow-lg">
          <ul className="py-1 text-sm">
            {options.map((option) => (
              <li key={option}>
                <button
                  className={`block w-full text-left px-4 py-2 hover:bg-prometeo-gray ${
                    option === selected ? "bg-prometeo-gray" : ""
                  }`}
                  onClick={() => {
                    onSelect(option);
                    setIsOpen(false);
                  }}
                >
                  {option}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default TopBar;
