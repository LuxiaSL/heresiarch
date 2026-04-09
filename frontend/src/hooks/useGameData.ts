import { useQuery } from '@tanstack/react-query';
import { fetchJobs, fetchItems, fetchAbilities, fetchEnemies, fetchZones } from '../api/client';

export function useJobs() {
  return useQuery({ queryKey: ['jobs'], queryFn: fetchJobs, staleTime: Infinity });
}

export function useItems() {
  return useQuery({ queryKey: ['items'], queryFn: fetchItems, staleTime: Infinity });
}

export function useAbilities() {
  return useQuery({ queryKey: ['abilities'], queryFn: fetchAbilities, staleTime: Infinity });
}

export function useEnemies() {
  return useQuery({ queryKey: ['enemies'], queryFn: fetchEnemies, staleTime: Infinity });
}

export function useZones() {
  return useQuery({ queryKey: ['zones'], queryFn: fetchZones, staleTime: Infinity });
}
