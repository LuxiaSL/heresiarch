import { useQuery, type UseQueryResult } from '@tanstack/react-query';

/**
 * Generic hook for sim endpoint queries.
 * Automatically re-fetches when params change.
 */
export function useSimQuery<T>(
  key: string,
  fetcher: (body: Record<string, unknown>) => Promise<T>,
  params: Record<string, unknown>,
  enabled = true,
): UseQueryResult<T> {
  return useQuery({
    queryKey: [key, params],
    queryFn: () => fetcher(params),
    enabled,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
