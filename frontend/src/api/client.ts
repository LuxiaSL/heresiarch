// Typed API client for the balance dashboard

import type {
  FormulaConfig, JobSummary, ItemSummary, AbilitySummary, EnemySummary, ZoneSummary,
  WeaponSweepResult, CrossoverResult, BuildCompareResult, ConverterCompareResult,
  SigmoidResult, AbilityDprResult, AbilityCompareResult, JobCurveResult,
  EconomyResult, XpCurveResult, EnemyStatsResult, ShopPricingResult, ProgressionResult,
} from './types';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json();
}

async function put<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PUT ${path}: ${res.status}`);
  return res.json();
}

// Data endpoints
export const fetchJobs = () => get<Record<string, JobSummary>>('/data/jobs');
export const fetchItems = () => get<Record<string, ItemSummary>>('/data/items');
export const fetchAbilities = () => get<Record<string, AbilitySummary>>('/data/abilities');
export const fetchEnemies = () => get<Record<string, EnemySummary>>('/data/enemies');
export const fetchZones = () => get<Record<string, ZoneSummary>>('/data/zones');

// Config endpoints
export const fetchFormulas = () => get<FormulaConfig>('/config/formulas');
export const updateFormulas = (cfg: FormulaConfig) => put<FormulaConfig>('/config/formulas', cfg as unknown as Record<string, unknown>);
export const saveFormulas = () => post<{ status: string }>('/config/formulas/save', {});
export const resetFormulas = () => post<FormulaConfig>('/config/formulas/reset', {});

// Sim endpoints
export const simWeaponSweep = (body: Record<string, unknown>) => post<WeaponSweepResult>('/sim/weapon-sweep', body);
export const simCrossovers = (body: Record<string, unknown>) => post<CrossoverResult>('/sim/crossovers', body);
export const simBuildCompare = (body: Record<string, unknown>) => post<BuildCompareResult>('/sim/build-compare', body);
export const simConverter = (body: Record<string, unknown>) => post<ConverterCompareResult>('/sim/converter', body);
export const simSigmoid = (body: Record<string, unknown>) => post<SigmoidResult>('/sim/sigmoid', body);
export const simAbilityDpr = (body: Record<string, unknown>) => post<AbilityDprResult>('/sim/ability-dpr', body);
export const simAbilityCompare = (body: Record<string, unknown>) => post<AbilityCompareResult>('/sim/ability-compare', body);
export const simJobCurve = (body: Record<string, unknown>) => post<JobCurveResult>('/sim/job-curve', body);
export const simEconomy = (body: Record<string, unknown>) => post<EconomyResult>('/sim/economy', body);
export const simXpCurve = (body: Record<string, unknown>) => post<XpCurveResult>('/sim/xp-curve', body);
export const simEnemyStats = (body: Record<string, unknown>) => post<EnemyStatsResult>('/sim/enemy-stats', body);
export const simShopPricing = (body: Record<string, unknown>) => post<ShopPricingResult>('/sim/shop-pricing', body);
export const simProgression = (body: Record<string, unknown>) => post<ProgressionResult>('/sim/progression', body);
