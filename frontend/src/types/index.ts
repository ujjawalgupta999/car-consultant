export interface Vehicle {
  id: string;
  brand: string;
  model: string;
  year: number;
  category: string;
  condition: 'new' | 'used';
  fuel_type: string;
  transmission: string;
  seats: number;
  location: string;
  rental_price_per_day: number;
  purchase_price: number;
  available_for_rent: boolean;
  available_for_purchase: boolean;
  rating: number;
  review_count: number;
  image_url?: string;
  features: string[];
  mileage_kmpl?: number;
  range_km?: number | null;
  odometer_km: number;
  source: string;
  listing_type?: string;
  // Convenience getters/aliases if needed
  pricing?: {
    rental_daily: number;
    purchase_price: number;
    security_deposit?: number;
  };
  specs?: {
    transmission: string;
    fuel_type: string;
    seating_capacity: number;
    engine_capacity?: string;
    horsepower?: number;
    mileage?: string;
  };
  images?: string[];
}

export interface ScoreBreakdown {
  budget_score: number;
  category_score: number;
  preference_score: number;
  rating_score: number;
  brand_score: number;
}

export interface RecommendationItem {
  vehicle: Vehicle;
  match_score: number;
  score_breakdown: ScoreBreakdown;
  estimated_total_cost: number;
  currency: string;
  positive_matches: string[];
  trade_offs: string[];
  explanation: string;
  availability_status: string;
}

export interface UserPreferences {
  session_id?: string;
  intent: 'rent' | 'buy';
  location?: string;
  category?: string;
  budget?: {
    amount: number;
    currency: string;
    period: 'per_day' | 'total';
  };
  fuel_type?: string;
  transmission?: string;
  seating_capacity?: number;
  preferred_brands: string[];
  additional_preferences: string[];
  rental_details?: {
    pickup_date?: string;
    return_date?: string;
    rental_duration_days?: number;
    pickup_location?: string;
    return_location?: string;
  };
  purchase_details?: {
    purchase_budget?: number;
    expected_purchase_date?: string;
    condition?: string;
    financing_preference?: string;
  };
  interview_complete: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  a2ui_surfaces?: string[];
  mcp_app?: 'booking' | 'checkout' | null;
  data?: any;
}

export interface ProgressEvent {
  stage: string;
  step: number;
  total_steps: number;
  message: string;
}

export interface A2UIComponent {
  id: string;
  component: string;
  properties: Record<string, any>;
  children?: string[];
}

