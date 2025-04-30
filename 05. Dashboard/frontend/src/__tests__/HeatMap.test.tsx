/// <reference types="vitest" />
import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import HeatMap from '../components/dashboard/HeatMap';

// Mocked data for API responses
const mockVariables = {
  variables: ['age', 'income_range', 'risk_profile', 'status'],
  categories: {
    age: ['18-25', '26-35', '36-45', '46-55', '56+'],
    income_range: ['0-50k', '50k-100k', '100k-150k', '150k+'],
    risk_profile: ['conservative', 'moderate', 'aggressive'],
    status: ['pending', 'contacted']
  }
};

const mockHeatmapData = {
  x_categories: ['18-25', '26-35', '36-45', '46-55', '56+'],
  y_categories: ['0-50k', '50k-100k', '100k-150k', '150k+'],
  values: [
    [0.15, 0.18, 0.21, 0.19, 0.16],
    [0.22, 0.27, 0.32, 0.29, 0.25],
    [0.31, 0.36, 0.42, 0.38, 0.33],
    [0.38, 0.45, 0.53, 0.48, 0.41]
  ]
};

// Set up MSW server to mock API requests
const server = setupServer(
  http.get('*/api/v1/metrics/heatmap/variables', () => {
    return HttpResponse.json(mockVariables);
  }),
  http.get('*/api/v1/metrics/heatmap', () => {
    return HttpResponse.json(mockHeatmapData);
  })
);

// Set up the QueryClient for testing
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

// Start server before tests
beforeAll(() => server.listen());
// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
  queryClient.clear();
});
// Close server after all tests
afterAll(() => server.close());

describe('HeatMap Component', () => {
  test('renders loading state initially', async () => {
    render(
      <Wrapper>
        <HeatMap />
      </Wrapper>
    );
    
    // Should show loading state initially
    expect(screen.getByText(/Mapa de Calor - Segmentación de Clientes/i)).toBeInTheDocument();
  });
  
  test('renders heatmap with data after loading', async () => {
    render(
      <Wrapper>
        <HeatMap />
      </Wrapper>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/18-25/i)).toBeInTheDocument();
      expect(screen.getByText(/0-50k/i)).toBeInTheDocument();
    });
    
    // Check that options for axis selectors exist
    const ejeXLabel = screen.getByText('Eje X:');
    const ejeYLabel = screen.getByText('Eje Y:');
    expect(ejeXLabel).toBeInTheDocument();
    expect(ejeYLabel).toBeInTheDocument();
    
    // Check that cell values are displayed correctly
    expect(screen.getByText('53%')).toBeInTheDocument(); // Highest value in the mock data
    expect(screen.getByText('15%')).toBeInTheDocument(); // Lowest value in the mock data
  });
  
  test('does not render threshold line', async () => {
    render(
      <Wrapper>
        <HeatMap />
      </Wrapper>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/18-25/i)).toBeInTheDocument();
    });
    
    // Verify that umbral text is not shown
    const umbralText = screen.queryByText(/Umbral:/i);
    expect(umbralText).not.toBeInTheDocument();
  });
  
  test('displays correct cell values based on metric', async () => {
    render(
      <Wrapper>
        <HeatMap />
      </Wrapper>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/18-25/i)).toBeInTheDocument();
    });
    
    // Check that probability values are formatted correctly
    expect(screen.getByText('53%')).toBeInTheDocument();
    expect(screen.getByText('15%')).toBeInTheDocument();
    
    // Verify that the legend shows correct label for probability
    expect(screen.getByText('Probabilidad')).toBeInTheDocument();
  });
  
  test('handles error state properly', async () => {
    // Override the server response for this test
    server.use(
      http.get('*/api/v1/metrics/heatmap', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );
    
    render(
      <Wrapper>
        <HeatMap />
      </Wrapper>
    );
    
    // Wait for error state to show
    await waitFor(() => {
      expect(screen.getByText(/Error al cargar los datos del mapa de calor/i)).toBeInTheDocument();
    });
    
    // Check for retry button
    expect(screen.getByText(/Reintentar/i)).toBeInTheDocument();
  });
}); 