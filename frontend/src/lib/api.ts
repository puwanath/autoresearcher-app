export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010/api/v1";

export type TaskStatus = "pending" | "running" | "completed" | "failed";
export type OutputFormat = "md" | "pdf" | "pptx" | "xlsx";
export const FORMAT_LABEL: Record<OutputFormat, string> = { md: "Markdown", pdf: "PDF", pptx: "PowerPoint", xlsx: "Excel" };

export interface ResearchRequest {
  query: string;
  target_competitors: string[];
  product_category?: string | null;
  our_brand?: string | null;
  language: "th" | "en";
  output_formats: OutputFormat[];
}

export interface TaskSummary {
  task_id: string;
  status: TaskStatus;
  query: string;
  target_competitors: string[];
  created_at: string;
  finished_at: string | null;
  products: number;
}

export interface Price {
  amount: number | null;
  currency: string;
  original_price: number | null;
  discount_percentage: number | null;
  unit_price: number | null;
}

export interface Product {
  product_name: string;
  brand_name: string | null;
  variant: string | null;
  category: string | null;
  price: Price;
  sales_channels: { channel_name: string; channel_url: string | null; availability: string }[];
  promotions: { promo_type: string; promo_description: string }[];
  rating: number | null;
  review_count: number | null;
  image_urls: string[];
  data_source_url: string;
}

export interface CompetitorAssessment {
  brand_name: string;
  price_position: "budget" | "mid-range" | "premium" | "unknown";
  price_range_thb: string;
  strengths: string[];
  weaknesses: string[];
  channels: string[];
  sentiment: "positive" | "neutral" | "negative" | "mixed" | "unknown";
  sentiment_note: string;
}

export interface ChannelStats {
  channel_name: string;
  listing_count: number;
  brand_count: number;
  brands: string[];
  price_min: number | null;
  price_max: number | null;
  price_median: number | null;
  avg_seller_rating: number | null;
  promo_count: number;
}

export interface ChannelAssessment {
  channel_name: string;
  role: string;
  strengths: string[];
  watchouts: string[];
  fit_for_us: "high" | "medium" | "low";
  recommendation: string;
}

export interface ChannelAnalysis {
  summary: string;
  channels: ChannelAssessment[];
  channel_mix_recommendation: string[];
  matrix: Record<string, string | number>[];
  stats: ChannelStats[];
}

export interface TargetSegment {
  segment: string;
  needs: string[];
  brands_serving: string[];
  opportunity: string;
}

export interface UsageInsights {
  summary: string;
  use_cases: string[];
  usage_occasions: string[];
  purchase_drivers: string[];
  pain_points: string[];
  target_segments: TargetSegment[];
  evidence: string[];
}

export interface PromotionAnalysis {
  summary: string;
  promo_type_counts: { promo_type: string; count: number; brands: string[] }[];
  brand_tactics: string[];
  recommendations: string[];
}

export interface FeatureComparison {
  summary: string;
  features: { feature: string; brands_offering: string[]; is_table_stakes: boolean }[];
  differentiation_opportunities: string[];
}

export interface Analysis {
  title: string;
  executive_summary: string;
  key_findings: string[];
  market_overview: string;
  competition_type: string;
  competitors: CompetitorAssessment[];
  pricing_insight: string;
  recommended_price_range_thb: string;
  channel_insight: string;
  recommended_channels: string[];
  sentiment_summary: string;
  swot: { strengths: string[]; weaknesses: string[]; opportunities: string[]; threats: string[] };
  recommendations: string[];
  action_plan: string[];
  data_gaps: string[];
  confidence: "low" | "medium" | "high";
  channel_analysis?: ChannelAnalysis | null;
  usage_insights?: UsageInsights | null;
  promotion_analysis?: PromotionAnalysis | null;
  feature_comparison?: FeatureComparison | null;
}

export interface PriceStats {
  currency: string;
  min: number | null;
  max: number | null;
  median: number | null;
  mean: number | null;
  sample_size: number;
}

export interface Plan {
  input_type: string;
  product_category: string;
  search_queries: string[];
  direct_urls: string[];
  target_channels: string[];
  rationale: string;
}

export interface ImageAsset {
  image_id: string;
  brand_name: string | null;
  product_name: string;
  image_url: string;
  local_file_path: string;
  alt_text: string;
  width_px: number;
  height_px: number;
}

export interface TaskView {
  task_id: string;
  status: TaskStatus;
  request: ResearchRequest;
  events: string[];
  error: string | null;
  created_at: string;
  finished_at: string | null;
  plan: Plan | null;
  analysis: Analysis | null;
  price_stats: PriceStats | null;
  products: Product[];
  images: ImageAsset[];
  charts: string[];
  artifacts: Partial<Record<OutputFormat, string>>;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export const api = {
  create: (body: ResearchRequest) =>
    http<{ task_id: string; status: TaskStatus }>("/research", { method: "POST", body: JSON.stringify(body) }),
  retry: (id: string) => http<{ task_id: string; status: TaskStatus }>(`/research/${id}/retry`, { method: "POST" }),
  list: (limit = 20) => http<TaskSummary[]>(`/research?limit=${limit}`),
  get: (id: string) => http<TaskView>(`/research/${id}`),
  reportUrl: (id: string, format: OutputFormat) => `${API_URL}/research/${id}/report?format=${format}`,
  assetUrl: (id: string, path: string) => `${API_URL}/research/${id}/assets/${path}`,
};
