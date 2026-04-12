// TypeScript types mirroring backend Pydantic response models

export interface FormulaConfig {
  HP_COEFFICIENT: number;
  DEF_REDUCTION_RATIO: number;
  RES_THRESHOLD_RATIO: number;
  SPEED_BONUS_RATIO: number;
  SURVIVE_DAMAGE_REDUCTION: number;
  MAX_ACTION_POINT_BANK: number;
  CHEAT_DEBT_PER_ACTION: number;
  CHEAT_DEBT_RECOVERY_PER_TURN: number;
  XP_THRESHOLD_BASE: number;
  XP_THRESHOLD_EXPONENT: number;
  XP_OVERLEVEL_PENALTY_PER_LEVEL: number;
  XP_MINIMUM_RATIO: number;
  CHA_PRICE_MODIFIER_PER_POINT: number;
  CHA_PRICE_MIN_RATIO: number;
  CHA_PRICE_MAX_RATIO: number;
  SELL_RATIO: number;
  MONEY_DROP_MIN_MULTIPLIER: number;
  MONEY_DROP_MAX_MULTIPLIER: number;
  OVERSTAY_PENALTY_PER_BATTLE: number;
}

// Data summaries
export interface JobSummary {
  id: string; name: string; origin: string;
  growth: Record<string, number>;
  base_hp: number; hp_growth: number;
  innate_ability_id: string; description: string;
}

export interface ItemSummary {
  id: string; name: string; slot: string;
  scaling_type: string | null; scaling_stat: string | null;
  has_conversion: boolean; base_price: number; description: string;
}

export interface AbilitySummary {
  id: string; name: string; category: string;
  target: string; quality: string | null; description: string;
}

export interface EnemySummary {
  id: string; name: string; archetype: string;
  budget_multiplier: number; description: string;
}

export interface ZoneSummary {
  id: string; name: string; zone_level: number; region: string;
  encounter_count: number; shop_item_count: number;
}

// Weapon sweep
export interface WeaponSweepPoint {
  level: number; stat_value: number;
  outputs: Record<string, number>;
  effective: Record<string, number>;
  best: string;
}

export interface WeaponSweepResult {
  job_id: string; stat: string; growth_rate: number;
  weapon_names: string[];
  points: WeaponSweepPoint[];
}

// Crossover
export interface CrossoverEvent {
  winner: string; loser: string; level: number;
  winner_value: number; loser_value: number;
}

export interface BreakevenEvent {
  weapon: string; level: number; stat_value: number; output: number;
}

export interface CrossoverResult {
  job_id: string; stat: string; growth_rate: number;
  crossovers: CrossoverEvent[];
  breakevens: BreakevenEvent[];
}

// Build compare
export interface BuildSnapshot {
  name: string; items: string[];
  stats: Record<string, number>; hp: number; bonus_actions: number;
  heavy_damage: number | null; bolt_damage: number | null; dpt: number | null;
}

export interface BuildCompareResult {
  job_id: string; level: number;
  builds: BuildSnapshot[];
  enemy_info: string | null;
}

// Converter
export interface ConverterPoint {
  level: number; source_stat: number; outputs: Record<string, number>;
}

export interface ConverterCompareResult {
  job_id: string; converter_id: string;
  source_stat: string; target_stat: string; growth_rate: number;
  points: ConverterPoint[];
}

// Sigmoid
export interface SigmoidPoint {
  stat: number; output: number; pct_of_max: number;
}

export interface SigmoidResult {
  max_output: number; midpoint: number; rate: number;
  points: SigmoidPoint[];
}

// Ability DPR
export interface AbilityDprRow {
  ability_id: string; ability_name: string;
  quality: string; scaling_stat: string; coefficient: number;
  unlock_level: number | string;
  damage_by_level: Record<string, number>;
  ratio_by_level: Record<string, number>;
}

export interface AbilityDprResult {
  job_id: string; job_name: string; enemy_def: number;
  levels: number[];
  rows: AbilityDprRow[];
  surge_breakdowns: Array<{ ability_name: string; stack_bonus: number; data: Record<string, number>[] }>;
  dot_breakdowns: Array<{ ability_name: string; duration: number; tick_base: number; data: Record<string, number>[] }>;
  pierce_breakdowns: Array<{ ability_name: string; pierce_pct: number; data: Record<string, number>[] }>;
  chain_breakdowns: Array<{ ability_name: string; chain_ratio: number; data: Record<string, number>[] }>;
}

// Ability compare
export interface AbilityComparePoint {
  level: number; str_val: number; mag_val: number;
  damages: Record<string, number>; best: string;
}

export interface AbilityCompareResult {
  job_id: string; enemy_def: number;
  ability_names: string[];
  points: AbilityComparePoint[];
  crossovers: CrossoverEvent[];
}

// Job curve
export interface JobCurveUnlock {
  unlock_level: number; ability_id: string; ability_name: string;
  category: string; quality: string; scaling_stat: string;
  damage_at_unlock: number; basic_attack_at_unlock: number;
  ratio_vs_basic: number;
}

export interface JobCurveResult {
  job_id: string; job_name: string; enemy_def: number;
  unlocks: JobCurveUnlock[];
  strongest_unlock: string | null;
  first_power_spike: string | null;
}

// Economy
export interface ZoneEconomySnapshot {
  zone_id: string; zone_name: string; zone_level: number;
  enemies_total: number; encounters_total: number;
  zone_gold: number; overstay_max_gold: number; avg_encounter_gold: number;
  cumulative_gold_rush: number; cumulative_gold_moderate: number; cumulative_gold_grind: number;
  shop_items: string[];
}

export interface PilferImpact {
  zone_id: string; zone_gold: number; cumulative_gold: number;
  pilfer_per_hit: number; two_hits: number; encounter_equivalent: number;
}

export interface EconomyResult {
  zones: ZoneEconomySnapshot[];
  pilfer_flat: number; pilfer_per_level: number;
  pilfer_impacts: PilferImpact[];
}

// XP curve
export interface ZoneXpSnapshot {
  zone_id: string; zone_level: number;
  level_at_exit_rush: number; level_at_exit_moderate: number; level_at_exit_grind: number;
  cumulative_xp_rush: number; cumulative_xp_moderate: number; cumulative_xp_grind: number;
}

export interface XpMilestone {
  target_level: number; rush_zone: string; moderate_zone: string; grind_zone: string;
}

export interface XpCurveResult {
  job_id: string; job_name: string;
  zones: ZoneXpSnapshot[];
  milestones: XpMilestone[];
}

// Enemy stats
export interface EnemyZoneStats {
  zone_level: number; hp: number;
  base_stats: Record<string, number>;
  effective_stats: Record<string, number> | null;
}

export interface EnemyStatsEntry {
  enemy_id: string; enemy_name: string; archetype: string;
  budget_multiplier: number; stat_distribution: Record<string, number>;
  equipment: string[];
  zone_stats: EnemyZoneStats[];
}

export interface EnemyStatsResult {
  enemies: EnemyStatsEntry[];
}

// Shop pricing
export interface ShopItem {
  item_name: string; item_id: string;
  base_price: number; buy_price: number;
  pct_rush: number | null; pct_moderate: number | null; pct_grind: number | null;
  affordable: string;
}

export interface ShopZone {
  zone_name: string; zone_level: number;
  cumulative_gold_rush: number; cumulative_gold_moderate: number; cumulative_gold_grind: number;
  items: ShopItem[];
}

export interface PotionCheck {
  potion_name: string; potion_id: string;
  base_price: number; buy_price: number;
  intro_zone: string | null; avg_encounter_gold: number | null;
  ratio: number | null; status: string;
}

export interface ShopPricingResult {
  zones: ShopZone[];
  potions: PotionCheck[];
}

// Progression
export interface ProgressionZone {
  zone_id: string; zone_name: string; zone_level: number;
  exit_level_rush: number; exit_level_moderate: number; exit_level_grind: number;
  cumulative_gold_rush: number; cumulative_gold_moderate: number; cumulative_gold_grind: number;
  affordable_items: string[];
  unlocked_abilities: string[];
  best_weapon: string | null;
  weapon_outputs: Record<string, number>;
}

export interface ProgressionResult {
  job_id: string; job_name: string;
  primary_stat: string; growth_rate: number;
  zones: ProgressionZone[];
}
