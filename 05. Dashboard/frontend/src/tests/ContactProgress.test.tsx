/// <reference types="vitest" />
import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import ContactProgress from '../components/dashboard/ContactProgress';

// Datos de prueba mock para la respuesta del API
const mockProgressData = {
  total_contacted: 123,
  total_prioritized: 345,
  monthly_target: 250,
  contacted_this_month: 123,
  days_remaining: 14,
  daily_needed: 9,
  daily_expected: 7,
  difference: -2,
  projection_message: "Con el ritmo actual, no alcanzarás la meta mensual. Necesitas aumentar el ritmo de contactos."
};

// Configurar servidor MSW para interceptar solicitudes API
const server = setupServer(
  http.get('*/api/v1/contacts/progress', () => {
    return HttpResponse.json(mockProgressData);
  })
);

// Configurar QueryClient para testing
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

// Iniciar/detener servidor mock
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  queryClient.clear();
});
afterAll(() => server.close());

describe('ContactProgress Component', () => {
  test('muestra estado de carga inicialmente', async () => {
    render(
      <Wrapper>
        <ContactProgress />
      </Wrapper>
    );
    
    // Verificar que se muestra el título durante la carga
    expect(screen.getByText('Progreso de Contactos')).toBeInTheDocument();
    
    // Esperar a que se carguen los datos
    await waitFor(() => {
      expect(screen.getByText('123 contactados')).toBeInTheDocument();
    });
  });
  
  test('renderiza correctamente con datos', async () => {
    render(
      <Wrapper>
        <ContactProgress />
      </Wrapper>
    );
    
    // Esperar a que se carguen los datos
    await waitFor(() => {
      // Verificar elementos clave del componente
      expect(screen.getByText('Progreso General')).toBeInTheDocument();
      expect(screen.getByText('Meta Mensual')).toBeInTheDocument();
      expect(screen.getByText('Proyección de Cumplimiento')).toBeInTheDocument();
      
      // Verificar datos específicos
      expect(screen.getByText('123 contactados')).toBeInTheDocument();
      expect(screen.getByText('345 clientes prioritarios')).toBeInTheDocument();
      expect(screen.getByText(/Faltan 14 días/i)).toBeInTheDocument();
      expect(screen.getByText('9 contactos/día')).toBeInTheDocument();
      expect(screen.getByText('7 contactos/día')).toBeInTheDocument();
      expect(screen.getByText(/-2 contactos/i)).toBeInTheDocument();
      
      // Verificar presencia del mensaje de proyección
      expect(screen.getByText(mockProgressData.projection_message)).toBeInTheDocument();
    });
  });
  
  test('muestra error cuando falla la carga de datos', async () => {
    // Sobreescribir el handler para simular un error
    server.use(
      http.get('*/api/v1/contacts/progress', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );
    
    render(
      <Wrapper>
        <ContactProgress />
      </Wrapper>
    );
    
    // Esperar a que se muestre el mensaje de error
    await waitFor(() => {
      expect(screen.getByText(/Error al cargar los datos de progreso de contactos/i)).toBeInTheDocument();
      expect(screen.getByText('Reintentar')).toBeInTheDocument();
    });
  });
}); 