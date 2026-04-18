export type UserProfile = {
  bio: string | null;
  avatar_url: string | null;
  default_market_focus: string | null;
  timezone: string | null;
  theme: string | null;
};

export type UserPreference = {
  preferred_categories: string[];
  preferred_desk_mode: string | null;
  alert_move_threshold: number | null;
  alert_headline_matches: boolean;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
  updated_at: string;
  profile: UserProfile;
  preference: UserPreference;
};

export type AuthResponse = {
  token: {
    access_token: string;
    token_type: "bearer";
  };
  user: User;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  display_name: string;
};
